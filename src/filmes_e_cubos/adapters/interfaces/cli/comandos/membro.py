"""Comandos de gestão dos membros de um clube."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

import typer

from filmes_e_cubos.adapters.interfaces.cli.apresentacao import (
    echo_resultado,
    echo_tabela,
    formatar_opcional,
)
from filmes_e_cubos.adapters.interfaces.cli.contexto import obter_contexto
from filmes_e_cubos.adapters.interfaces.cli.resolucao import resolver_clube
from filmes_e_cubos.domain.value_objects.identificadores import MembroId

app = typer.Typer(help="Cadastro e situação dos membros.", no_args_is_help=True)


@app.command("cadastrar")
def cadastrar(
    ctx: typer.Context,
    nome: Annotated[str, typer.Argument(help="Nome do membro.")],
    apelido: Annotated[
        str | None, typer.Option("--apelido", help="Como o membro é chamado no clube.")
    ] = None,
    clube_id: Annotated[UUID | None, typer.Option("--clube-id", help="Clube do membro.")] = None,
) -> None:
    """Cadastra um membro no clube."""
    contexto = obter_contexto(ctx)
    clube = resolver_clube(contexto, clube_id)
    membro = contexto.cadastrar_membro.executar(clube_id=clube.id, nome=nome, apelido=apelido)
    echo_resultado(f"Membro cadastrado: {membro.nome} ({membro.id})")


@app.command("desativar")
def desativar(
    ctx: typer.Context,
    membro_id: Annotated[UUID, typer.Argument(help="Id do membro a desativar.")],
) -> None:
    """Desativa um membro, preservando todo o histórico dele."""
    contexto = obter_contexto(ctx)
    contexto.desativar_membro.executar(membro_id=MembroId(membro_id))
    echo_resultado(f"Membro desativado: {membro_id}")


@app.command("reativar")
def reativar(
    ctx: typer.Context,
    membro_id: Annotated[UUID, typer.Argument(help="Id do membro a reativar.")],
) -> None:
    """Reativa um membro desativado; ele volta a indicar, avaliar e votar."""
    contexto = obter_contexto(ctx)
    contexto.reativar_membro.executar(membro_id=MembroId(membro_id))
    echo_resultado(f"Membro reativado: {membro_id}")


@app.command("listar")
def listar(
    ctx: typer.Context,
    clube_id: Annotated[
        UUID | None, typer.Option("--clube-id", help="Clube cujos membros listar.")
    ] = None,
    apenas_ativos: Annotated[
        bool, typer.Option("--apenas-ativos", help="Omite os membros desativados.")
    ] = False,
) -> None:
    """Lista os membros do clube."""
    contexto = obter_contexto(ctx)
    clube = resolver_clube(contexto, clube_id)
    membros = (
        contexto.membros.listar_ativos_por_clube(clube.id)
        if apenas_ativos
        else contexto.membros.listar_por_clube(clube.id)
    )
    echo_tabela(
        ("ID", "NOME", "APELIDO", "INGRESSO", "SITUAÇÃO"),
        [
            (
                str(membro.id),
                membro.nome,
                formatar_opcional(membro.apelido),
                membro.data_ingresso.isoformat(),
                "ativo" if membro.ativo else "inativo",
            )
            for membro in membros
        ],
        vazio=f"Nenhum membro cadastrado em {clube.nome}.",
    )
