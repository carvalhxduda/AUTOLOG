from collections import Counter
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from autolog import CAMINHO_LOGS, iterar_erros


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output" / "pdf"
PDF_PATH = OUTPUT_DIR / "relatorio_analise_gcba.pdf"
SOURCE_LABEL = str(CAMINHO_LOGS)

PALETTE = {
    "navy": colors.HexColor("#22324A"),
    "blue": colors.HexColor("#2F80ED"),
    "teal": colors.HexColor("#1F9D8A"),
    "green": colors.HexColor("#2EAD5B"),
    "amber": colors.HexColor("#F2A93B"),
    "red": colors.HexColor("#D64550"),
    "purple": colors.HexColor("#7D5CC6"),
    "slate": colors.HexColor("#6B7280"),
    "light_blue": colors.HexColor("#EAF3FF"),
    "light_teal": colors.HexColor("#E7F7F4"),
    "light_green": colors.HexColor("#E9F7EE"),
    "light_amber": colors.HexColor("#FFF4E0"),
    "light_red": colors.HexColor("#FDECEF"),
    "light_purple": colors.HexColor("#F2EEFB"),
    "line": colors.HexColor("#D8DEE8"),
    "bg": colors.HexColor("#F7F9FC"),
    "white": colors.white,
}


def load_rows():
    return list(iterar_erros())


def shorten(text, limit):
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def parse_date(row):
    try:
        return datetime.strptime(row["data_hora"], "%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.min


def classify_color(cause):
    text = cause.lower()
    if "404" in text:
        return PALETTE["red"], PALETTE["light_red"]
    if "horario" in text or "time" in text:
        return PALETTE["amber"], PALETTE["light_amber"]
    if "pipe" in text:
        return PALETTE["purple"], PALETTE["light_purple"]
    if "host" in text or "http" in text or "ssl" in text:
        return PALETTE["blue"], PALETTE["light_blue"]
    return PALETTE["teal"], PALETTE["light_teal"]


def add_header_footer(canvas, doc):
    canvas.saveState()
    width, height = doc.pagesize
    canvas.setFillColor(PALETTE["navy"])
    canvas.rect(0, height - 1.1 * cm, width, 1.1 * cm, fill=1, stroke=0)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(PALETTE["white"])
    canvas.drawString(1.2 * cm, height - 0.68 * cm, "Analise de Logs GCBA")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(width - 1.2 * cm, height - 0.68 * cm, f"Pagina {doc.page}")
    canvas.setFillColor(PALETTE["slate"])
    canvas.drawRightString(width - 1.2 * cm, 0.75 * cm, f"Fonte: {SOURCE_LABEL}")
    canvas.restoreState()


def paragraph_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "TitleCustom",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=PALETTE["navy"],
            alignment=TA_LEFT,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            "SubtitleCustom",
            parent=styles["BodyText"],
            fontSize=10,
            leading=14,
            textColor=PALETTE["slate"],
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            "SectionTitle",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=PALETTE["navy"],
            spaceBefore=8,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            "Small",
            parent=styles["BodyText"],
            fontSize=8,
            leading=10,
            textColor=PALETTE["navy"],
        )
    )
    styles.add(
        ParagraphStyle(
            "HeaderSmall",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=PALETTE["white"],
            alignment=TA_CENTER,
        )
    )
    styles.add(
        ParagraphStyle(
            "TableSmall",
            parent=styles["BodyText"],
            fontSize=7.2,
            leading=8.5,
            textColor=PALETTE["navy"],
        )
    )
    styles.add(
        ParagraphStyle(
            "CardValue",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=23,
            alignment=TA_CENTER,
            textColor=PALETTE["navy"],
        )
    )
    styles.add(
        ParagraphStyle(
            "CardLabel",
            parent=styles["BodyText"],
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            textColor=PALETTE["slate"],
        )
    )
    styles.add(
        ParagraphStyle(
            "RightSmall",
            parent=styles["BodyText"],
            fontSize=7.2,
            leading=8.5,
            alignment=TA_RIGHT,
            textColor=PALETTE["navy"],
        )
    )
    return styles


def make_card(value, label, bg_color, border_color, styles):
    table = Table(
        [[Paragraph(str(value), styles["CardValue"])], [Paragraph(label, styles["CardLabel"])]],
        colWidths=[4.3 * cm],
        rowHeights=[1.0 * cm, 0.75 * cm],
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg_color),
                ("BOX", (0, 0), (-1, -1), 0.8, border_color),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def count_table(title, counter, total, styles, max_rows=10):
    data = [
        [
            Paragraph(title, styles["HeaderSmall"]),
            Paragraph("Qtde", styles["HeaderSmall"]),
            Paragraph("%", styles["HeaderSmall"]),
        ]
    ]
    table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), PALETTE["navy"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), PALETTE["white"]),
        ("BOX", (0, 0), (-1, -1), 0.5, PALETTE["line"]),
        ("GRID", (0, 0), (-1, -1), 0.3, PALETTE["line"]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]

    for index, (name, count) in enumerate(counter.most_common(max_rows), start=1):
        pct = count / total if total else 0
        color, bg = classify_color(name)
        data.append(
            [
                Paragraph(f"<font color='{color.hexval()}'><b>{shorten(name, 68)}</b></font>", styles["TableSmall"]),
                Paragraph(str(count), styles["RightSmall"]),
                Paragraph(f"{pct:.1%}", styles["RightSmall"]),
            ]
        )
        table_style.append(("BACKGROUND", (0, index), (-1, index), bg if index % 2 else PALETTE["white"]))

    table = Table(data, colWidths=[14.0 * cm, 2.2 * cm, 2.0 * cm], repeatRows=1)
    table.setStyle(TableStyle(table_style))
    return table


def build_pdf(rows):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    styles = paragraph_styles()
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.55 * cm,
        bottomMargin=1.2 * cm,
    )

    total = len(rows)
    components = Counter(row["componente"] for row in rows)
    causes = Counter(row["causa_raiz"] for row in rows)
    agents = Counter(row["id_agente"] for row in rows)
    impacts = Counter(row["impacto"] for row in rows)
    folders = Counter(Path(row["pasta_verificada"]).name for row in rows)
    dates = [parse_date(row) for row in rows if parse_date(row) != datetime.min]
    first_date = min(dates).strftime("%d/%m/%Y") if dates else "N/A"
    last_date = max(dates).strftime("%d/%m/%Y") if dates else "N/A"

    story = []
    story.append(Paragraph("Relatorio de Analise de Logs GCBA", styles["TitleCustom"]))
    story.append(
        Paragraph(
            f"Arquivo consolidado em {PDF_PATH.name}. Periodo observado: {first_date} a {last_date}. "
            "As cores destacam os grupos com maior criticidade operacional ou maior volume de ocorrencias.",
            styles["SubtitleCustom"],
        )
    )

    cards = Table(
        [
            [
                make_card(total, "erros mapeados", PALETTE["light_blue"], PALETTE["blue"], styles),
                make_card(len(components), "componentes afetados", PALETTE["light_teal"], PALETTE["teal"], styles),
                make_card(len(agents), "agentes/sessoes", PALETTE["light_purple"], PALETTE["purple"], styles),
                make_card(len(folders), "pastas verificadas", PALETTE["light_green"], PALETTE["green"], styles),
            ]
        ],
        colWidths=[4.55 * cm] * 4,
    )
    cards.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(cards)
    story.append(Spacer(1, 0.35 * cm))

    top_component, top_component_count = components.most_common(1)[0]
    top_cause, top_cause_count = causes.most_common(1)[0]
    insight_data = [
        [
            Paragraph("<b>Principal componente</b>", styles["Small"]),
            Paragraph(shorten(top_component, 90), styles["Small"]),
            Paragraph(f"{top_component_count} eventos", styles["RightSmall"]),
        ],
        [
            Paragraph("<b>Principal causa raiz</b>", styles["Small"]),
            Paragraph(shorten(top_cause, 90), styles["Small"]),
            Paragraph(f"{top_cause_count} eventos", styles["RightSmall"]),
        ],
        [
            Paragraph("<b>Impacto mais recorrente</b>", styles["Small"]),
            Paragraph(shorten(impacts.most_common(1)[0][0], 90), styles["Small"]),
            Paragraph(f"{impacts.most_common(1)[0][1]} eventos", styles["RightSmall"]),
        ],
    ]
    insights = Table(insight_data, colWidths=[4.4 * cm, 10.7 * cm, 3.1 * cm])
    insights.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALETTE["bg"]),
                ("BOX", (0, 0), (-1, -1), 0.6, PALETTE["line"]),
                ("GRID", (0, 0), (-1, -1), 0.25, PALETTE["line"]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(insights)

    story.append(Paragraph("Distribuicao Por Componente", styles["SectionTitle"]))
    story.append(count_table("Componente", components, total, styles, max_rows=10))
    story.append(PageBreak())

    story.append(Paragraph("Causas Raiz Mais Frequentes", styles["SectionTitle"]))
    story.append(count_table("Causa raiz", causes, total, styles, max_rows=12))
    story.append(Spacer(1, 0.35 * cm))
    story.append(Paragraph("Impactos Operacionais", styles["SectionTitle"]))
    story.append(count_table("Impacto", impacts, total, styles, max_rows=10))
    story.append(PageBreak())

    story.append(Paragraph("Agentes e Pastas Com Mais Ocorrencias", styles["SectionTitle"]))
    left = count_table("ID do agente", agents, total, styles, max_rows=12)
    right = count_table("Pasta", folders, total, styles, max_rows=12)
    two_col = Table([[left, right]], colWidths=[9.4 * cm, 9.4 * cm])
    two_col.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(two_col)
    story.append(PageBreak())

    story.append(Paragraph("Eventos Recentes", styles["SectionTitle"]))
    recent_rows = sorted(rows, key=parse_date, reverse=True)[:25]
    data = [[
        Paragraph("Data/hora", styles["HeaderSmall"]),
        Paragraph("Agente", styles["HeaderSmall"]),
        Paragraph("Componente", styles["HeaderSmall"]),
        Paragraph("Causa raiz", styles["HeaderSmall"]),
        Paragraph("Impacto", styles["HeaderSmall"]),
    ]]
    table_style = [
        ("BACKGROUND", (0, 0), (-1, 0), PALETTE["navy"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), PALETTE["white"]),
        ("BOX", (0, 0), (-1, -1), 0.5, PALETTE["line"]),
        ("GRID", (0, 0), (-1, -1), 0.25, PALETTE["line"]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for index, row in enumerate(recent_rows, start=1):
        _, bg = classify_color(row["causa_raiz"])
        data.append(
            [
                Paragraph(row["data_hora"], styles["TableSmall"]),
                Paragraph(shorten(row["id_agente"], 18), styles["TableSmall"]),
                Paragraph(shorten(row["componente"], 34), styles["TableSmall"]),
                Paragraph(shorten(row["causa_raiz"], 48), styles["TableSmall"]),
                Paragraph(shorten(row["impacto"], 55), styles["TableSmall"]),
            ]
        )
        table_style.append(("BACKGROUND", (0, index), (-1, index), bg if index % 2 else PALETTE["white"]))

    recent = Table(data, colWidths=[2.7 * cm, 3.0 * cm, 4.1 * cm, 4.6 * cm, 4.1 * cm], repeatRows=1)
    recent.setStyle(TableStyle(table_style))
    story.append(recent)

    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)


def main():
    rows = load_rows()
    if not rows:
        raise SystemExit("Nenhum erro encontrado nos logs para gerar o relatorio.")
    build_pdf(rows)
    print(PDF_PATH)


if __name__ == "__main__":
    main()
