"""Fábrica do engine SQLAlchemy para o banco SQLite."""

from pathlib import Path

from sqlalchemy import Engine, create_engine

from filmes_e_cubos.adapters.persistence.sqlite.esquema import metadata


def criar_engine(caminho_banco: str | Path) -> Engine:
    """Cria o engine apontando para `caminho_banco` e garante que as tabelas existam."""
    engine = create_engine(f"sqlite:///{caminho_banco}")
    metadata.create_all(engine)
    return engine
