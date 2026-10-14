"""Testes que só fazem sentido no Postgres da produção.

Rodam quando `FILMES_E_CUBOS_TESTE_POSTGRES` aponta um servidor Postgres
(a CI sobe um); nessa mesma situação, os testes de repositório e os da
API também rodam contra o Postgres, pela fixture `engine_de_teste`.
"""

from __future__ import annotations

import os

import pytest
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from sqlalchemy import Engine

from filmes_e_cubos.adapters.persistence.sqlite.esquema import metadata
from filmes_e_cubos.adapters.persistence.sqlite.migracao import migrar
from tests.conftest import VARIAVEL_DO_POSTGRES_DE_TESTE

pytestmark = pytest.mark.skipif(
    not os.environ.get(VARIAVEL_DO_POSTGRES_DE_TESTE),
    reason=f"defina {VARIAVEL_DO_POSTGRES_DE_TESTE} para testar o Postgres",
)


def test_migracoes_no_postgres_produzem_exatamente_o_esquema_declarado(
    engine_de_teste: Engine,
) -> None:
    assert engine_de_teste.dialect.name == "postgresql"
    with engine_de_teste.connect() as conexao:
        assert compare_metadata(MigrationContext.configure(conexao), metadata) == []


def test_migrar_de_novo_no_postgres_nao_muda_nada(engine_de_teste: Engine) -> None:
    with engine_de_teste.connect() as conexao:
        antes = MigrationContext.configure(conexao).get_current_revision()

    migrar(engine_de_teste)

    with engine_de_teste.connect() as conexao:
        assert MigrationContext.configure(conexao).get_current_revision() == antes
