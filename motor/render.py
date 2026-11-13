"""Geração de HTML (Jinja), PDF (Chromium/Playwright via Node) e formatação pt-BR."""
from __future__ import annotations

import subprocess
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

PASTA = Path(__file__).resolve().parent
TEMPLATES = PASTA / "templates"

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def brl(x, cents: bool = False) -> str:
    if x is None:
        return "–"
    neg = x < 0
    x = abs(x)
    s = f"{x:,.2f}" if cents else f"{round(x):,}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return ("−" if neg else "") + "R$ " + s


def pct(x, d: int = 2, sinal: bool = False) -> str:
    if x is None:
        return "–"
    s = f"{abs(x)*100:.{d}f}".replace(".", ",") + "%"
    if x < 0:
        return "−" + s
    return ("+" if sinal and x > 0 else "") + s


def data(d) -> str:
    return d.strftime("%d/%m/%Y") if d else "–"


def mes(ym) -> str:
    y, m = ym
    return f"{MESES[m-1]}/{str(y)[2:]}"


def mes_longo(d) -> str:
    return f"{MESES[d.month-1]}/{d.year}"


def ambiente() -> Environment:
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html", "j2"]))
    env.filters.update(brl=brl, pct=pct, data=data, mes=mes, mes_longo=mes_longo)
    env.globals["css_base"] = (TEMPLATES / "_base.css").read_text(encoding="utf-8")
    return env


def gerar_html(template: str, contexto: dict, destino: Path) -> Path:
    html = ambiente().get_template(template).render(**contexto)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html, encoding="utf-8")
    return destino


PRINT_CSS = """html{background:#0a0a0a;-webkit-print-color-adjust:exact;print-color-adjust:exact}
@page{size:A4;margin:0}
body{margin:0;padding-block:36px!important;padding-left:40px!important;padding-right:40px!important}
.verdict,.thesis,.ba,.step,.card,.read,.chartbox,.method li,tr,h2{break-inside:avoid}
h2{break-after:avoid}
.pb{break-before:page;padding-top:44px}
.ctrl input,.chips{display:none!important}"""


def gerar_pdf(html: Path, pdf: Path) -> Path:
    """Converte a página em PDF A4 (fundo preto, quebras nas seções marcadas com .pb)."""
    impressao = html.with_name(html.stem + ".print.html")
    corpo = html.read_text(encoding="utf-8")
    impressao.write_text(
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width"><style>{PRINT_CSS}</style></head><body>'
        + corpo + "</body></html>", encoding="utf-8")
    try:
        subprocess.run(["node", str(PASTA / "pdf.js"), str(impressao), str(pdf)], check=True, timeout=180)
    finally:
        impressao.unlink(missing_ok=True)
    return pdf
