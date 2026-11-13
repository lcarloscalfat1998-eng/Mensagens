"""Carteira do cliente: leitura da entrada e classificação de cada posição."""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import dados
from .dados import norm_cnpj, sem_acento

RAIZ = Path(__file__).resolve().parent.parent

GRUPOS = [
    "Títulos públicos",
    "Bancários e quase soberanos",
    "Fundo de destino (DI)",
    "Crédito privado",
    "Crédito privado em alerta",
    "Fundos de renda fixa e crédito",
    "Fundos fechados (FIDC, FIP, Fiagro, FII)",
    "Multimercados",
    "Fundos de ações",
    "Internacional",
    "Cripto",
    "Renda variável Brasil",
    "Outros",
]

RE_PUBLICO = re.compile(r"^(ntn|ltn|lft|tesouro)")
RE_BANCARIO = re.compile(r"^(lca|lci|cdb|lc|lig|rdb)\b")
RE_LCD = re.compile(r"^lcd\b")
RE_CREDITO = re.compile(r"^(cra|cri|deb|debenture|cdca|cpr|ccb|nc|lf|lfsn|cce)\b")
RE_VENC = re.compile(r"\s*-\s*[a-z]{3}/\d{4}$")


def carregar_regras(caminho: str | Path | None = None) -> dict:
    caminho = Path(caminho) if caminho else RAIZ / "regras.yaml"
    return yaml.safe_load(Path(caminho).read_text(encoding="utf-8"))


@dataclass
class Posicao:
    nome: str
    posicao: float
    liquido: float
    tipo: str = "outros"              # titulo | fundo | renda_variavel | coe | outros
    aplicado: float | None = None
    taxa: str | None = None
    vencimento: str | None = None
    cnpj: str | None = None
    isento: bool | None = None
    # preenchidos pela classificação
    categoria: str = "outros"
    emissor: str | None = None
    setor: str | None = None
    status: str | None = None
    nota: str | None = None
    fechado: bool = False
    tipo_fundo: str | None = None
    nome_cvm: str | None = None
    grupo: str = "Outros"
    avisos: list = field(default_factory=list)

    @property
    def resultado(self) -> float | None:
        return self.posicao / self.aplicado - 1 if self.aplicado else None


@dataclass
class Carteira:
    posicoes: list[Posicao]
    data_posicao: dt.date | None = None
    patrimonio_informado: float | None = None
    titulo: str | None = None

    @property
    def total(self) -> float:
        soma = sum(p.posicao for p in self.posicoes)
        return max(soma, self.patrimonio_informado or 0)


def _emissor_regra(nome_norm: str, regras: dict) -> dict | None:
    for r in regras.get("emissores", []):
        if re.search(r["padrao"], nome_norm):
            return r
    return None


def _emissor_do_nome(nome: str) -> str:
    n = RE_VENC.sub("", nome.strip())
    partes = n.split(" ", 1)
    return partes[1].strip() if len(partes) > 1 else n


def _fundo_conhecido(nome_norm: str, regras: dict) -> dict | None:
    for r in regras.get("fundos_conhecidos", []):
        if sem_acento(r["padrao"]) in nome_norm:
            return r
    return None


def _tipo_fundo(nome_norm: str, info: dict | None) -> str:
    tc = sem_acento(str((info or {}).get("tipo_classe") or ""))
    if "fidc" in nome_norm or "direitos creditorios" in nome_norm or "fidc" in tc:
        return "fidc"
    if "fiagro" in nome_norm:
        return "fiagro"
    if re.search(r"\bfip\b", nome_norm) or "participacoes" in nome_norm or "fip" in tc:
        return "fip"
    if re.search(r"\bfii\b", nome_norm) or "imobiliario" in tc:
        return "fii"
    if any(k in nome_norm for k in ("bitcoin", "cripto", "hashdex", "ethereum")):
        return "cripto"
    if re.search(r"\bie\b", nome_norm) or "exterior" in nome_norm or "global" in nome_norm:
        return "internacional"
    cl = sem_acento(str((info or {}).get("classificacao") or ""))
    if "acoes" in cl or re.search(r"\bfia\b", nome_norm):
        return "acoes"
    if "multimercado" in cl or re.search(r"\b(fim|multimercado)\b", nome_norm):
        return "multimercado"
    return "renda_fixa"


def classificar(p: Posicao, regras: dict) -> Posicao:
    n = sem_acento(p.nome).strip()
    destino = norm_cnpj(regras.get("destino_padrao", {}).get("cnpj"))
    ignorar = set(regras.get("compliance", {}).get("ignorar", []))

    if p.tipo == "coe" or n.startswith("coe"):
        p.categoria, p.grupo = ("ignorado" if "coe" in ignorar else "outros"), "Outros"
        return p
    if p.tipo == "renda_variavel":
        p.categoria, p.grupo = "renda_variavel", "Renda variável Brasil"
        return p

    eh_titulo = p.tipo == "titulo" or (p.tipo == "outros" and (RE_PUBLICO.match(n) or RE_BANCARIO.match(n) or RE_LCD.match(n) or RE_CREDITO.match(n)))
    if eh_titulo:
        p.tipo = "titulo"
        regra = _emissor_regra(n, regras)
        if regra:
            p.emissor, p.setor, p.status, p.nota = regra["emissor"], regra.get("setor"), regra.get("status"), regra.get("nota")
        else:
            p.emissor = _emissor_do_nome(p.nome)
        if RE_PUBLICO.match(n):
            p.categoria, p.grupo, p.emissor, p.status = "titulo_publico", "Títulos públicos", "Tesouro Nacional", "soberano"
        elif p.status == "quase_soberano":
            p.categoria, p.grupo = "quase_soberano", "Bancários e quase soberanos"
        elif RE_BANCARIO.match(n):
            p.categoria, p.grupo = "bancario_fgc", "Bancários e quase soberanos"
            p.status = p.status or "bancario"
        else:
            p.categoria = "credito_privado"
            if not regra:
                p.status = "sem_classificacao"
                p.avisos.append(f"Emissor '{p.emissor}' não está em regras.yaml: defina setor e situação.")
            p.grupo = "Crédito privado" if p.status == "manter" else "Crédito privado em alerta"
        return p

    # fundos
    conhecido = _fundo_conhecido(n, regras)
    p.cnpj = norm_cnpj(p.cnpj) or norm_cnpj((conhecido or {}).get("cnpj"))
    info = dados.info_fundo(p.cnpj) if p.cnpj else None
    if p.tipo == "outros" and not (p.cnpj or conhecido):
        cands = dados.buscar_fundo(p.nome)
        if len(cands) == 1:
            p.cnpj = cands[0]["cnpj"]
            info = dados.info_fundo(p.cnpj)
            p.avisos.append(f"CNPJ encontrado pelo nome na CVM: {p.cnpj} ({cands[0]['nome']}). Confirme.")
        elif cands:
            p.avisos.append(f"Fundo '{p.nome}' com {len(cands)} possíveis CNPJs na CVM: informe o CNPJ.")
    if p.tipo == "outros" and not (p.cnpj or conhecido or info):
        p.avisos.append(f"Posição '{p.nome}' não identificada: classificada como Outros.")
        return p
    p.tipo = "fundo"
    if info:
        p.nome_cvm = info["nome"]
    p.fechado = bool((conhecido or {}).get("fechado", (info or {}).get("fechado", False)))
    p.tipo_fundo = (conhecido or {}).get("tipo_fundo") or _tipo_fundo(n, info)
    p.setor = (conhecido or {}).get("setor")
    if p.tipo_fundo == "fip" or (p.tipo_fundo in ("fidc", "fiagro", "fii") and info is None and conhecido is None):
        p.fechado = True  # FIP é sempre fechado; demais, quando não há cadastro
    if p.cnpj and p.cnpj == destino:
        p.categoria, p.grupo = "fundo_aberto", "Fundo de destino (DI)"
    elif p.fechado:
        p.categoria, p.grupo = "fundo_fechado", "Fundos fechados (FIDC, FIP, Fiagro, FII)"
    else:
        p.categoria = "fundo_aberto"
        p.grupo = {"renda_fixa": "Fundos de renda fixa e crédito", "multimercado": "Multimercados",
                   "acoes": "Fundos de ações", "internacional": "Internacional", "cripto": "Cripto"}.get(p.tipo_fundo, "Fundos de renda fixa e crédito")
    return p


def _num(v) -> float | None:
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace("R$", "").strip().replace(".", "").replace(",", ".")
    return float(s)


def carregar(caminho: str | Path, regras: dict | None = None) -> Carteira:
    """Lê a carteira de um arquivo YAML (ver exemplos/carteira_exemplo.yaml)."""
    regras = regras or carregar_regras()
    d = yaml.safe_load(Path(caminho).read_text(encoding="utf-8"))
    pos = []
    for item in d["posicoes"]:
        valor = _num(item.get("posicao", item.get("valor")))
        p = Posicao(
            nome=item["nome"], posicao=valor, liquido=_num(item.get("liquido")) or valor,
            tipo=item.get("tipo", "outros"), aplicado=_num(item.get("aplicado")),
            taxa=item.get("taxa"), vencimento=str(item["vencimento"]) if item.get("vencimento") else None,
            cnpj=item.get("cnpj"), isento=item.get("isento"),
        )
        pos.append(classificar(p, regras))
    data = d.get("data_posicao")
    if isinstance(data, str):
        data = dt.date.fromisoformat(data)
    return Carteira(posicoes=pos, data_posicao=data, patrimonio_informado=_num(d.get("patrimonio_total")),
                    titulo=d.get("titulo"))
