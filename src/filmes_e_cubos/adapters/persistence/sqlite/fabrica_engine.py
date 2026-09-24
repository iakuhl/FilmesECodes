"""Fábrica do engine SQLAlchemy para o banco SQLite."""

from pathlib import Path

from sqlalchemy import Engine, create_engine

from filmes_e_cubos.adapters.persistence.sqlite.migracao import migrar


def criar_engine(caminho_banco: str | Path) -> Engine:
    """Cria o engine apontando para `caminho_banco` e leva o esquema à versão atual.

    Um arquivo novo ganha todas as tabelas; um banco existente recebe só as
    migrações que ainda não tinha (ver `migracao.py`).
    """
    engine = create_engine(f"sqlite:///{caminho_banco}")
    migrar(engine)
    return engine
