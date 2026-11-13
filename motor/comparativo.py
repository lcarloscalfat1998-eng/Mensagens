"""Estudo comparativo: carteira proposta de fundos × fundo atual, nos últimos N meses."""
from __future__ import annotations

import datetime as dt
import math
import statistics

from . import dados, metricas
from .render import brl, mes, pct


def _grafico(cum: dict, rotulos: list[str], inicio: str) -> str:
    """SVG da rentabilidade acumulada (Proposta, Atual, CDI)."""
    W, H, L, R, T, B = 720, 300, 46, 108, 16, 34
    n = len(rotulos)
    topo = max(max(v) for v in cum.values()) - 1
    passo = 0.02 if topo <= 0.12 else 0.04 if topo <= 0.24 else 0.1
    ymax = passo * math.ceil(max(topo, 0.01) / passo)
    ymin = min(0.0, min(min(v) for v in cum.values()) - 1)
    ymin = -passo * math.ceil(-ymin / passo) if ymin < 0 else 0.0
    xs = lambda i: L + i * (W - L - R) / n
    ys = lambda v: T + (1 - (v - ymin) / (ymax - ymin)) * (H - T - B)
    out = []
    g = ymin
    while g <= ymax + 1e-9:
        y = ys(g)
        out.append(f'<line x1="{L}" x2="{W-R}" y1="{y:.1f}" y2="{y:.1f}" class="grid"/>'
                   f'<text x="{L-8}" y="{y+4:.1f}" class="ax" text-anchor="end">{round(g*100)}%</text>')
        g += passo
    for i in range(0, n + 1, 2):
        out.append(f'<text x="{xs(i):.1f}" y="{H-12}" class="ax" text-anchor="middle">{rotulos[i-1] if i else inicio}</text>')
    fins = []
    for k, cls in (("P", "s-prop"), ("A", "s-cur"), ("C", "s-cdi")):
        d = "M" + " L".join(f"{xs(i):.1f},{ys(v-1):.1f}" for i, v in enumerate(cum[k]))
        out.append(f'<path d="{d}" class="{cls}" fill="none"/>')
        fins.append((ys(cum[k][-1] - 1), k, cls))
    fins.sort()
    usados = []
    for y, k, cls in fins:
        yy = y if not usados or y - usados[-1] >= 15 else usados[-1] + 15
        usados.append(yy)
        out.append(f'<circle cx="{xs(n):.1f}" cy="{y:.1f}" r="3.5" class="{cls}-dot"/>'
                   f'<text x="{xs(n)+9:.1f}" y="{yy+4:.1f}" class="lbl {cls}-t">{pct(cum[k][-1]-1)}</text>')
    return f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Rentabilidade acumulada">{"".join(out)}</svg>'


def contexto(cfg: dict) -> dict:
    valor = float(cfg["valor"])
    meses = int(cfg.get("meses", 12))
    ref = cfg.get("data_ref") or dt.date.today()
    if isinstance(ref, str):
        ref = dt.date.fromisoformat(ref)
    ini, fim = metricas.janela_12m(ref, meses)
    prop = cfg["proposta"]
    atual = cfg["atual"]
    soma = sum(float(f["peso"]) for f in prop)
    if abs(soma - 1) > 1e-6:
        raise ValueError(f"Os pesos da proposta somam {soma:.4f}, e não 100%.")
    cnpjs = [dados.norm_cnpj(f["cnpj"]) for f in prop] + [dados.norm_cnpj(atual["cnpj"])]
    series = dados.cotas(cnpjs, ini - dt.timedelta(days=10), fim)
    faltando = [c for c in cnpjs if c not in series]
    if faltando:
        raise ValueError(f"Sem cotas na CVM para: {', '.join(faltando)}. Confira o CNPJ.")

    ref_serie = series[dados.norm_cnpj(atual["cnpj"])]
    fundos = []
    for f in prop + [atual]:
        c = dados.norm_cnpj(f["cnpj"])
        info = dados.info_fundo(c) or {}
        s = series[c]
        st = metricas.estatisticas(s, ini, fim)
        if not st or not st["completo"]:
            raise ValueError(f"{f.get('nome', c)} não tem {meses} meses de histórico na janela.")
        fundos.append({"cnpj": c, "nome": f.get("nome") or info.get("nome"), "peso": f.get("peso"),
                       "s": st, "mensal": [m["retorno"] for m in metricas.retornos_mensais(s, ini, fim)]})
    proposta, atualf = fundos[:-1], fundos[-1]
    cdi_m = [m["retorno"] for m in metricas.cdi_mensal(ini, fim, ref_serie)]
    meses_l = metricas.meses_entre(ini, fim)
    rot = [mes(m) for m in meses_l]

    # carteira proposta: aplicação única, sem rebalanceamento
    cum = {"P": [1.0], "A": [1.0], "C": [1.0]}
    acum = {f["cnpj"]: [1.0] for f in proposta}
    for i in range(len(meses_l)):
        for f in proposta:
            acum[f["cnpj"]].append(acum[f["cnpj"]][-1] * (1 + f["mensal"][i]))
        cum["A"].append(cum["A"][-1] * (1 + atualf["mensal"][i]))
        cum["C"].append(cum["C"][-1] * (1 + cdi_m[i]))
    cum["P"] = [sum(float(f["peso"]) * acum[f["cnpj"]][j] for f in proposta) for j in range(len(meses_l) + 1)]
    p_mensal = [cum["P"][j] / cum["P"][j - 1] - 1 for j in range(1, len(cum["P"]))]

    # risco diário da carteira proposta
    datas = sorted(set.intersection(*[set(series[f["cnpj"]].index) for f in proposta]))
    d0 = metricas.ultima_ate(series[proposta[0]["cnpj"]], ini)
    datas = [d for d in datas if d0 <= d <= fim]
    v = [sum(float(f["peso"]) * series[f["cnpj"]][d] / series[f["cnpj"]][datas[0]] for f in proposta) for d in datas]
    rd = [v[i] / v[i - 1] - 1 for i in range(1, len(v))]
    vol_p = statistics.pstdev(rd) * math.sqrt(252)
    pico, mdd_p = 0.0, 0.0
    for x in v:
        pico = max(pico, x)
        mdd_p = min(mdd_p, x / pico - 1)

    cdi12 = cum["C"][-1] - 1
    P12, A12 = cum["P"][-1] - 1, cum["A"][-1] - 1
    linhas = []
    for f in proposta:
        r = acum[f["cnpj"]][-1] - 1
        linhas.append({**f, "r": r, "pcdi": r / cdi12, "aplic": valor * float(f["peso"]), "final": valor * float(f["peso"]) * (1 + r)})

    leituras = []
    for f in linhas:
        neg = sum(1 for x in f["mensal"] if x < 0)
        acima = sum(1 for x, c in zip(f["mensal"], cdi_m) if x >= c)
        txt = f"Rendeu {pct(f['r'])} ({pct(f['pcdi'],1)} do CDI), com volatilidade de {pct(f['s']['vol'])}."
        if neg:
            txt += f" Teve {neg} {'mês negativo' if neg == 1 else 'meses negativos'} e queda máxima de {pct(f['s']['mdd'],1)}."
        else:
            txt += f" Ficou igual ou acima do CDI em {acima} dos {len(meses_l)} meses."
        leituras.append({"titulo": f"{f['nome']} · {pct(float(f['peso']),0)}", "texto": txt})
    leituras.append({"titulo": "Risco da carteira",
                     "texto": f"A carteira proposta teve volatilidade de {pct(vol_p)} ao ano e queda máxima de {pct(mdd_p)} no período."})

    tabela = []
    for i, m in enumerate(meses_l):
        tabela.append({"mes": rot[i], "fundos": [f["mensal"][i] for f in proposta], "p": p_mensal[i],
                       "a": atualf["mensal"][i], "c": cdi_m[i], "ganhou": p_mensal[i] > atualf["mensal"][i]})

    return {
        "titulo": cfg.get("titulo", "Carteira proposta × fundo atual"),
        "eyebrow": cfg.get("eyebrow", f"Estudo comparativo · {meses} meses"),
        "valor": valor, "ini": atualf["s"]["ini"], "fim": atualf["s"]["fim"], "ini_mes": ini + dt.timedelta(days=1),
        "proposta": linhas, "atual": atualf, "P12": P12, "A12": A12, "cdi12": cdi12,
        "pcdi_p": P12 / cdi12, "pcdi_a": A12 / cdi12, "dif": P12 - A12,
        "dif_txt": ("+" if P12 >= A12 else "−") + f"{abs(P12 - A12)*100:.2f}".replace(".", ","),
        "vol_p": vol_p, "mdd_p": mdd_p, "grafico": _grafico(cum, rot, mes((ini.year, ini.month))), "tabela": tabela,
        "leituras": leituras, "tese": cfg.get("tese"), "observacoes": cfg.get("observacoes", []),
        "aviso": cfg.get("aviso") or "Rentabilidade passada não é garantia de rentabilidade futura. Fundos de investimento não contam com garantia do administrador, do gestor, de mecanismo de seguro ou do Fundo Garantidor de Créditos (FGC).",
    }


def mensagem(ctx: dict) -> str:
    return "\n".join([
        "Olá! Segue o estudo comparativo da sua carteira.",
        "",
        f"Nos últimos 12 meses, a carteira proposta rendeu {pct(ctx['P12'])} ({pct(ctx['pcdi_p'],1)} do CDI), "
        f"contra {pct(ctx['A12'])} ({pct(ctx['pcdi_a'],1)} do CDI) do {ctx['atual']['nome']}.",
        f"Sobre {brl(ctx['valor'])}, a diferença foi de cerca de {brl(ctx['valor']*ctx['dif'])} no período.",
        "",
        "O documento completo está em anexo. Fico à disposição para conversarmos.",
    ])
