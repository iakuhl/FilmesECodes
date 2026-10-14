"""Fixtures compartilhadas pelos testes de integração da persistência."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import Engine

from filmes_e_cubos.adapters.persistence.sqlite.fabrica_engine import criar_engine


@pytest.fixture
def engine(tmp_path: Path) -> Engine:
    """Um SQLite real, em arquivo temporário.

    Estes testes gravam entidades sem as "mães" (o SQLite do projeto não
    confere chaves estrangeiras — dívida técnica 1), então ficam no SQLite;
    o Postgres da produção é conferido pelos testes da API, que montam o
    cenário pela própria interface (ver tests/conftest.py).
    """
    return criar_engine(tmp_path / "filmes_e_cubos_teste.db")
