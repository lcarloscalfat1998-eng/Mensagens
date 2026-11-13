"""Proposta de carteira nova: projeção líquida de IR por cenário de CDI."""
from __future__ import annotations

import datetime as dt
import json

from . import dados, metricas
from .render import brl, pct

IR = 0.15


def _bruto(a: dict, cdi: float, anos: float) -> float:
    du = round(252 * anos)
    if a["tipo"] == "pre":
        return (1 + a["taxa"]) ** anos - 1
    return (1 + a["taxa"] * ((1 + cdi) ** (1 / 252) - 1)) ** du - 1


def _liquido(a: dict, cdi: float, anos: float) -> float:
    g = _bruto(a, cdi, anos)
    return g if a["isento"] else g * (1 - IR)


def _empate(a: dict, b: dict, anos: float) -> float | None:
    """CDI médio em que os ativos a e b entregam o mesmo valor líquido."""
    f = lambda c: _liquido(a, c, anos) - _liquido(b, c, anos)
    lo, hi = 0.02, 0.30
    if f(lo) * f(hi) > 0:
        return None
    for _ in range(80):
        m = (lo + hi) / 2
        if f(lo) * f(m) <= 0:
            hi = m
        else:
            lo = m
    return (lo + hi) / 2


def contexto(cfg: dict) -> dict:
    anos = float(cfg.get("horizonte_anos", 3))
    cdi_atual = dados.cdi_anual_atual()
    selic = dados.selic_meta_atual()
    ativos = []
    for a in cfg["ativos"]:
        a = dict(a)
        a["isento"] = bool(a.get("isento", False))
        a["fgc"] = bool(a.get("fgc", False))
        a["valor"] = float(a["valor"])
        if a.get("taxa") == "historico":
            ini, fim = metricas.janela_12m()
            c = dados.norm_cnpj(a["cnpj"])
            s = dados.cotas([c], ini - dt.timedelta(days=10), fim)[c]
            st = metricas.estatisticas(s, ini, fim)
            a["taxa"] = round(st["pct_cdi"], 3)
            a["historico"] = st
        a["taxa"] = float(a["taxa"])
        if a.get("cnpj") and not a.get("id"):
            a["id"] = f"CNPJ {dados.norm_cnpj(a['cnpj'])}"
        ativos.append(a)
    total = sum(a["valor"] for a in ativos)

    cenarios = []
    for c in cfg.get("cenarios", [{"nome": "Mantido", "cdi": "atual"}, {"nome": "Queda gradual", "cdi": 0.12}, {"nome": "Queda forte", "cdi": 0.105}]):
        v = cdi_atual if c["cdi"] == "atual" else float(c["cdi"])
        cenarios.append({"nome": c["nome"], "cdi": round(v, 4)})

    # textos do papel de cada ativo
    pres = [a for a in ativos if a["tipo"] == "pre"]
    isentos = [a for a in ativos if a["tipo"] == "cdi" and a["isento"]]
    for a in ativos:
        if a.get("papel"):
            continue
        if a["tipo"] == "pre":
            t = [f"Trava {pct(a['taxa'])} ao ano até o vencimento."]
            if isentos:
                ref = max(isentos, key=lambda x: x["taxa"])
                e = _empate(a, ref, anos)
                if e:
                    t.append(f"Pelo valor líquido, supera {ref['nome']} sempre que o CDI médio ficar abaixo de {pct(e)} ao ano.")
            t.append(f"Também supera um investimento de 100% do CDI tributado enquanto o CDI médio ficar abaixo de {pct(a['taxa'])}.")
            a["papel"] = " ".join(t)
        elif a["isento"]:
            a["papel"] = f"Isento de IR para pessoa física. Os {pct(a['taxa'],1)} do CDI equivalem a cerca de {pct(a['taxa']/(1-IR),1)} do CDI num investimento tributado."
        elif a.get("historico"):
            h = a["historico"]
            a["papel"] = f"Rendeu {pct(h['retorno'])} nos últimos 12 meses ({pct(h['pct_cdi'],1)} do CDI). Na projeção, usamos esse percentual."
        else:
            a["papel"] = f"Pós-fixado a {pct(a['taxa'],1)} do CDI, tributado pela tabela regressiva."

    tabela_cen = []
    for c in cenarios:
        fin = sum(a["valor"] * (1 + _liquido(a, c["cdi"], anos)) for a in ativos)
        bench = total * (1 + ((1 + c["cdi"]) ** anos - 1) * (1 - IR))
        tabela_cen.append({"nome": c["nome"], "cdi": c["cdi"], "fin": fin, "bench": bench, "dif": fin - bench})

    js_ativos = [{k: a.get(k) for k in ("nome", "id", "valor", "tipo", "taxa", "isento", "liquidez", "fgc")} for a in ativos]
    return {
        "titulo": cfg.get("titulo", f"Carteira de {brl(total)}"),
        "titulo_html": cfg.get("titulo_html") or (f'Carteira de <span class="x">{brl(total)}</span>' if "titulo" not in cfg else cfg["titulo"]),
        "eyebrow": cfg.get("eyebrow", "Proposta de carteira · renda fixa"),
        "descricao": cfg.get("descricao", "Projeção líquida de IR até o vencimento, com o CDI médio ajustável abaixo."),
        "vencimento": cfg.get("vencimento_label", f"{anos:g} anos"),
        "anos": anos, "total": total, "ativos": ativos, "cenarios": cenarios, "tabela_cen": tabela_cen,
        "cdi_atual": cdi_atual, "selic": selic,
        "js": json.dumps({"ativos": js_ativos, "cenarios": cenarios, "anos": anos, "ir": IR, "cdi": round(cdi_atual, 4)}, ensure_ascii=False),
        "observacoes": cfg.get("observacoes", []),
        "aviso": cfg.get("aviso") or "Taxas indicativas, sujeitas à disponibilidade no momento da aplicação. Rentabilidade passada não é garantia de rentabilidade futura.",
    }


def mensagem(ctx: dict) -> str:
    c = ctx["tabela_cen"][0]
    return "\n".join([
        "Olá! Segue a proposta de carteira que conversamos.",
        "",
        f"Com o CDI em {pct(c['cdi'])} ao ano, a projeção é chegar a {brl(c['fin'])} líquidos em {ctx['vencimento']}, "
        f"{brl(c['dif'])} acima de uma aplicação em 100% do CDI tributada.",
        "O documento mostra também os cenários de queda de juros.",
        "",
        "Fico à disposição para conversarmos.",
    ])
