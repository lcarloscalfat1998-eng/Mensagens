"""Linha de comando do motor.

  python -m motor readequacao   entrada.yaml [--saida pasta] [--sem-pdf]
  python -m motor enquadramento entrada.yaml
  python -m motor comparativo   entrada.yaml [--saida pasta] [--sem-pdf]
  python -m motor proposta      entrada.yaml [--saida pasta] [--sem-pdf]
  python -m motor fundo         "nome ou CNPJ"
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

import yaml

from . import carteira as mcart
from . import dados, render
from .dados import sem_acento

RAIZ = Path(__file__).resolve().parent.parent


def _saida(args, entrada: Path, tipo: str) -> Path:
    if args.saida:
        return Path(args.saida)
    slug = re.sub(r"[^a-z0-9]+", "-", sem_acento(entrada.stem)).strip("-")
    return RAIZ / "saidas" / f"{dt.date.today():%Y-%m-%d}-{tipo}-{slug}"


def _publicar(pasta: Path, nome: str, template: str, ctx: dict, texto: str, sem_pdf: bool):
    html = render.gerar_html(template, ctx, pasta / f"{nome}.html")
    (pasta / "mensagem.txt").write_text(texto, encoding="utf-8")
    print(f"HTML: {html}")
    if not sem_pdf:
        pdf = render.gerar_pdf(html, pasta / f"{nome}.pdf")
        print(f"PDF:  {pdf}")
    print(f"Mensagem: {pasta / 'mensagem.txt'}")


def cmd_readequacao(args):
    from . import doc_readequacao, readequacao
    regras = mcart.carregar_regras(args.regras)
    entrada = Path(args.entrada)
    bruto = yaml.safe_load(entrada.read_text(encoding="utf-8"))
    cart = mcart.carregar(entrada, regras)
    plano = readequacao.planejar(cart, regras, bruto.get("opcoes"))
    for a in plano.avisos:
        print("AVISO:", a)
    ctx = doc_readequacao.contexto(plano, bruto)
    _publicar(_saida(args, entrada, "readequacao"), "Readequacao da Carteira", "readequacao.html.j2", ctx,
              doc_readequacao.mensagem(ctx), args.sem_pdf)


def cmd_enquadramento(args):
    from .enquadramento import verificar
    regras = mcart.carregar_regras(args.regras)
    cart = mcart.carregar(args.entrada, regras)
    for p in cart.posicoes:
        for a in p.avisos:
            print("AVISO:", a)
    estouros, quadro = verificar(cart.posicoes, cart.total, regras)
    print(f"Patrimônio: {render.brl(cart.total, True)}")
    for regra, linhas in quadro.items():
        print(f"\n{regra.upper()}")
        for e in linhas:
            marca = "ESTOURO" if e in estouros else "ok"
            print(f"  {e.chave:40} {render.brl(e.valor):>14} {render.pct(e.pct):>8}  limite {render.pct(e.limite,0)}  {marca}"
                  + (f"  excesso {render.brl(e.excesso)}" if e in estouros else ""))
    sys.exit(1 if estouros else 0)


def cmd_comparativo(args):
    from . import comparativo
    entrada = Path(args.entrada)
    cfg = yaml.safe_load(entrada.read_text(encoding="utf-8"))
    ctx = comparativo.contexto(cfg)
    _publicar(_saida(args, entrada, "comparativo"), "Estudo Comparativo", "comparativo.html.j2", ctx,
              comparativo.mensagem(ctx), args.sem_pdf)


def cmd_proposta(args):
    from . import proposta
    entrada = Path(args.entrada)
    cfg = yaml.safe_load(entrada.read_text(encoding="utf-8"))
    ctx = proposta.contexto(cfg)
    _publicar(_saida(args, entrada, "proposta"), "Proposta de Carteira", "proposta.html.j2", ctx,
              proposta.mensagem(ctx), args.sem_pdf)


def cmd_fundo(args):
    from . import metricas
    alvo = dados.norm_cnpj(args.entrada)
    cands = [{"cnpj": alvo}] if alvo else dados.buscar_fundo(args.entrada, 10)
    ini, fim = metricas.janela_12m()
    for c in cands:
        info = dados.info_fundo(c["cnpj"]) or {}
        s = dados.cotas([c["cnpj"]], ini - dt.timedelta(days=10), fim).get(c["cnpj"])
        st = metricas.estatisticas(s, ini, fim) if s is not None else None
        print(f"{c['cnpj']}  {info.get('nome', c.get('nome'))}")
        print(f"   {info.get('condominio')} · {info.get('classificacao')} · PL {render.brl(info.get('pl'))}")
        if st:
            print(f"   12m: {render.pct(st['retorno'])} ({render.pct(st['pct_cdi'],1)} do CDI) · vol {render.pct(st['vol'])} · maior queda {render.pct(st['mdd'])}")


def main():
    ap = argparse.ArgumentParser(prog="motor", description="Motor de estudo e readequação de carteiras")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nome, fn in (("readequacao", cmd_readequacao), ("enquadramento", cmd_enquadramento),
                     ("comparativo", cmd_comparativo), ("proposta", cmd_proposta), ("fundo", cmd_fundo)):
        s = sub.add_parser(nome)
        s.add_argument("entrada")
        s.add_argument("--saida")
        s.add_argument("--regras")
        s.add_argument("--sem-pdf", action="store_true")
        s.set_defaults(fn=fn)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
