"""Fixtures compartilhadas pela suíte de testes."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Final
from uuid import uuid4

import pytest
from sqlalchemy import Engine, create_engine, make_url, text

from filmes_e_cubos.adapters.persistence.sqlite.fabrica_engine import (
    criar_engine,
    criar_engine_da_url,
    normalizar_url_do_banco,
)
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.value_objects.configuracao_clube import ConfiguracaoClube

VARIAVEL_DO_POSTGRES_DE_TESTE: Final = "FILMES_E_CUBOS_TESTE_POSTGRES"
"""URL de um servidor Postgres em que a suíte pode criar e apagar bancos."""


@pytest.fixture
def configuracao_padrao() -> ConfiguracaoClube:
    return ConfiguracaoClube.padrao()


@pytest.fixture
def clube(configuracao_padrao: ConfiguracaoClube) -> Clube:
    return Clube.criar(nome="Filmes e Cubos", configuracao=configuracao_padrao)


@pytest.fixture
def engine_de_teste(tmp_path: Path) -> Iterator[Engine]:
    """O banco de um teste: um SQLite novo em `tmp_path`, por padrão.

    Com `FILMES_E_CUBOS_TESTE_POSTGRES` apontando um servidor Postgres, é um
    banco Postgres novo nele, apagado no fim do teste — é assim que os
    testes de repositório e os da API conferem também o banco da produção
    (a Neon, na Vercel). Os dois caminhos passam pelas migrações.
    """
    url_do_servidor = os.environ.get(VARIAVEL_DO_POSTGRES_DE_TESTE)
    if not url_do_servidor:
        yield criar_engine(tmp_path / "filmes_e_cubos_teste.db")
        return
    nome = f"teste_{uuid4().hex}"
    servidor = create_engine(normalizar_url_do_banco(url_do_servidor), isolation_level="AUTOCOMMIT")
    with servidor.connect() as conexao:
        conexao.execute(text(f'CREATE DATABASE "{nome}"'))
    url_do_banco = make_url(normalizar_url_do_banco(url_do_servidor)).set(database=nome)
    engine = criar_engine_da_url(url_do_banco.render_as_string(hide_password=False))
    try:
        yield engine
    finally:
        engine.dispose()
        with servidor.connect() as conexao:
            conexao.execute(text(f'DROP DATABASE "{nome}" WITH (FORCE)'))
        servidor.dispose()
