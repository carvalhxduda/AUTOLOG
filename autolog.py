import csv
import os
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CAMINHO_LOGS = BASE_DIR / "LOGS"
ARQUIVO_SAIDA = BASE_DIR / "erros_mapeados_gcba.csv"

CABECALHO = [
    "pasta_verificada",
    "id_agente",
    "data_hora",
    "componente",
    "descricao",
    "causa_raiz",
    "impacto",
]


def normalizar_timestamp(valor):
    match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", valor)
    return match.group(1) if match else valor.strip()


def limpar_descricao(mensagem):
    descricao = mensagem.strip()
    descricao = re.split(r"\s+System\.", descricao, maxsplit=1)[0]
    descricao = re.split(r"\s+-\s+System\.", descricao, maxsplit=1)[0]
    return descricao.strip(" -") or mensagem.strip()


def mapear_causa_raiz(mensagem):
    if "404 (Not Found)" in mensagem:
        return "Erro 404 (Not Found) - Endpoint inacessivel"
    if "Este host" in mensagem and "conhecido" in mensagem:
        return "Host desconhecido - api.sae1.pure.cloud:443 inacessivel"
    if "SSL connection could not be established" in mensagem or "SSL conn" in mensagem:
        return "Falha SSL - conexao segura nao estabelecida"
    if "Time mismatch" in mensagem:
        return "Divergencia de horario entre cliente e servidor"
    if "Todas as instancias de pipes" in mensagem or "Todas as instâncias de pipes" in mensagem:
        return "Pipes ocupados - limite de instancias atingido"
    if "Pipe is broken" in mensagem:
        return "Pipe quebrado - comunicacao interprocesso interrompida"
    if "Last ping received is more than 5 minutes" in mensagem:
        return "Ping ausente por mais de 5 minutos"
    if "GcbaWebApp instance is null" in mensagem:
        return "Instancia GcbaWebApp nula ou WebRTC SDK inativo"
    if "KeyNotFoundException" in mensagem:
        return "Chave de sessao nao encontrada"
    if "ArgumentNullException" in mensagem:
        return "Argumento nulo no processo GcbaBrowser"
    if "Cannot execute javascript" in mensagem:
        return "Falha ao executar JavaScript no frame principal"
    if "Failed to post to api" in mensagem:
        return "Falha no envio HTTP para API de diagnostico"
    return mensagem.strip()


def mapear_impacto(componente, mensagem, causa_raiz):
    texto = f"{componente} {mensagem} {causa_raiz}"
    if "GcbaWebAppVersion" in texto:
        return "Falha de sincronizacao entre extensao do navegador e app desktop"
    if "SumoLog" in texto or "diagnostics" in texto or "newrelic" in texto:
        return "Perda ou atraso no envio de telemetria e diagnosticos"
    if "Time mismatch" in texto or "horario" in texto:
        return "Risco de falha de autenticacao por diferenca de horario"
    if "Pipe" in texto or "pipe" in texto:
        return "Quebra na comunicacao entre processos do GCBA"
    if "ping" in texto.lower() or "sleep mode" in texto:
        return "Encerramento do processo do navegador por inatividade ou suspensao"
    if "GcbaWebApp instance is null" in texto or "WebRTC" in texto:
        return "Recursos WebRTC ou integracao web indisponiveis para o usuario"
    if "login" in texto.lower():
        return "Falha de login ou inicializacao de sessao do usuario"
    return "Falha operacional no GCBA que exige avaliacao tecnica"


def iterar_erros():
    for caminho in sorted(CAMINHO_LOGS.rglob("*.log")):
        with caminho.open("r", encoding="utf-8", errors="ignore") as arquivo:
            for linha in arquivo:
                if "|ERROR|" not in linha:
                    continue

                partes = linha.rstrip("\n").split("|", 5)
                if len(partes) < 6:
                    continue

                timestamp, _nivel_num, nivel, id_agente, componente, mensagem = partes
                if nivel != "ERROR":
                    continue

                id_agente = id_agente.strip() or "Sistema"
                componente = componente.strip() or "N/A"
                mensagem = mensagem.strip()
                causa_raiz = mapear_causa_raiz(mensagem)

                yield {
                    "pasta_verificada": str(caminho.parent),
                    "id_agente": id_agente,
                    "data_hora": normalizar_timestamp(timestamp),
                    "componente": componente,
                    "descricao": limpar_descricao(mensagem),
                    "causa_raiz": causa_raiz,
                    "impacto": mapear_impacto(componente, mensagem, causa_raiz),
                }


def main():
    if not CAMINHO_LOGS.exists():
        raise SystemExit(f"Pasta de logs nao encontrada: {CAMINHO_LOGS}")

    registros = list(iterar_erros())
    with ARQUIVO_SAIDA.open("w", newline="", encoding="utf-8-sig") as arquivo_csv:
        writer = csv.DictWriter(arquivo_csv, fieldnames=CABECALHO, delimiter=";")
        writer.writeheader()
        writer.writerows(registros)

    print(f"CSV gerado: {ARQUIVO_SAIDA}")
    print(f"Erros mapeados: {len(registros)}")


if __name__ == "__main__":
    main()
