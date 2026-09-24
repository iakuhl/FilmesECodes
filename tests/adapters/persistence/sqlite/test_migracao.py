"""Testes das migrações de esquema (Alembic)."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from filmes_e_cubos.adapters.persistence.sqlite.clube_repository_sqlite import (
    ClubeRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.esquema import metadata
from filmes_e_cubos.adapters.persistence.sqlite.fabrica_engine import criar_engine
from filmes_e_cubos.adapters.persistence.sqlite.migracao import (
    REVISAO_INICIAL,
    configuracao_alembic,
)
from filmes_e_cubos.domain.entities.clube import Clube


def _revisao_mais_recente() -> str | None:
    return ScriptDirectory.from_config(configuracao_alembic()).get_current_head()


def test_banco_novo_chega_na_revisao_mais_recente(tmp_path: Path) -> None:
    engine = criar_engine(tmp_path / "novo.db")

    with engine.connect() as conexao:
        assert MigrationContext.configure(conexao).get_current_revision() == (
            _revisao_mais_recente()
        )


def test_migracoes_produzem_exatamente_o_esquema_declarado(tmp_path: Path) -> None:
    """Se `esquema.py` mudar sem uma revisão nova, este teste acusa a diferença."""
    engine = criar_engine(tmp_path / "comparado.db")

    with engine.connect() as conexao:
        diferencas = compare_metadata(MigrationContext.configure(conexao), metadata)

    assert diferencas == []


def test_banco_anterior_as_migracoes_e_reconhecido_sem_perder_dados(tmp_path: Path) -> None:
    caminho = tmp_path / "legado.db"
    # Simula um banco criado pelas Fases 2 e 3: o esquema da revisão inicial,
    # sem a tabela de controle do Alembic.
    legado = create_engine(f"sqlite:///{caminho}")
    configuracao = configuracao_alembic()
    with legado.begin() as conexao:
        configuracao.attributes["connection"] = conexao
        command.upgrade(configuracao, REVISAO_INICIAL)
        conexao.execute(text("DROP TABLE alembic_version"))
    ClubeRepositorioSqlite(legado).salvar(Clube.criar(nome="Filmes e Cubos"))

    engine = criar_engine(caminho)

    assert [clube.nome for clube in ClubeRepositorioSqlite(engine).listar_todos()] == [
        "Filmes e Cubos"
    ]
    with engine.connect() as conexao:
        assert MigrationContext.configure(conexao).get_current_revision() == (
            _revisao_mais_recente()
        )


def test_abrir_o_mesmo_banco_de_novo_nao_muda_nada(tmp_path: Path) -> None:
    caminho = tmp_path / "reaberto.db"
    ClubeRepositorioSqlite(criar_engine(caminho)).salvar(Clube.criar(nome="Filmes e Cubos"))

    assert len(ClubeRepositorioSqlite(criar_engine(caminho)).listar_todos()) == 1
