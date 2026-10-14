"""Testes da fábrica do engine: arquivo SQLite local ou banco por URL."""

from __future__ import annotations

from pathlib import Path

import pytest

from filmes_e_cubos.adapters.persistence.sqlite.clube_repository_sqlite import (
    ClubeRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.fabrica_engine import (
    criar_engine_da_url,
    normalizar_url_do_banco,
)
from filmes_e_cubos.domain.entities.clube import Clube


@pytest.mark.parametrize(
    ("url", "esperada"),
    [
        ("postgres://u:s@neon.tech/banco", "postgresql+psycopg://u:s@neon.tech/banco"),
        (
            "postgresql://u:s@neon.tech/banco?sslmode=require",
            "postgresql+psycopg://u:s@neon.tech/banco?sslmode=require",
        ),
        ("postgresql+psycopg://u@h/b", "postgresql+psycopg://u@h/b"),
        ("sqlite:///clube.db", "sqlite:///clube.db"),
    ],
)
def test_url_do_provedor_ganha_o_driver_psycopg(url: str, esperada: str) -> None:
    assert normalizar_url_do_banco(url) == esperada


def test_url_de_sqlite_tambem_serve(tmp_path: Path) -> None:
    engine = criar_engine_da_url(f"sqlite:///{tmp_path / 'por_url.db'}")
    ClubeRepositorioSqlite(engine).salvar(Clube.criar(nome="Filmes e Cubos"))

    assert [clube.nome for clube in ClubeRepositorioSqlite(engine).listar_todos()] == [
        "Filmes e Cubos"
    ]
