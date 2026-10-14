"""Ordem de criação de indicações, avaliações, categorias e nomeações.

Revisão: 0006
Anterior: 0005
Criada em: 2026-10-13

Essas listagens mostram as linhas na ordem em que foram criadas — a das
nomeações, por exemplo, é a ordem da cédula. O SQLite devolve as linhas
nessa ordem por conta própria, mas o Postgres, usado em produção na
Vercel (decisão 34 de docs/PENDENCIAS.md), não garante ordem nenhuma sem
`ORDER BY`. A coluna `ordem` guarda a ordem de criação; nos bancos SQLite
que já existem, ela vem do `rowid`, que cresce a cada inserção.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | Sequence[str] | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABELAS = ("indicacoes", "avaliacoes", "categorias_oscar", "nomeacoes_oscar")


def upgrade() -> None:
    for tabela in _TABELAS:
        with op.batch_alter_table(tabela) as lote:
            lote.add_column(sa.Column("ordem", sa.Integer(), server_default="0", nullable=False))
    if op.get_bind().dialect.name == "sqlite":
        for tabela in _TABELAS:
            op.execute(f"UPDATE {tabela} SET ordem = rowid")


def downgrade() -> None:
    for tabela in _TABELAS:
        with op.batch_alter_table(tabela) as lote:
            lote.drop_column("ordem")
