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


def _carteira(fundos: list[dict], series: dict, ini, fim, n: int) -> dict:
    """Carteira com aplicação única, sem rebalanceamento: mensal, acumulado, volatilidade e maior queda."""
    acum = {f["cnpj"]: [1.0] for f in fundos}
    for i in range(n):
        for f in fundos:
            acum[f["cnpj"]].append(acum[f["cnpj"]][-1] * (1 + f["mensal"][i]))
    cum = [sum(float(f["peso"]) * acum[f["cnpj"]][j] for f in fundos) for j in range(n + 1)]
    mensal = [cum[j] / cum[j - 1] - 1 for j in range(1, n + 1)]
    datas = sorted(set.intersection(*[set(series[f["cnpj"]].index) for f in fundos]))
    d0 = max(metricas.ultima_ate(series[f["cnpj"]], ini) for f in fundos)
    datas = [d for d in datas if d0 <= d <= fim]
    v = [sum(float(f["peso"]) * series[f["cnpj"]][d] / series[f["cnpj"]][datas[0]] for f in fundos) for d in datas]
    rd = [v[i] / v[i - 1] - 1 for i in range(1, len(v))]
    pico, mdd = 0.0, 0.0
    for x in v:
        pico = max(pico, x)
        mdd = min(mdd, x / pico - 1)
    return {"acum": acum, "cum": cum, "mensal": mensal, "vol": statistics.pstdev(rd) * math.sqrt(252), "mdd": mdd}


def _lista(x) -> list[dict]:
    x = [x] if isinstance(x, dict) else list(x)
    if all("peso" not in f for f in x):
        for f in x:
            f["peso"] = 1 / len(x)
    return x


def contexto(cfg: dict) -> dict:
    valor = float(cfg["valor"])
    meses = int(cfg.get("meses", 12))
    ref = cfg.get("data_ref") or dt.date.today()
    if isinstance(ref, str):
        ref = dt.date.fromisoformat(ref)
    ini, fim = metricas.janela_12m(ref, meses)
    prop, atual = _lista(cfg["proposta"]), _lista(cfg["atual"])
    for nome, lst in (("proposta", prop), ("atual", atual)):
        soma = sum(float(f["peso"]) for f in lst)
        if abs(soma - 1) > 1e-6:
            raise ValueError(f"Os pesos de '{nome}' somam {soma:.4f}, e não 100%.")
    cnpjs = [dados.norm_cnpj(f["cnpj"]) for f in prop + atual]
    series = dados.cotas(cnpjs, ini - dt.timedelta(days=10), fim)
    faltando = [c for c in cnpjs if c not in series]
    if faltando:
        raise ValueError(f"Sem cotas na CVM para: {', '.join(faltando)}. Confira o CNPJ.")

    def montar(lst):
        out = []
        for f in lst:
            c = dados.norm_cnpj(f["cnpj"])
            info = dados.info_fundo(c) or {}
            st = metricas.estatisticas(series[c], ini, fim)
            if not st or not st["completo"]:
                raise ValueError(f"{f.get('nome', c)} não tem {meses} meses de histórico na janela.")
            out.append({"cnpj": c, "nome": f.get("nome") or info.get("nome"), "peso": float(f["peso"]), "s": st,
                        "mensal": [m["retorno"] for m in metricas.retornos_mensais(series[c], ini, fim)]})
        return out

    proposta, atuais = montar(prop), montar(atual)
    meses_l = metricas.meses_entre(ini, fim)
    n = len(meses_l)
    rot = [mes(m) for m in meses_l]
    cdi_m = [m["retorno"] for m in metricas.cdi_mensal(ini, fim, series[atuais[0]["cnpj"]])]
    cdi_cum = [1.0]
    for x in cdi_m:
        cdi_cum.append(cdi_cum[-1] * (1 + x))
    P = _carteira(proposta, series, ini, fim, n)
    A = _carteira(atuais, series, ini, fim, n)
    cdi12 = cdi_cum[-1] - 1
    P12, A12 = P["cum"][-1] - 1, A["cum"][-1] - 1

    def linhas(lst, cart):
        out = []
        for f in lst:
            r = cart["acum"][f["cnpj"]][-1] - 1
            out.append({**f, "r": r, "pcdi": r / cdi12, "aplic": valor * f["peso"], "final": valor * f["peso"] * (1 + r)})
        return out

    lp, la = linhas(proposta, P), linhas(atuais, A)
    atual_nome = la[0]["nome"] if len(la) == 1 else cfg.get("atual_nome", "Carteira atual")

    leituras = []
    for f in la + lp:
        neg = sum(1 for x in f["mensal"] if x < 0)
        acima = sum(1 for x, c in zip(f["mensal"], cdi_m) if x >= c)
        lado = "atual" if f in la else "proposta"
        txt = f"Rendeu {pct(f['r'])} ({pct(f['pcdi'],1)} do CDI), com volatilidade de {pct(f['s']['vol'])}."
        if neg:
            pior = min(range(n), key=lambda i: f["mensal"][i])
            txt += f" Teve {neg} {'mês negativo' if neg == 1 else 'meses negativos'} e queda máxima de {pct(f['s']['mdd'],1)}"
            txt += f"; o pior mês foi {rot[pior]}, com {pct(f['mensal'][pior])}." if f["mensal"][pior] < -0.01 else "."
        else:
            txt += f" Ficou igual ou acima do CDI em {acima} dos {n} meses."
        peso = f" · {pct(f['peso'],0)}" if (lado == "proposta" and len(lp) > 1) or (lado == "atual" and len(la) > 1) else ""
        leituras.append({"titulo": f"{f['nome']}{peso}", "texto": txt, "lado": lado})
    if len(lp) > 1:
        leituras.append({"titulo": "Risco da carteira proposta", "lado": "proposta",
                         "texto": f"A carteira proposta teve volatilidade de {pct(P['vol'])} ao ano e queda máxima de {pct(P['mdd'])} no período."})

    tabela = []
    for i in range(n):
        tabela.append({"mes": rot[i], "fundos": [f["mensal"][i] for f in lp] if len(lp) > 1 else [],
                       "p": P["mensal"][i], "atuais": [f["mensal"][i] for f in la] if len(la) > 1 else [],
                       "a": A["mensal"][i], "c": cdi_m[i], "ganhou": P["mensal"][i] > A["mensal"][i]})

    cum = {"P": P["cum"], "A": A["cum"], "C": cdi_cum}
    return {
        "titulo": cfg.get("titulo", "Carteira proposta × fundo atual"),
        "eyebrow": cfg.get("eyebrow", f"Estudo comparativo · {meses} meses"),
        "valor": valor, "ini": la[0]["s"]["ini"], "fim": la[0]["s"]["fim"], "ini_mes": ini + dt.timedelta(days=1),
        "proposta": lp, "atuais": la, "multi_p": len(lp) > 1, "multi_a": len(la) > 1,
        "atual": {"nome": atual_nome, "cnpj": la[0]["cnpj"], "s": {"vol": A["vol"], "mdd": A["mdd"]}},
        "proposta_nome": cfg.get("proposta_nome", lp[0]["nome"] if len(lp) == 1 else "Carteira proposta"),
        "P12": P12, "A12": A12, "cdi12": cdi12,
        "pcdi_p": P12 / cdi12, "pcdi_a": A12 / cdi12, "dif": P12 - A12,
        "dif_txt": ("+" if P12 >= A12 else "−") + f"{abs(P12 - A12)*100:.2f}".replace(".", ","),
        "vol_p": P["vol"], "mdd_p": P["mdd"], "grafico": _grafico(cum, rot, mes((ini.year, ini.month))), "tabela": tabela,
        "leituras": leituras, "tese": cfg.get("tese"), "observacoes": cfg.get("observacoes", []),
        "aviso": cfg.get("aviso") or "Rentabilidade passada não é garantia de rentabilidade futura. Fundos de investimento não contam com garantia do administrador, do gestor, de mecanismo de seguro ou do Fundo Garantidor de Créditos (FGC).",
    }


def mensagem(ctx: dict) -> str:
    return "\n".join([
        "Olá! Segue o estudo comparativo da sua carteira.",
        "",
        f"Nos últimos 12 meses, {('o ' + ctx['proposta_nome']) if not ctx['multi_p'] else 'a carteira proposta'} rendeu {pct(ctx['P12'])} ({pct(ctx['pcdi_p'],1)} do CDI), "
        f"contra {pct(ctx['A12'])} ({pct(ctx['pcdi_a'],1)} do CDI) {'da carteira atual' if ctx['multi_a'] else 'do ' + ctx['atual']['nome']}.",
        f"Sobre {brl(ctx['valor'])}, a diferença foi de cerca de {brl(ctx['valor']*ctx['dif'])} no período.",
        "",
        "O documento completo está em anexo. Fico à disposição para conversarmos.",
    ])
