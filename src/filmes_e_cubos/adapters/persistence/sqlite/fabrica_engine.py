"""Fábrica do engine SQLAlchemy: o arquivo SQLite local ou um banco por URL."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, create_engine

from filmes_e_cubos.adapters.persistence.sqlite.migracao import migrar

_DRIVER_DO_POSTGRES = "postgresql+psycopg"


def criar_engine(caminho_banco: str | Path) -> Engine:
    """Cria o engine apontando para o arquivo SQLite e leva o esquema à versão atual.

    Um arquivo novo ganha todas as tabelas; um banco existente recebe só as
    migrações que ainda não tinha (ver `migracao.py`).
    """
    engine = create_engine(f"sqlite:///{caminho_banco}")
    migrar(engine)
    return engine


def criar_engine_da_url(url: str) -> Engine:
    """Cria o engine para um banco dado por URL — em produção, o Postgres da Neon.

    Os provedores entregam a URL como `postgres://` ou `postgresql://`; o
    SQLAlchemy precisa saber o driver, então ela é reescrita para o
    `psycopg`. As conexões ficam num pool e são testadas antes do uso
    (`pool_pre_ping`): numa função da Vercel, a instância pode passar um
    tempo congelada, e o servidor fecha as conexões paradas.
    """
    url = normalizar_url_do_banco(url)
    opcoes = {} if url.startswith("sqlite") else {"pool_pre_ping": True, "pool_recycle": 300}
    engine = create_engine(url, **opcoes)
    migrar(engine)
    return engine


def normalizar_url_do_banco(url: str) -> str:
    """`postgres://...` e `postgresql://...` viram `postgresql+psycopg://...`."""
    for prefixo in ("postgres://", "postgresql://"):
        if url.startswith(prefixo):
            return f"{_DRIVER_DO_POSTGRES}://{url.removeprefix(prefixo)}"
    return url
