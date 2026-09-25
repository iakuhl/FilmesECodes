"""Número de nomeações por categoria de cada edição do Óscar.

Revisão: 0004
Anterior: 0003
Criada em: 2026-09-24

Toda categoria de uma edição tem o mesmo número de nomeações, escolhido
ao abrir a edição (decisão 17 de docs/PENDENCIAS.md). As edições que já
existem ficam com o padrão, 5.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("temporadas_oscar") as tabela:
        tabela.add_column(
            sa.Column("nomeacoes_por_categoria", sa.Integer(), server_default="5", nullable=False)
        )


def downgrade() -> None:
    with op.batch_alter_table("temporadas_oscar") as tabela:
        tabela.drop_column("nomeacoes_por_categoria")
