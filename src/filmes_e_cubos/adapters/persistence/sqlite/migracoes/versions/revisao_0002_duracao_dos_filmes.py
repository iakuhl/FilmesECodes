"""Duração dos filmes, em minutos.

Revisão: 0002
Anterior: 0001
Criada em: 2026-09-24

A coluna é anulável: os filmes já cadastrados não têm duração conhecida,
e ela continua opcional no cadastro (ver docs/PENDENCIAS.md, decisão 10).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("filmes") as tabela:
        tabela.add_column(sa.Column("duracao_minutos", sa.Integer(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("filmes") as tabela:
        tabela.drop_column("duracao_minutos")
