"""Utilitário interno de insert-or-update, compartilhado pelos repositórios SQLite."""

from typing import Any

from sqlalchemy import Engine, Table
from sqlalchemy.dialects.sqlite import insert as sqlite_insert


def upsert(engine: Engine, tabela: Table, linha: dict[str, Any]) -> None:
    """Insere `linha` em `tabela`, ou atualiza a linha existente com o mesmo `id`."""
    instrucao = sqlite_insert(tabela).values(**linha)
    instrucao = instrucao.on_conflict_do_update(index_elements=["id"], set_=linha)
    with engine.begin() as conexao:
        conexao.execute(instrucao)
