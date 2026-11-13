"""Métricas de fundos a partir das cotas da CVM e do CDI do Banco Central."""
from __future__ import annotations

import calendar
import datetime as dt
import math

import pandas as pd

from . import dados


def fim_mes(y: int, m: int) -> dt.date:
    return dt.date(y, m, calendar.monthrange(y, m)[1])


def janela_12m(ref: dt.date | None = None, meses: int = 12) -> tuple[dt.date, dt.date]:
    """Últimos N meses fechados: (fim do mês inicial, fim do último mês fechado)."""
    ref = ref or dt.date.today()
    y, m = ref.year, ref.month - 1
    if m == 0:
        y, m = y - 1, 12
    fim = fim_mes(y, m)
    y0, m0 = y, m - meses
    while m0 <= 0:
        y0, m0 = y0 - 1, m0 + 12
    return fim_mes(y0, m0), fim


def ultima_ate(serie: pd.Series, d: dt.date):
    s = serie[serie.index <= d]
    return s.index[-1] if len(s) else None


def estatisticas(serie: pd.Series, ini: dt.date, fim: dt.date) -> dict | None:
    """Retorno, % do CDI, volatilidade anualizada e maior queda entre ini e fim (datas de cota)."""
    d0, d1 = ultima_ate(serie, ini), ultima_ate(serie, fim)
    if d0 is None or d1 is None or d0 >= d1:
        return None
    s = serie[(serie.index >= d0) & (serie.index <= d1)]
    ret = s.iloc[-1] / s.iloc[0] - 1
    diarios = s.pct_change().dropna()
    vol = float(diarios.std(ddof=0) * math.sqrt(252)) if len(diarios) > 1 else 0.0
    pico, mdd = 0.0, 0.0
    for v in s.values:
        pico = max(pico, v)
        mdd = min(mdd, v / pico - 1)
    cdi = dados.cdi_acumulado(d0, d1)
    return {"ini": d0, "fim": d1, "retorno": float(ret), "cdi": cdi,
            "pct_cdi": float(ret / cdi) if cdi else None, "vol": vol, "mdd": float(mdd),
            "completo": d0 >= ini - dt.timedelta(days=7)}


def meses_entre(ini: dt.date, fim: dt.date) -> list[tuple[int, int]]:
    out, y, m = [], ini.year, ini.month
    while True:
        m += 1
        if m == 13:
            y, m = y + 1, 1
        if (y, m) > (fim.year, fim.month):
            return out
        out.append((y, m))


def retornos_mensais(serie: pd.Series, ini: dt.date, fim: dt.date) -> list[dict]:
    """Retorno mês a mês (cota do último dia útil de cada mês)."""
    out = []
    ant = ultima_ate(serie, ini)
    for y, m in meses_entre(ini, fim):
        d = ultima_ate(serie, fim_mes(y, m))
        if ant is None or d is None or d <= ant:
            out.append({"mes": (y, m), "retorno": None, "ini": ant, "fim": d})
        else:
            out.append({"mes": (y, m), "retorno": float(serie[d] / serie[ant] - 1), "ini": ant, "fim": d})
        ant = d
    return out


def cdi_mensal(ini: dt.date, fim: dt.date, ref: pd.Series | None = None) -> list[dict]:
    """CDI mês a mês, usando as mesmas datas de corte de uma série de referência (se dada)."""
    out = []
    for y, m in meses_entre(ini, fim):
        a = fim_mes(*((y, m - 1) if m > 1 else (y - 1, 12)))
        b = fim_mes(y, m)
        if ref is not None:
            a, b = ultima_ate(ref, a), ultima_ate(ref, b)
        else:
            cdi = dados.bcb_serie(dados.SERIE_CDI, a - dt.timedelta(days=10), b)
            a = cdi[cdi.index <= a].index[-1]
            b = cdi[cdi.index <= b].index[-1]
        out.append({"mes": (y, m), "retorno": dados.cdi_acumulado(a, b)})
    return out
