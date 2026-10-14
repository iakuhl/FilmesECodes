"""Utilitários internos de gravação, compartilhados pelos repositórios.

Os repositórios gravam com "insere ou atualiza" (upsert). O SQL disso
não é padrão: SQLite e Postgres têm cada um o seu `INSERT ... ON CONFLICT`,
com a mesma forma no SQLAlchemy, então o dialeto da conexão escolhe qual
usar.
"""

from typing import Any

from sqlalchemy import Connection, Engine, Table, func, select
from sqlalchemy.dialects import postgresql, sqlite


def upsert(engine: Engine, tabela: Table, linha: dict[str, Any]) -> None:
    """Insere `linha` em `tabela`, ou atualiza a linha existente com o mesmo `id`."""
    with engine.begin() as conexao:
        upsert_na_conexao(conexao, tabela, linha)


def upsert_na_conexao(conexao: Connection, tabela: Table, linha: dict[str, Any]) -> None:
    """Como `upsert`, dentro de uma transação já aberta — para gravar a entidade
    e as suas tabelas filhas de uma vez só.
    """
    insercao = _insert_do_dialeto(conexao, tabela).values(**linha)
    conexao.execute(insercao.on_conflict_do_update(index_elements=["id"], set_=linha))


def upsert_mantendo_a_ordem(engine: Engine, tabela: Table, linha: dict[str, Any]) -> None:
    """Upsert para tabelas que guardam a ordem em que as linhas foram criadas.

    Linha nova ganha `ordem` = maior ordem da tabela + 1; linha existente é
    atualizada sem mexer na ordem. É o que dá às listagens a ordem de
    criação em qualquer banco — o SQLite devolve as linhas na ordem em que
    entraram, mas o Postgres não garante ordem nenhuma sem `ORDER BY`.
    """
    with engine.begin() as conexao:
        existe = conexao.execute(select(tabela.c.id).where(tabela.c.id == linha["id"])).first()
        if existe is not None:
            conexao.execute(tabela.update().where(tabela.c.id == linha["id"]).values(**linha))
            return
        proxima = conexao.execute(
            select(func.coalesce(func.max(tabela.c.ordem), 0) + 1)
        ).scalar_one()
        conexao.execute(tabela.insert().values(**linha, ordem=proxima))


def _insert_do_dialeto(conexao: Connection, tabela: Table) -> postgresql.Insert | sqlite.Insert:
    if conexao.dialect.name == "postgresql":
        return postgresql.insert(tabela)
    return sqlite.insert(tabela)
