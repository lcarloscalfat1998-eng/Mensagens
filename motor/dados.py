"""Fontes oficiais: CVM (cotas e cadastro de fundos) e Banco Central (CDI, IPCA, Selic).

Tudo fica em cache local (pasta .cache na raiz do repositório, ou MOTOR_CACHE).
"""
from __future__ import annotations

import datetime as dt
import io
import json
import os
import shutil
import time
import unicodedata
import urllib.request
import zipfile
from functools import lru_cache
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
CACHE = Path(os.environ.get("MOTOR_CACHE", RAIZ / ".cache"))

CVM_DIARIO = "https://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/DADOS/inf_diario_fi_{ym}.zip"
CVM_CADASTRO = "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/registro_fundo_classe.zip"
BCB_SGS = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados?formato=json&dataInicial={ini}&dataFinal={fim}"

SERIE_CDI = 12      # CDI diário (% a.d.)
SERIE_IPCA = 433    # IPCA mensal (%)
SERIE_SELIC_META = 432


def _baixar(url: str, destino: Path, idade_max_h: float | None) -> Path:
    """Baixa url para destino, a menos que o arquivo já exista e seja recente."""
    if destino.exists() and (idade_max_h is None or time.time() - destino.stat().st_mtime < idade_max_h * 3600):
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_name(destino.name + ".tmp")
    req = urllib.request.Request(url, headers={"User-Agent": "motor-carteiras/1.0"})
    with urllib.request.urlopen(req, timeout=600) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f)
    tmp.replace(destino)
    return destino


def norm_cnpj(c: str | None) -> str | None:
    if not c:
        return None
    d = "".join(ch for ch in str(c) if ch.isdigit())
    if len(d) != 14:
        return None
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"


def sem_acento(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch)).lower()


# ---------------------------------------------------------------- CVM: cotas

def _ym_range(ini: dt.date, fim: dt.date):
    y, m = ini.year, ini.month
    while (y, m) <= (fim.year, fim.month):
        yield f"{y}{m:02d}"
        m += 1
        if m == 13:
            y, m = y + 1, 1


def _cotas_mes(ym: str) -> pd.DataFrame:
    """Cotas de todos os fundos num mês, em cache compacto (cnpj, data, cota, pl, cotistas)."""
    hoje = dt.date.today()
    recente = ym >= f"{(hoje.replace(day=1) - dt.timedelta(days=1)):%Y%m}"
    pk = CACHE / "cvm" / f"cotas_{ym}.pkl"
    zp = CACHE / "cvm" / f"inf_diario_fi_{ym}.zip"
    if pk.exists() and not (recente and time.time() - pk.stat().st_mtime > 12 * 3600):
        return pd.read_pickle(pk)
    _baixar(CVM_DIARIO.format(ym=ym), zp, 12 if recente else None)
    with zipfile.ZipFile(zp) as z:
        nome = z.namelist()[0]
        with z.open(nome) as f:
            df = pd.read_csv(f, sep=";", dtype=str, encoding="latin1")
    col_cnpj = "CNPJ_FUNDO_CLASSE" if "CNPJ_FUNDO_CLASSE" in df.columns else "CNPJ_FUNDO"
    if "ID_SUBCLASSE" in df.columns:
        # cota da classe (sem subclasse) tem prioridade
        df["_sub"] = df["ID_SUBCLASSE"].fillna("").str.len() > 0
        df = df.sort_values("_sub").drop_duplicates([col_cnpj, "DT_COMPTC"], keep="first")
    out = pd.DataFrame({
        "cnpj": df[col_cnpj],
        "data": pd.to_datetime(df["DT_COMPTC"]).dt.date,
        "cota": pd.to_numeric(df["VL_QUOTA"], errors="coerce"),
        "pl": pd.to_numeric(df["VL_PATRIM_LIQ"], errors="coerce"),
        "cotistas": pd.to_numeric(df["NR_COTST"], errors="coerce"),
    }).dropna(subset=["cota"])
    out.to_pickle(pk)
    zp.unlink(missing_ok=True)
    return out


def cotas(cnpjs, ini: dt.date, fim: dt.date) -> dict[str, pd.Series]:
    """Série de cotas diárias (index = data) para cada CNPJ, entre ini e fim."""
    alvo = {norm_cnpj(c) for c in cnpjs if norm_cnpj(c)}
    partes = []
    for ym in _ym_range(ini, fim):
        df = _cotas_mes(ym)
        partes.append(df[df["cnpj"].isin(alvo)])
    tudo = pd.concat(partes) if partes else pd.DataFrame(columns=["cnpj", "data", "cota"])
    tudo = tudo[(tudo["data"] >= ini) & (tudo["data"] <= fim)]
    return {c: g.set_index("data")["cota"].sort_index() for c, g in tudo.groupby("cnpj")}


# ---------------------------------------------------------------- CVM: cadastro

@lru_cache(maxsize=1)
def cadastro() -> pd.DataFrame:
    zp = _baixar(CVM_CADASTRO, CACHE / "cvm" / "registro_fundo_classe.zip", 24 * 7)
    with zipfile.ZipFile(zp) as z:
        with z.open("registro_classe.csv") as f:
            df = pd.read_csv(f, sep=";", dtype=str, encoding="latin1")
    df["cnpj"] = df["CNPJ_Classe"].map(norm_cnpj)
    df["nome_norm"] = df["Denominacao_Social"].fillna("").map(sem_acento)
    return df.set_index("cnpj", drop=False)


def info_fundo(cnpj: str) -> dict | None:
    c = norm_cnpj(cnpj)
    cad = cadastro()
    if c not in cad.index:
        return None
    r = cad.loc[c]
    if isinstance(r, pd.DataFrame):
        r = r.iloc[0]
    def num(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None
    return {
        "cnpj": c,
        "nome": r["Denominacao_Social"],
        "situacao": r["Situacao"],
        "condominio": r.get("Forma_Condominio"),
        "fechado": str(r.get("Forma_Condominio", "")).lower().startswith("fechado"),
        "classificacao": r.get("Classificacao"),
        "anbima": r.get("Classificacao_Anbima"),
        "tipo_classe": r.get("Tipo_Classe"),
        "pl": num(r.get("Patrimonio_Liquido")),
        "inicio": r.get("Data_Inicio"),
    }


def buscar_fundo(texto: str, limite: int = 5) -> list[dict]:
    """Procura fundos no cadastro da CVM por palavras do nome (ignora acentos)."""
    palavras = [p for p in sem_acento(texto).replace("-", " ").split() if len(p) > 1]
    cad = cadastro()
    ok = cad[cad["Situacao"].fillna("").str.contains("Funcionamento")]
    mask = pd.Series(True, index=ok.index)
    for p in palavras:
        mask &= ok["nome_norm"].str.contains(p, regex=False)
    res = ok[mask]
    return [{"cnpj": c, "nome": n} for c, n in zip(res["cnpj"], res["Denominacao_Social"])][:limite]


# ---------------------------------------------------------------- Banco Central

def bcb_serie(serie: int, ini: dt.date, fim: dt.date | None = None) -> pd.Series:
    """Série do SGS/BCB em % (valores como publicados), index = data."""
    fim = fim or dt.date.today()
    arq = CACHE / "bcb" / f"sgs_{serie}.json"
    dados = []
    if arq.exists() and time.time() - arq.stat().st_mtime < 12 * 3600:
        dados = json.loads(arq.read_text())
    primeira = dt.datetime.strptime(dados[0]["data"], "%d/%m/%Y").date() if dados else None
    if not dados or primeira > ini:
        ini_req = min(ini, dt.date(2019, 1, 1))
        url = BCB_SGS.format(serie=serie, ini=ini_req.strftime("%d/%m/%Y"), fim=dt.date.today().strftime("%d/%m/%Y"))
        req = urllib.request.Request(url, headers={"User-Agent": "motor-carteiras/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            dados = json.loads(r.read().decode())
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_text(json.dumps(dados))
    s = pd.Series({dt.datetime.strptime(d["data"], "%d/%m/%Y").date(): float(d["valor"]) for d in dados}).sort_index()
    return s[(s.index >= ini) & (s.index <= fim)]


def cdi_acumulado(d0: dt.date, d1: dt.date) -> float:
    """CDI acumulado entre duas datas de cota: taxas dos dias em [d0, d1)."""
    s = bcb_serie(SERIE_CDI, d0 - dt.timedelta(days=5), d1)
    s = s[(s.index >= d0) & (s.index < d1)]
    f = 1.0
    for v in s.values:
        f *= 1 + v / 100
    return f - 1


def cdi_anual_atual() -> float:
    s = bcb_serie(SERIE_CDI, dt.date.today() - dt.timedelta(days=20))
    return (1 + s.iloc[-1] / 100) ** 252 - 1


def selic_meta_atual() -> float:
    s = bcb_serie(SERIE_SELIC_META, dt.date.today() - dt.timedelta(days=60))
    return s.iloc[-1] / 100
