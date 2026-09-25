"""Utilitário interno de insert-or-update, compartilhado pelos repositórios SQLite."""

from typing import Any

from sqlalchemy import Connection, Engine, Table
from sqlalchemy.dialects.sqlite import insert as sqlite_insert


def upsert(engine: Engine, tabela: Table, linha: dict[str, Any]) -> None:
    """Insere `linha` em `tabela`, ou atualiza a linha existente com o mesmo `id`."""
    with engine.begin() as conexao:
        upsert_na_conexao(conexao, tabela, linha)


def upsert_na_conexao(conexao: Connection, tabela: Table, linha: dict[str, Any]) -> None:
    """Como `upsert`, dentro de uma transação já aberta — para gravar a entidade
    e as suas tabelas filhas de uma vez só.
    """
    instrucao = sqlite_insert(tabela).values(**linha)
    instrucao = instrucao.on_conflict_do_update(index_elements=["id"], set_=linha)
    conexao.execute(instrucao)
