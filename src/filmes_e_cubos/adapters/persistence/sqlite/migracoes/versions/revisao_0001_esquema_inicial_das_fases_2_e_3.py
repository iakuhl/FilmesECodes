"""Esquema inicial: as tabelas que as Fases 2 e 3 criavam com `metadata.create_all`.

Revisão: 0001
Anterior: nenhuma
Criada em: 2026-09-24

É a linha de base das migrações. Bancos criados antes de as migrações
existirem têm exatamente este esquema e são marcados como estando nesta
revisão (ver `sqlite/migracao.py`), sem que ela precise rodar neles.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "clubes",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("tamanho_rodada", sa.Integer(), nullable=False),
        sa.Column("nota_minima", sa.String(), nullable=False),
        sa.Column("nota_maxima", sa.String(), nullable=False),
        sa.Column("passo", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "filmes",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("titulo", sa.String(), nullable=False),
        sa.Column("ano_lancamento", sa.Integer(), nullable=True),
        sa.Column("diretor", sa.String(), nullable=True),
        sa.Column("identificador_externo", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "membros",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("clube_id", sa.String(), nullable=False),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("apelido", sa.String(), nullable=True),
        sa.Column("data_ingresso", sa.Date(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["clube_id"],
            ["clubes.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "rodadas",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("clube_id", sa.String(), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("data_inicio", sa.Date(), nullable=False),
        sa.Column("data_encerramento", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(
            ["clube_id"],
            ["clubes.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "temporadas_oscar",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("clube_id", sa.String(), nullable=False),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("data_evento", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(
            ["clube_id"],
            ["clubes.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "categorias_oscar",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("temporada_id", sa.String(), nullable=False),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("descricao", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["temporada_id"],
            ["temporadas_oscar.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "indicacoes",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("rodada_id", sa.String(), nullable=False),
        sa.Column("membro_id", sa.String(), nullable=True),
        sa.Column("filme_id", sa.String(), nullable=False),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("data_indicacao", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(
            ["filme_id"],
            ["filmes.id"],
        ),
        sa.ForeignKeyConstraint(
            ["membro_id"],
            ["membros.id"],
        ),
        sa.ForeignKeyConstraint(
            ["rodada_id"],
            ["rodadas.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "nomeacoes_oscar",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("categoria_id", sa.String(), nullable=False),
        sa.Column("filme_id", sa.String(), nullable=False),
        sa.Column("indicado_por_membro_id", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["categoria_id"],
            ["categorias_oscar.id"],
        ),
        sa.ForeignKeyConstraint(
            ["filme_id"],
            ["filmes.id"],
        ),
        sa.ForeignKeyConstraint(
            ["indicado_por_membro_id"],
            ["membros.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "sessoes_exibicao",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("indicacao_id", sa.String(), nullable=False),
        sa.Column("data_sessao", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(
            ["indicacao_id"],
            ["indicacoes.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("indicacao_id"),
    )
    op.create_table(
        "sorteios",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("rodada_id", sa.String(), nullable=False),
        sa.Column("indicacao_sorteada_id", sa.String(), nullable=False),
        sa.Column("data_sorteio", sa.DateTime(), nullable=False),
        sa.Column("metodo", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["indicacao_sorteada_id"],
            ["indicacoes.id"],
        ),
        sa.ForeignKeyConstraint(
            ["rodada_id"],
            ["rodadas.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "avaliacoes",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("sessao_id", sa.String(), nullable=False),
        sa.Column("membro_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("nota", sa.String(), nullable=True),
        sa.Column("comentario", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["membro_id"],
            ["membros.id"],
        ),
        sa.ForeignKeyConstraint(
            ["sessao_id"],
            ["sessoes_exibicao.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "sessao_membros_presentes",
        sa.Column("sessao_id", sa.String(), nullable=False),
        sa.Column("membro_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["membro_id"],
            ["membros.id"],
        ),
        sa.ForeignKeyConstraint(
            ["sessao_id"],
            ["sessoes_exibicao.id"],
        ),
        sa.PrimaryKeyConstraint("sessao_id", "membro_id"),
    )
    op.create_table(
        "trofeus",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("categoria_id", sa.String(), nullable=False),
        sa.Column("nomeacao_vencedora_id", sa.String(), nullable=False),
        sa.Column("membro_vencedor_id", sa.String(), nullable=False),
        sa.Column("data_apuracao", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(
            ["categoria_id"],
            ["categorias_oscar.id"],
        ),
        sa.ForeignKeyConstraint(
            ["membro_vencedor_id"],
            ["membros.id"],
        ),
        sa.ForeignKeyConstraint(
            ["nomeacao_vencedora_id"],
            ["nomeacoes_oscar.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("categoria_id"),
    )


def downgrade() -> None:
    op.drop_table("trofeus")
    op.drop_table("sessao_membros_presentes")
    op.drop_table("avaliacoes")
    op.drop_table("sorteios")
    op.drop_table("sessoes_exibicao")
    op.drop_table("nomeacoes_oscar")
    op.drop_table("indicacoes")
    op.drop_table("categorias_oscar")
    op.drop_table("temporadas_oscar")
    op.drop_table("rodadas")
    op.drop_table("membros")
    op.drop_table("filmes")
    op.drop_table("clubes")
