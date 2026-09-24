"""Ambiente do Alembic para as migrações do banco SQLite do Filmes e Cubos.

Roda de dois jeitos:

- **pelo programa** (`migracao.migrar`), que entrega a conexão pronta em
  `config.attributes["connection"]` — assim a migração acontece dentro da
  mesma transação em que o programa abriu o banco;
- **pela linha de comando do Alembic**, no desenvolvimento (ex.:
  `uv run alembic revision --autogenerate -m "..."`), com o banco vindo de
  `sqlalchemy.url` ou da variável de ambiente `FILMES_E_CUBOS_DB`.

`render_as_batch=True` é o que permite alterar tabelas no SQLite, cujo
`ALTER TABLE` é limitado: o Alembic recria a tabela quando precisa.
"""

from __future__ import annotations

import os

from alembic import context
from sqlalchemy import Connection, create_engine

from filmes_e_cubos.adapters.persistence.sqlite.esquema import metadata

_BANCO_PADRAO = "filmes_e_cubos.db"


def _url_do_banco() -> str:
    url = context.config.get_main_option("sqlalchemy.url")
    if url:
        return url
    return f"sqlite:///{os.environ.get('FILMES_E_CUBOS_DB', _BANCO_PADRAO)}"


def _configurar(**opcoes: object) -> None:
    context.configure(
        target_metadata=metadata,
        render_as_batch=True,
        compare_type=True,
        **opcoes,  # type: ignore[arg-type]
    )


def _migrar_com(conexao: Connection) -> None:
    _configurar(connection=conexao)
    with context.begin_transaction():
        context.run_migrations()


def _migrar_offline() -> None:
    """Gera o SQL das migrações sem conectar ao banco (`alembic upgrade --sql`)."""
    _configurar(url=_url_do_banco(), literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def _migrar_online() -> None:
    conexao_do_programa = context.config.attributes.get("connection")
    if conexao_do_programa is not None:
        _migrar_com(conexao_do_programa)
        return
    with create_engine(_url_do_banco()).begin() as conexao:
        _migrar_com(conexao)


if context.is_offline_mode():
    _migrar_offline()
else:
    _migrar_online()
