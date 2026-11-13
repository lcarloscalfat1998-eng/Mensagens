"""Plano de readequação: regras da casa + enquadramento + antes e depois."""
from __future__ import annotations

import copy
import datetime as dt
from collections import OrderedDict
from dataclasses import dataclass, field

from . import dados, metricas
from .carteira import GRUPOS, Carteira, Posicao
from .dados import norm_cnpj, sem_acento
from .enquadramento import Estouro, verificar

DECISAO = {
    "vender": ("Vender", "sell"),
    "sem_liquidez": ("Acompanhar", "watch"),
    "monitorar": ("Monitorar", "watch"),
    "manter": ("Manter", "keep"),
    "sem_classificacao": ("Classificar", "watch"),
}


@dataclass
class Acao:
    posicao: Posicao
    tipo: str          # resgatar | vender | vender_parcial | sair_quando_liberar | acompanhar | monitorar
    valor: float       # valor que sai (líquido de IR) ou posição afetada
    motivo: str = ""
    etapa: int = 1


@dataclass
class Plano:
    carteira: Carteira
    regras: dict
    acoes: list[Acao]
    depois: list[Posicao]
    total_antes: float
    total_depois: float
    ir: float
    destino_nome: str
    destino_cnpj: str
    valor_destino_agora: float
    valor_destino_total: float
    estouros_antes: list[Estouro]
    estouros_depois: list[Estouro]
    quadro_depois: dict
    ajustes: list[Acao]
    stats: dict
    janela: tuple
    grupos_antes: OrderedDict
    grupos_depois: OrderedDict
    credito_antes: float
    credito_depois: float
    avisos: list[str] = field(default_factory=list)

    def acoes_de(self, *tipos):
        return [a for a in self.acoes if a.tipo in tipos]


def _bate(p: Posicao, nomes) -> bool:
    n = sem_acento(p.nome)
    return any(sem_acento(x) in n for x in (nomes or []))


def _eh_credito(p: Posicao, destino: str) -> bool:
    if p.categoria == "credito_privado":
        return True
    if p.tipo != "fundo" or p.cnpj == destino:
        return False
    n = sem_acento(p.nome + " " + (p.nome_cvm or ""))
    return p.tipo_fundo in ("fidc", "fiagro") or " cp" in n or "credito" in n or "debentures" in n


def _agrupar(posicoes: list[Posicao]) -> OrderedDict:
    g = OrderedDict((k, 0.0) for k in GRUPOS)
    for p in posicoes:
        g[p.grupo] = g.get(p.grupo, 0.0) + p.posicao
    return g


def planejar(cart: Carteira, regras: dict, opcoes: dict | None = None) -> Plano:
    opcoes = opcoes or {}
    comp = regras["compliance"]
    destino = norm_cnpj(regras["destino_padrao"]["cnpj"])
    destino_nome = regras["destino_padrao"]["nome"]
    subst = {norm_cnpj(f["cnpj"]): f for f in regras.get("fundos_substituir", [])}
    manter_forcado = opcoes.get("manter", [])
    vender_forcado = opcoes.get("vender", [])
    acao_estouro = opcoes.get("acao_estouro", comp.get("acao_estouro", "sugerir_ajuste"))

    acoes: list[Acao] = []
    avisos = [a for p in cart.posicoes for a in p.avisos]
    for p in cart.posicoes:
        if p.categoria == "ignorado":
            continue
        if _bate(p, manter_forcado):
            if p.categoria == "credito_privado" and p.status in ("sem_liquidez", "monitorar"):
                acoes.append(Acao(p, "acompanhar" if p.status == "sem_liquidez" else "monitorar", p.posicao, p.nota or "", 2))
            continue
        if _bate(p, vender_forcado):
            acoes.append(Acao(p, "resgatar" if p.tipo == "fundo" else "vender", p.liquido, "Decisão do assessor.", 1))
            continue
        if p.tipo == "fundo" and p.cnpj in subst:
            motivo = subst[p.cnpj].get("motivo", "")
            if p.fechado:
                acoes.append(Acao(p, "sair_quando_liberar", p.liquido, motivo, 2))
            else:
                acoes.append(Acao(p, "resgatar", p.liquido, motivo, 1))
        elif p.categoria == "credito_privado":
            if p.status == "vender":
                acoes.append(Acao(p, "vender", p.liquido, p.nota or "", 1))
            elif p.status == "sem_liquidez":
                acoes.append(Acao(p, "acompanhar", p.posicao, p.nota or "", 2))
            elif p.status == "monitorar":
                acoes.append(Acao(p, "monitorar", p.posicao, p.nota or "", 2))

    # ---- carteira depois da etapa 1
    saindo = {id(a.posicao): a for a in acoes if a.tipo in ("resgatar", "vender")}
    depois: list[Posicao] = []
    destino_pos = None
    for p in cart.posicoes:
        if id(p) in saindo:
            continue
        q = copy.copy(p)
        depois.append(q)
        if q.cnpj == destino:
            destino_pos = q
    entrada = sum(a.valor for a in saindo.values())
    if destino_pos is None:
        destino_pos = Posicao(nome=destino_nome, posicao=0.0, liquido=0.0, tipo="fundo", cnpj=destino,
                              categoria="fundo_aberto", grupo="Fundo de destino (DI)", tipo_fundo="renda_fixa")
        depois.append(destino_pos)
    destino_pos.posicao += entrada
    destino_pos.liquido += entrada
    ir = sum(a.posicao.posicao - a.valor for a in saindo.values())
    total_antes = cart.total
    total_depois = total_antes - ir
    outros_nao_det = max(0.0, (cart.patrimonio_informado or 0) - sum(p.posicao for p in cart.posicoes))

    estouros_antes, _ = verificar(cart.posicoes, total_antes, regras)

    # ---- ajustes de enquadramento
    ajustes: list[Acao] = []
    if acao_estouro == "sugerir_ajuste":
        for _ in range(10):
            estouros, _ = verificar(depois, total_depois, regras)
            alvo = [e for e in estouros if e.regra in ("emissor", "nicho")]
            if not alvo:
                break
            e = alvo[0]
            vendaveis = [p for p in e.posicoes if p.categoria == "credito_privado" and p.status not in ("sem_liquidez",)
                         and not _bate(p, manter_forcado)]
            ordem = {"vender": 0, "sem_classificacao": 1, "monitorar": 2, "manter": 3}
            vendaveis.sort(key=lambda p: (ordem.get(p.status, 4), -p.posicao))
            falta = e.excesso
            if not vendaveis or falta <= 0.5:
                break
            for p in vendaveis:
                if falta <= 0.5:
                    break
                v = min(p.posicao, falta)
                p.posicao -= v
                p.liquido = max(0.0, p.liquido - v)
                destino_pos.posicao += v
                destino_pos.liquido += v
                original = next(o for o in cart.posicoes if o.nome == p.nome)
                pct_txt = f"{e.pct*100:.1f}".replace(".", ",")
                motivo = f"{e.rotulo} {e.chave} em {pct_txt}% do patrimônio, acima do limite de {e.limite*100:.0f}%."
                ajustes.append(Acao(original, "vender_parcial", v, motivo, 1))
                falta -= v
        depois = [p for p in depois if p.posicao > 0.5]

    estouros_depois, quadro_depois = verificar(depois, total_depois, regras)
    acoes.extend(ajustes)

    # ---- métricas dos fundos (12 meses fechados)
    ref = cart.data_posicao or dt.date.today()
    ini, fim = metricas.janela_12m(ref)
    cnpjs = {p.cnpj for p in cart.posicoes if p.tipo == "fundo" and p.cnpj} | {destino}
    series = dados.cotas(cnpjs, ini - dt.timedelta(days=10), fim)
    stats = {c: metricas.estatisticas(s, ini, fim) for c, s in series.items()}
    stats["_cdi"] = dados.cdi_acumulado(min((s["ini"] for s in stats.values() if s), default=ini),
                                        max((s["fim"] for s in stats.values() if s), default=fim))

    valor_destino_agora = destino_pos.posicao - next((p.posicao for p in cart.posicoes if p.cnpj == destino), 0.0)
    valor_destino_total = valor_destino_agora + sum(a.valor for a in acoes if a.tipo == "sair_quando_liberar")

    ga, gd = _agrupar(cart.posicoes), _agrupar(depois)
    ga["Outros"] += outros_nao_det
    gd["Outros"] += outros_nao_det
    cred_a = sum(p.posicao for p in cart.posicoes if _eh_credito(p, destino))
    cred_d = sum(p.posicao for p in depois if _eh_credito(p, destino))

    return Plano(cart, regras, acoes, depois, total_antes, total_depois, ir, destino_nome, destino,
                 valor_destino_agora, valor_destino_total, estouros_antes, estouros_depois, quadro_depois,
                 ajustes, stats, (ini, fim), ga, gd, cred_a, cred_d, avisos)
