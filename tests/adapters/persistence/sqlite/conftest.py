"""Fixtures compartilhadas pelos testes de integração da persistência SQLite."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import Engine

from filmes_e_cubos.adapters.persistence.sqlite.fabrica_engine import criar_engine


@pytest.fixture
def engine(tmp_path: Path) -> Engine:
    return criar_engine(tmp_path / "filmes_e_cubos_teste.db")
