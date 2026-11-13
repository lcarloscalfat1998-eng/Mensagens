"""Monta o documento de readequação a partir do Plano."""
from __future__ import annotations

import datetime as dt
import re

from .readequacao import DECISAO, Plano
from .dados import sem_acento
from .render import brl, pct

CORES = {
    "Títulos públicos": "#f3f3f3",
    "Bancários e quase soberanos": "#bdbdbd",
    "Fundo de destino (DI)": "#ffc709",
    "Crédito privado": "#8a7a3c",
    "Crédito privado em alerta": "#e7a23a",
    "Fundos de renda fixa e crédito": "#6b6b6b",
    "Fundos fechados (FIDC, FIP, Fiagro, FII)": "#3d3d3d",
    "Multimercados": "#4b5a63",
    "Fundos de ações": "#7a5c99",
    "Internacional": "#4f8fd6",
    "Cripto": "#a65bd6",
    "Renda variável Brasil": "#5aa66e",
    "COE": "#8f6bd6",
    "Outros": "#262626",
}


def _stats(plano: Plano, cnpj):
    return plano.stats.get(cnpj) if cnpj else None


def contexto(plano: Plano, entrada: dict | None = None) -> dict:
    entrada = entrada or {}
    r = plano.regras
    textos = r.get("textos", {})
    dest = _stats(plano, plano.destino_cnpj)
    cdi = plano.stats.get("_cdi")
    ini, fim = plano.janela

    resgates = plano.acoes_de("resgatar")
    fechados = plano.acoes_de("sair_quando_liberar")
    vendas = plano.acoes_de("vender")
    ajustes = plano.ajustes
    acompanhar = plano.acoes_de("acompanhar")
    monitorar = plano.acoes_de("monitorar")

    # ---- fundos que saem
    fundos = []
    for a in resgates + fechados:
        p = a.posicao
        s = _stats(plano, p.cnpj)
        fundos.append({"nome": p.nome, "cnpj": p.cnpj, "valor": a.valor, "s": s, "motivo": a.motivo,
                       "fechado": a.tipo == "sair_quando_liberar"})
    total_resgates = sum(a.valor for a in resgates)

    # ---- crédito privado
    ajuste_por_nome = {}
    for a in ajustes:
        ajuste_por_nome[a.posicao.nome] = ajuste_por_nome.get(a.posicao.nome, 0) + a.valor
    creditos = []
    saida_nomes = {a.posicao.nome for a in vendas}
    for p in plano.carteira.posicoes:
        if p.categoria != "credito_privado":
            continue
        if p.nome in saida_nomes:
            rotulo, cls = "Vender", "sell"
        elif p.nome in ajuste_por_nome:
            rotulo, cls = f"Vender {brl(ajuste_por_nome[p.nome])}", "sell"
        else:
            rotulo, cls = DECISAO.get(p.status, ("Manter", "keep"))
        nota = p.nota or ("Emissor ainda não classificado em regras.yaml." if p.status == "sem_classificacao" else "")
        if p.nome in ajuste_por_nome:
            nota = (nota + " " if nota else "") + "Venda parcial para enquadrar no limite por emissor."
        creditos.append({"nome": p.nome, "taxa": p.taxa, "venc": p.vencimento, "posicao": p.posicao,
                         "resultado": p.resultado, "nota": nota, "rotulo": rotulo, "cls": cls})
    ordem = {"sell": 0, "watch": 1, "keep": 2}
    creditos.sort(key=lambda c: (ordem[c["cls"]], -c["posicao"]))

    # ---- enquadramento (depois)
    c = r["compliance"]
    antes_por = {}
    from .enquadramento import verificar
    _, quadro_antes = verificar(plano.carteira.posicoes, plano.total_antes, r)
    for regra, linhas in quadro_antes.items():
        for e in linhas:
            antes_por[(regra, e.chave)] = e.pct
    enq = []
    for regra, titulo, lim in (("emissor", "Maiores emissores de crédito privado", c["limite_emissor"]),
                               ("nicho", "Nichos (setor do devedor)", c["limite_nicho"]),
                               ("fundo_fechado", "Fundos fechados", c["limite_fundo_fechado"])):
        linhas = plano.quadro_depois.get(regra, [])
        chaves = {e.chave for e in linhas} | {k for (rg, k) in antes_por if rg == regra}
        depois_por = {e.chave: e.pct for e in linhas}
        rows = sorted(({"chave": k, "antes": antes_por.get((regra, k), 0.0), "depois": depois_por.get(k, 0.0)} for k in chaves),
                      key=lambda x: -max(x["antes"], x["depois"]))
        if regra == "emissor":
            rows = rows[:8]
        enq.append({"titulo": titulo, "limite": lim, "rows": rows})

    # ---- antes e depois
    grupos = []
    for k in plano.grupos_antes:
        a, d = plano.grupos_antes[k], plano.grupos_depois.get(k, 0.0)
        if a < 0.5 and d < 0.5:
            continue
        grupos.append({"nome": k, "cor": CORES.get(k, "#555"), "antes": a, "depois": d,
                       "pa": a / plano.total_antes, "pd": d / plano.total_depois, "delta": d - a})

    # ---- tese (automática, ou da entrada)
    pts = []
    cp_fundos = [f for f in fundos if f["s"] and f["s"]["pct_cdi"] is not None and not f["fechado"]
                 and f["s"]["vol"] < 0.02 and dest and f["s"]["retorno"] < dest["retorno"]]
    if cp_fundos:
        nomes = ", ".join(f["nome"].split(" Advisory")[0].split(" FIC")[0] for f in cp_fundos[:3])
        faixa = sorted(f["s"]["pct_cdi"] for f in cp_fundos)
        pts.append({"titulo": "Fundos replicáveis",
                    "texto": f"{nomes} fizeram de {pct(faixa[0],1)} a {pct(faixa[-1],1)} do CDI. O fundo de destino entrega o mesmo papel com liquidez e risco menores."})
    volateis = [f for f in fundos if f["s"] and f["s"]["vol"] >= 0.05 and "global" not in f["motivo"].lower()
                and "incentivad" not in f["nome"].lower()]
    if volateis:
        partes = ", ".join(f"{f['nome'].split(' FI')[0]} ({pct(f['s']['retorno'],1)})" for f in volateis[:3])
        pts.append({"titulo": "Posições sem função",
                    "texto": f"{partes}: {'pesam' if len(volateis) > 1 else 'pesa'} pouco no patrimônio, mas {'trazem' if len(volateis) > 1 else 'traz'} a maior volatilidade da carteira."})
    alerta = [a.posicao.emissor for a in vendas]
    if alerta or acompanhar:
        t = ""
        if alerta:
            t += f"{', '.join(alerta)}: crédito em deterioração, o risco não compensa a taxa. "
        if acompanhar:
            t += f"{', '.join(a.posicao.emissor for a in acompanhar)}: sem liquidez para venda, será acompanhado."
        pts.append({"titulo": "Crédito em deterioração", "texto": t.strip()})
    if ajustes:
        emis = sorted({a.motivo.split(" em ")[0] for a in ajustes})
        pts.append({"titulo": "Enquadramento", "texto": f"{'; '.join(emis)} acima do limite da política. Sugerimos vender o excesso."})
    tese = entrada.get("tese") or {
        "titulo": "Menos risco, <em>mesma rentabilidade</em>" if not cp_fundos else "Os fundos de crédito renderam <em>menos que o DI</em>, com mais risco",
        "texto": (f"Nos últimos 12 meses, o {plano.destino_nome} rendeu {pct(dest['retorno'])} ({pct(dest['pct_cdi'],1)} do CDI). "
                  + (f"{len(cp_fundos)} dos fundos de crédito que saem renderam menos que ele, mesmo carregando risco de crédito." if cp_fundos else ""))
        if dest else "",
        "pontos": pts[:4],
    }

    # ---- etapas
    etapa1 = []
    if resgates:
        etapa1.append(f"Resgatar {len(resgates)} fundo{'s' if len(resgates) > 1 else ''}: <b>{brl(total_resgates)}</b> líquidos.")
    if vendas:
        etapa1.append(f"Vender {', '.join(a.posicao.nome.split(' - ')[0] for a in vendas)}: <b>{brl(sum(a.valor for a in vendas))}</b>.")
    if ajustes:
        etapa1.append(f"Enquadramento: vender <b>{brl(sum(a.valor for a in ajustes))}</b> de {', '.join(sorted({a.posicao.nome.split(' - ')[0] for a in ajustes}))}.")
    etapa1.append(f"Tudo vai para o <b>{plano.destino_nome.split(' FI')[0]}</b>, conforme o prazo de resgate de cada fundo.")
    etapa2 = [f"<b>{a.posicao.nome.split(' FIDC')[0].split(' FIP')[0]}</b> ({brl(a.valor)}) é fundo fechado: sair pelas amortizações ou por venda no secundário." for a in fechados]
    etapa2 += [f"Acompanhar a reestruturação de <b>{a.posicao.emissor}</b>." for a in acompanhar]
    if monitorar:
        etapa2.append(f"Revisar <b>{' e '.join(a.posicao.emissor for a in monitorar)}</b> a cada resultado trimestral.")
    if any(p.categoria == "fundo_fechado" for p in plano.depois):
        etapa2.append("Fundos fechados e ilíquidos seguem até o fim do prazo.")
    etapas = [
        {"quando": "Etapa 1 · agora", "titulo": "Simplificar e reduzir risco", "itens": etapa1},
        {"quando": "Etapa 2 · próximos meses", "titulo": "Acompanhar o que ficou", "itens": etapa2 or ["Revisar a carteira no próximo trimestre."]},
        {"quando": "Etapa 3 · ao longo do tempo", "titulo": "Realocar com calma", "itens": textos.get("etapa3", [])},
    ]

    # ---- pontos de atenção
    cards = []
    for a in acompanhar:
        cards.append({"titulo": a.posicao.nome.split(" - ")[0].title().replace("Cri ", "CRI ").replace("Cra ", "CRA ").replace("Deb ", "Deb. "),
                      "texto": textos.get("sem_liquidez", "")})
    isentos = [f for f in fundos if "incentivad" in f["nome"].lower()]
    if isentos and dest:
        eq = ", ".join(pct(f["s"]["retorno"] / 0.85, 1) for f in isentos if f["s"])
        cards.append({"titulo": "Isenção de IR",
                      "texto": f"Ao sair dos fundos de debêntures incentivadas, o recurso passa a ser tributado no fundo de destino, inclusive pelo come-cotas. Mesmo assim, ele rendeu mais: {pct(dest['retorno'],1)} bruto contra {eq} de equivalente bruto dos incentivados."})
    if any("global" in f["motivo"].lower() for f in fundos):
        cards.append({"titulo": "Exposição global", "texto": textos.get("exposicao_global", "")})
    if ajustes:
        perdas = [a for a in ajustes if (a.posicao.resultado or 0) < -0.01]
        txt = "A venda parcial reenquadra a carteira no limite por emissor."
        if perdas:
            txt += f" Atenção: {', '.join(a.posicao.nome.split(' - ')[0] for a in perdas)} está com perda de marcação, e a venda realiza parte dela. Se preferir, o estouro pode ficar só registrado."
        isentos_aj = [a for a in ajustes if re.match(r"(cra|cri|lca|lci|lcd)\b", sem_acento(a.posicao.nome))]
        if isentos_aj:
            txt += " O título vendido é isento de IR, e o fundo de destino é tributado: a ideia é que esse valor volte aos poucos para isentos de outros emissores (etapa 3), mantendo a isenção sem concentrar risco."
        cards.append({"titulo": "Ajuste de enquadramento", "texto": txt})
    if resgates:
        cards.append({"titulo": "Prazos de resgate", "texto": "Fundos de crédito privado costumam ter resgate em D+30 ou mais, e fundos internacionais têm prazo próprio. O dinheiro chega ao fundo de destino em datas diferentes."})
    if vendas:
        cards.append({"titulo": "Venda de títulos", "texto": "As vendas foram consideradas pelo valor de posição de hoje. O preço no mercado secundário pode ser diferente."})

    sai = []
    if resgates:
        sai.append(f"{len(resgates)} fundo{'s' if len(resgates) > 1 else ''}")
    if vendas:
        sai.append(f"{len(vendas)} título{'s' if len(vendas) > 1 else ''}")
    n_aj = len({a.posicao.nome for a in ajustes})
    if sai:
        sai_big = " + ".join(sai)
        sai_sub = (f"{n_aj} venda{'s' if n_aj > 1 else ''} parcial para enquadramento" if n_aj else "")
    elif n_aj:
        sai_big = f"{n_aj} venda{'s' if n_aj > 1 else ''} parcial"
        sai_sub = "para enquadrar na política de risco"
    else:
        sai_big, sai_sub = "Nada", "carteira enquadrada na política"
    if fechados:
        sai_sub = (sai_sub + " · " if sai_sub else "") + "fechados saem conforme liberar"
    objetivos = []
    if resgates or fechados:
        objetivos.append("tirar fundos replicáveis ou sem função na carteira")
    if vendas:
        objetivos.append("sair de emissores com crédito em deterioração")
    if ajustes or plano.estouros_antes:
        objetivos.append("enquadrar a carteira na política de risco")
    if not objetivos:
        objetivos.append("revisar o risco e a liquidez da carteira")
    n = len(objetivos)
    obj_txt = ("Revisão das posições com " + ("um objetivo: " if n == 1 else ("dois objetivos: " if n == 2 else "três objetivos: "))
               + (", ".join(objetivos[:-1]) + " e " if n > 1 else "") + objetivos[-1] + ".")
    return {
        "titulo": plano.carteira.titulo or "Readequação da carteira",
        "sai_big": sai_big, "sai_sub": sai_sub, "objetivos": obj_txt,
        "data_posicao": plano.carteira.data_posicao,
        "plano": plano,
        "janela": (ini, fim),
        "janela_ini_mes": ini + dt.timedelta(days=1),
        "cdi": cdi,
        "dest": dest,
        "fundos": fundos,
        "total_resgates": total_resgates,
        "creditos": creditos,
        "enq": enq,
        "grupos": grupos,
        "tese": tese,
        "etapas": etapas,
        "cards": cards[:6],
        "n_fundos": len(resgates),
        "n_titulos": len(vendas),
        "n_ajustes": len({a.posicao.nome for a in ajustes}),
        "fechados": fechados,
        "estouros_depois": plano.estouros_depois,
        "textos": textos,
    }


def mensagem(ctx: dict) -> str:
    """Texto curto para WhatsApp/e-mail."""
    p = ctx["plano"]
    motivos = []
    if p.ajustes:
        motivos.append("enquadrar a concentração por emissor na nossa política de risco")
    if p.acoes_de("resgatar"):
        motivos.append("substituir fundos que renderam abaixo do DI")
    if p.acoes_de("vender"):
        motivos.append("sair de emissores com crédito em deterioração")
    linhas = [
        "Olá! Segue a proposta de readequação da sua carteira.",
        "",
        f"Resumo: sugerimos concentrar {brl(p.valor_destino_agora)} no {p.destino_nome.split(' FI')[0]}, "
        f"reduzindo o crédito privado de {pct(p.credito_antes/p.total_antes,0)} para {pct(p.credito_depois/p.total_depois,0)} do patrimônio.",
    ]
    if motivos:
        linhas.append("O objetivo é " + ", ".join(motivos[:-1]) + (" e " if len(motivos) > 1 else "") + motivos[-1] + ".")
    if ctx["dest"] and ctx["fundos"]:
        linhas.append(f"Nos últimos 12 meses, esse fundo rendeu {pct(ctx['dest']['retorno'])} ({pct(ctx['dest']['pct_cdi'],1)} do CDI), mais que os fundos de crédito que saem.")
    linhas += ["", "O documento completo está em anexo. Fico à disposição para conversarmos."]
    return "\n".join(linhas)
