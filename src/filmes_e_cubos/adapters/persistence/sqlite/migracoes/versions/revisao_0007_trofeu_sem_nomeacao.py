"""Troféu sem nomeação vencedora, para o empate absoluto.

Revisão: 0007
Anterior: 0006
Criada em: 2026-10-13

Num empate absoluto nenhuma nomeação vence, e o troféu vai para um
membro escolhido pelo grupo (decisões 8.6 e 29 de docs/PENDENCIAS.md).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | Sequence[str] | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("trofeus") as tabela:
        tabela.alter_column("nomeacao_vencedora_id", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("trofeus") as tabela:
        tabela.alter_column("nomeacao_vencedora_id", existing_type=sa.String(), nullable=False)
