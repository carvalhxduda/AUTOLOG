# AUTOLOG

AUTOLOG analisa logs do Genesys Cloud Background Assistant (GCBA), identifica linhas de erro e gera um relatorio em PDF com cores para facilitar a leitura operacional.


## O Que O Projeto Faz

- Le arquivos `.log` dentro da pasta `LOGS`.
- Identifica eventos `ERROR`.
- Extrai data/hora, ID do agente, componente, descricao, causa raiz e impacto.
- Gera um relatorio PDF colorido em `output/pdf/relatorio_analise_gcba.pdf`.
- Opcionalmente gera um CSV detalhado em `erros_mapeados_gcba.csv`.

## Estrutura Esperada

```text
AUTOLOG/
  LOGS/
    Nome do usuario/
      background-assistant.log
      background-assistant.0.log
      sumologger.log
  autolog.py
  gerar_relatorio_pdf.py
  requirements.txt
```

Coloque os logs que deseja analisar dentro da pasta `LOGS`. O script procura arquivos `.log` de forma recursiva, entao subpastas por usuario, maquina ou data funcionam normalmente.

## Requisitos

- Python 3.10 ou superior.
- Pacote Python `reportlab`.

Instale as dependencias com:

```powershell
pip install -r requirements.txt
```

## Gerar Apenas O PDF

Este e o fluxo recomendado para uso:

```powershell
python gerar_relatorio_pdf.py
```

Saida gerada:

```text
output/pdf/relatorio_analise_gcba.pdf
```

O PDF e criado diretamente a partir dos logs.

## Gerar CSV Detalhado

Use esta opcao quando quiser abrir a base no Excel, auditar linha a linha ou compartilhar os dados tabulados.

```powershell
python autolog.py
```

Saida gerada:

```text
erros_mapeados_gcba.csv
```

## Exemplo De Uso Completo

```powershell
cd C:\caminho\para\AUTOLOG
pip install -r requirements.txt
python gerar_relatorio_pdf.py
```

Depois, abra:

```text
output/pdf/relatorio_analise_gcba.pdf
```

## Campos Mapeados

O parser extrai os seguintes campos dos logs:

| Campo | Descricao |
| --- | --- |
| `pasta_verificada` | Pasta onde o arquivo de log foi encontrado. |
| `id_agente` | ID da sessao/agente, ou `Sistema` quando vazio. |
| `data_hora` | Data e hora do erro no log. |
| `componente` | Classe ou servico que registrou o erro. |
| `descricao` | Mensagem resumida do erro. |
| `causa_raiz` | Causa tecnica inferida a partir da mensagem. |
| `impacto` | Impacto operacional provavel. |

## Observacoes Para O Time

- O arquivo PDF e o produto final recomendado para apresentacao.
- O CSV e opcional e serve para analise detalhada.
- Logs, CSVs e PDFs gerados localmente nao devem ser commitados no GitHub, pois podem conter dados operacionais.

