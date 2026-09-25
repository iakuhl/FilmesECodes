"""Média das notas de cada sessão, guardada como fração (soma e quantidade).

Revisão: 0003
Anterior: 0002
Criada em: 2026-09-24

A média passa a ser gravada na sessão a cada avaliação (decisões 9 e 19
de docs/PENDENCIAS.md). Para que as sessões já avaliadas não fiquem sem
ela, a migração calcula a soma e a quantidade das notas existentes —
dorminhocos (nota nula) não entram. A soma é feita com `Decimal`, como
no domínio, porque as notas são guardadas como texto exato.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("sessoes_exibicao") as tabela:
        tabela.add_column(
            sa.Column("soma_das_notas", sa.String(), server_default="0", nullable=False)
        )
        tabela.add_column(
            sa.Column("quantidade_de_notas", sa.Integer(), server_default="0", nullable=False)
        )

    conexao = op.get_bind()
    notas_por_sessao: dict[str, list[Decimal]] = {}
    for sessao_id, nota in conexao.execute(
        sa.text("SELECT sessao_id, nota FROM avaliacoes WHERE nota IS NOT NULL")
    ):
        notas_por_sessao.setdefault(sessao_id, []).append(Decimal(nota))
    for sessao_id, notas in notas_por_sessao.items():
        conexao.execute(
            sa.text(
                "UPDATE sessoes_exibicao SET soma_das_notas = :soma, "
                "quantidade_de_notas = :quantidade WHERE id = :id"
            ),
            {"soma": str(sum(notas, Decimal(0))), "quantidade": len(notas), "id": sessao_id},
        )


def downgrade() -> None:
    with op.batch_alter_table("sessoes_exibicao") as tabela:
        tabela.drop_column("quantidade_de_notas")
        tabela.drop_column("soma_das_notas")
