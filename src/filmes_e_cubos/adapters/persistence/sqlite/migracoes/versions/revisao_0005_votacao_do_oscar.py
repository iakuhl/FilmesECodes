"""Votação do Óscar: eleitores, turnos, candidatas e cédulas.

Revisão: 0005
Anterior: 0004
Criada em: 2026-09-25

A votação de uma edição tem eleitores definidos no início (decisão 23 de
docs/PENDENCIAS.md), corre em turnos por categoria (decisão 28) e guarda
uma cédula por eleitor e turno (decisão 25).

As edições que já estavam *em votação* antes desta revisão não tinham
votação registrada, e ninguém conseguiria votar nelas. Elas ganham uma,
com os membros ativos de agora como eleitores — a melhor aproximação de
"ativos quando a votação começou" — e o 1º turno aberto em cada
categoria que ainda não tem troféu e tem ao menos duas nomeações.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | Sequence[str] | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "votacoes_oscar",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("temporada_id", sa.String(), nullable=False),
        sa.Column("iniciada_em", sa.DateTime(), nullable=False),
        sa.Column("turno_atual", sa.Integer(), nullable=False),
        sa.Column("encerrada_em", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["temporada_id"], ["temporadas_oscar.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("temporada_id"),
    )
    op.create_table(
        "votacao_eleitores",
        sa.Column("votacao_id", sa.String(), nullable=False),
        sa.Column("membro_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["membro_id"], ["membros.id"]),
        sa.ForeignKeyConstraint(["votacao_id"], ["votacoes_oscar.id"]),
        sa.PrimaryKeyConstraint("votacao_id", "membro_id"),
    )
    op.create_table(
        "turnos_votacao",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("categoria_id", sa.String(), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("modo", sa.String(), nullable=False),
        sa.Column("apurado_em", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["categoria_id"], ["categorias_oscar.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("categoria_id", "numero"),
    )
    op.create_table(
        "turno_candidatas",
        sa.Column("turno_id", sa.String(), nullable=False),
        sa.Column("posicao", sa.Integer(), nullable=False),
        sa.Column("nomeacao_id", sa.String(), nullable=False),
        sa.Column("pontos", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["nomeacao_id"], ["nomeacoes_oscar.id"]),
        sa.ForeignKeyConstraint(["turno_id"], ["turnos_votacao.id"]),
        sa.PrimaryKeyConstraint("turno_id", "posicao"),
    )
    op.create_table(
        "cedulas",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("votacao_id", sa.String(), nullable=False),
        sa.Column("turno", sa.Integer(), nullable=False),
        sa.Column("membro_id", sa.String(), nullable=False),
        sa.Column("confirmada_em", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["membro_id"], ["membros.id"]),
        sa.ForeignKeyConstraint(["votacao_id"], ["votacoes_oscar.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("votacao_id", "turno", "membro_id"),
    )
    op.create_table(
        "cedula_escolhas",
        sa.Column("cedula_id", sa.String(), nullable=False),
        sa.Column("categoria_id", sa.String(), nullable=False),
        sa.Column("posicao", sa.Integer(), nullable=False),
        sa.Column("nomeacao_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["categoria_id"], ["categorias_oscar.id"]),
        sa.ForeignKeyConstraint(["cedula_id"], ["cedulas.id"]),
        sa.ForeignKeyConstraint(["nomeacao_id"], ["nomeacoes_oscar.id"]),
        sa.PrimaryKeyConstraint("cedula_id", "categoria_id", "posicao"),
    )
    _iniciar_as_votacoes_em_andamento(op.get_bind())


def downgrade() -> None:
    for tabela in (
        "cedula_escolhas",
        "cedulas",
        "turno_candidatas",
        "turnos_votacao",
        "votacao_eleitores",
        "votacoes_oscar",
    ):
        op.drop_table(tabela)


# Retratos das tabelas como estão nesta revisão: gravar por elas (e não por
# SQL puro) deixa o SQLAlchemy formatar as datas como o resto do programa lê.
_votacoes = sa.table(
    "votacoes_oscar",
    sa.column("id", sa.String()),
    sa.column("temporada_id", sa.String()),
    sa.column("iniciada_em", sa.DateTime()),
    sa.column("turno_atual", sa.Integer()),
    sa.column("encerrada_em", sa.DateTime()),
)
_eleitores = sa.table(
    "votacao_eleitores", sa.column("votacao_id", sa.String()), sa.column("membro_id", sa.String())
)
_turnos = sa.table(
    "turnos_votacao",
    sa.column("id", sa.String()),
    sa.column("categoria_id", sa.String()),
    sa.column("numero", sa.Integer()),
    sa.column("modo", sa.String()),
    sa.column("apurado_em", sa.DateTime()),
)
_candidatas = sa.table(
    "turno_candidatas",
    sa.column("turno_id", sa.String()),
    sa.column("posicao", sa.Integer()),
    sa.column("nomeacao_id", sa.String()),
    sa.column("pontos", sa.Integer()),
)


def _iniciar_as_votacoes_em_andamento(conexao: sa.Connection) -> None:
    agora = datetime.now()
    edicoes = conexao.execute(
        sa.text("SELECT id, clube_id FROM temporadas_oscar WHERE status = 'EM_VOTACAO'")
    ).all()
    for temporada_id, clube_id in edicoes:
        votacao_id = str(uuid4())
        disputas = _disputas_da_edicao(conexao, temporada_id)
        conexao.execute(
            _votacoes.insert().values(
                id=votacao_id,
                temporada_id=temporada_id,
                iniciada_em=agora,
                turno_atual=1,
                encerrada_em=None if disputas else agora,
            )
        )
        membros = (
            conexao.execute(
                sa.text("SELECT id FROM membros WHERE clube_id = :clube AND ativo"),
                {"clube": clube_id},
            )
            .scalars()
            .all()
        )
        for membro_id in membros:
            conexao.execute(_eleitores.insert().values(votacao_id=votacao_id, membro_id=membro_id))
        for categoria_id, nomeacoes in disputas:
            turno_id = str(uuid4())
            conexao.execute(
                _turnos.insert().values(
                    id=turno_id, categoria_id=categoria_id, numero=1, modo="DUPLA", apurado_em=None
                )
            )
            for posicao, nomeacao_id in enumerate(nomeacoes, start=1):
                conexao.execute(
                    _candidatas.insert().values(
                        turno_id=turno_id, posicao=posicao, nomeacao_id=nomeacao_id, pontos=None
                    )
                )


def _disputas_da_edicao(conexao: sa.Connection, temporada_id: str) -> list[tuple[str, list[str]]]:
    """As categorias ainda sem troféu, cada uma com as nomeações na ordem em que foram feitas.

    No SQLite, a ordem de criação é a do `rowid`. Outros bancos só chegam a
    esta revisão vazios (o Postgres de produção nasceu depois dela), mas a
    consulta precisa ser válida neles também.
    """
    ordem = "rowid" if conexao.dialect.name == "sqlite" else "id"
    categorias = (
        conexao.execute(
            sa.text(
                "SELECT id FROM categorias_oscar WHERE temporada_id = :temporada AND id NOT IN "
                f"(SELECT categoria_id FROM trofeus) ORDER BY {ordem}"
            ),
            {"temporada": temporada_id},
        )
        .scalars()
        .all()
    )
    disputas = []
    for categoria_id in categorias:
        nomeacoes = list(
            conexao.execute(
                sa.text(
                    "SELECT id FROM nomeacoes_oscar WHERE categoria_id = :categoria "
                    f"ORDER BY {ordem}"
                ),
                {"categoria": categoria_id},
            )
            .scalars()
            .all()
        )
        if len(nomeacoes) >= 2:
            disputas.append((categoria_id, nomeacoes))
    return disputas
