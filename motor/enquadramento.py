"""Verificação das regras de compliance (limites por emissor, nicho e fundo fechado)."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .carteira import Posicao


@dataclass
class Estouro:
    regra: str            # emissor | nicho | fundo_fechado
    chave: str            # nome do emissor, setor ou fundo
    valor: float
    base: float
    limite: float
    posicoes: list[Posicao] = field(default_factory=list)

    @property
    def pct(self) -> float:
        return self.valor / self.base

    @property
    def excesso(self) -> float:
        return max(0.0, self.valor - self.limite * self.base)

    @property
    def rotulo(self) -> str:
        return {"emissor": "Emissor", "nicho": "Nicho", "fundo_fechado": "Fundo fechado"}[self.regra]


def exposicoes(posicoes: list[Posicao], regras: dict) -> dict:
    """Valores que contam em cada limite, por emissor, nicho e fundo fechado."""
    c = regras["compliance"]
    exc = set(c.get("excecoes_emissor", []))
    fgc = c.get("fgc_por_instituicao", 250000)
    por_emissor, por_nicho, por_fundo = defaultdict(float), defaultdict(float), defaultdict(float)
    pos_emissor, pos_nicho, pos_fundo = defaultdict(list), defaultdict(list), defaultdict(list)

    bancario = defaultdict(float)
    for p in posicoes:
        if p.categoria == "bancario_fgc":
            bancario[p.emissor] += p.posicao
    for p in posicoes:
        if p.posicao <= 0:
            continue
        if p.categoria == "credito_privado" or (p.categoria not in exc and p.categoria in ("bancario_fgc", "quase_soberano")):
            por_emissor[p.emissor] += p.posicao
            pos_emissor[p.emissor].append(p)
        elif p.categoria == "bancario_fgc" and bancario[p.emissor] > fgc:
            # o que passa da cobertura do FGC conta como risco do banco
            parte = p.posicao * (bancario[p.emissor] - fgc) / bancario[p.emissor]
            por_emissor[p.emissor] += parte
            pos_emissor[p.emissor].append(p)
        if p.categoria in ("credito_privado", "fundo_fechado") and p.setor:
            por_nicho[p.setor] += p.posicao
            pos_nicho[p.setor].append(p)
        if p.categoria == "fundo_fechado":
            por_fundo[p.nome] += p.posicao
            pos_fundo[p.nome].append(p)
    return {"emissor": (por_emissor, pos_emissor), "nicho": (por_nicho, pos_nicho), "fundo_fechado": (por_fundo, pos_fundo)}


def verificar(posicoes: list[Posicao], base: float, regras: dict) -> tuple[list[Estouro], dict]:
    """Retorna os estouros e o quadro completo de exposições (para o documento)."""
    c = regras["compliance"]
    limites = {"emissor": c["limite_emissor"], "nicho": c["limite_nicho"], "fundo_fechado": c["limite_fundo_fechado"]}
    exp = exposicoes(posicoes, regras)
    estouros, quadro = [], {}
    for regra, (valores, pos) in exp.items():
        lim = limites[regra]
        linhas = []
        for chave, v in sorted(valores.items(), key=lambda kv: -kv[1]):
            e = Estouro(regra, chave, v, base, lim, pos[chave])
            linhas.append(e)
            if v > lim * base + 0.5:
                estouros.append(e)
        quadro[regra] = linhas
    return estouros, quadro
