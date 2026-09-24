"""Comandos do ciclo de vida de uma rodada de indicações."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

import typer

from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.adapters.interfaces.cli.apresentacao import (
    echo_resultado,
    echo_tabela,
    echo_titulo,
    formatar_opcional,
)
from filmes_e_cubos.adapters.interfaces.cli.contexto import obter_contexto
from filmes_e_cubos.adapters.interfaces.cli.resolucao import resolver_clube, resolver_rodada
from filmes_e_cubos.domain.entities.indicacao import Indicacao

app = typer.Typer(help="Abertura, situação e encerramento de rodadas.", no_args_is_help=True)


@app.command("abrir")
def abrir(
    ctx: typer.Context,
    clube_id: Annotated[UUID | None, typer.Option("--clube-id", help="Clube da rodada.")] = None,
) -> None:
    """Abre uma nova rodada de indicações."""
    contexto = obter_contexto(ctx)
    clube = resolver_clube(contexto, clube_id)
    rodada = contexto.abrir_nova_rodada.executar(clube_id=clube.id)
    echo_resultado(f"Rodada {rodada.numero} aberta em {rodada.data_inicio} ({rodada.id})")


@app.command("encerrar")
def encerrar(
    ctx: typer.Context,
    rodada_id: Annotated[
        UUID | None, typer.Option("--rodada-id", help="Rodada a encerrar (padrão: a aberta).")
    ] = None,
    clube_id: Annotated[UUID | None, typer.Option("--clube-id", help="Clube da rodada.")] = None,
) -> None:
    """Encerra a rodada, exigindo que todas as indicações já tenham sido assistidas."""
    contexto = obter_contexto(ctx)
    rodada = resolver_rodada(contexto, rodada_id, clube_id)
    encerrada = contexto.encerrar_rodada.executar(rodada_id=rodada.id)
    echo_resultado(
        f"Rodada {encerrada.numero} encerrada em {encerrada.data_encerramento} ({encerrada.id})"
    )


@app.command("status")
def status(
    ctx: typer.Context,
    rodada_id: Annotated[
        UUID | None, typer.Option("--rodada-id", help="Rodada a exibir (padrão: a aberta).")
    ] = None,
    clube_id: Annotated[UUID | None, typer.Option("--clube-id", help="Clube da rodada.")] = None,
) -> None:
    """Mostra a rodada e a situação de cada indicação dela."""
    contexto = obter_contexto(ctx)
    rodada = resolver_rodada(contexto, rodada_id, clube_id)

    situacao = "aberta" if rodada.esta_aberta else f"encerrada em {rodada.data_encerramento}"
    echo_titulo(f"Rodada {rodada.numero} — {situacao}")
    typer.echo(f"Id: {rodada.id}")
    typer.echo(f"Início: {rodada.data_inicio}")
    typer.echo("")

    indicacoes = contexto.indicacoes.listar_por_rodada(rodada.id)
    echo_tabela(
        ("ID", "FILME", "INDICADO POR", "TIPO", "SITUAÇÃO"),
        [_linha_de_indicacao(contexto, indicacao) for indicacao in indicacoes],
        vazio="Nenhuma indicação nesta rodada ainda.",
    )


def _linha_de_indicacao(contexto: Contexto, indicacao: Indicacao) -> tuple[str, ...]:
    filme = contexto.filmes.buscar_por_id(indicacao.filme_id)
    membro = (
        contexto.membros.buscar_por_id(indicacao.membro_id)
        if indicacao.membro_id is not None
        else None
    )
    return (
        str(indicacao.id),
        filme.titulo if filme is not None else str(indicacao.filme_id),
        formatar_opcional(membro.nome if membro is not None else None),
        indicacao.tipo.name.lower(),
        indicacao.status.name.lower(),
    )
