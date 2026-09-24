"""Comandos de indicação de filmes e de sorteio da próxima sessão."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

import typer

from filmes_e_cubos.adapters.interfaces.cli.apresentacao import echo_resultado
from filmes_e_cubos.adapters.interfaces.cli.contexto import obter_contexto
from filmes_e_cubos.adapters.interfaces.cli.resolucao import resolver_clube, resolver_rodada
from filmes_e_cubos.domain.value_objects.identificadores import FilmeId, MembroId

app = typer.Typer(help="Indicações da rodada e sorteio da sessão.", no_args_is_help=True)


@app.command("indicar")
def indicar(
    ctx: typer.Context,
    membro_id: Annotated[UUID, typer.Option("--membro-id", help="Membro que indica.")],
    filme_id: Annotated[UUID, typer.Option("--filme-id", help="Filme indicado.")],
    rodada_id: Annotated[
        UUID | None, typer.Option("--rodada-id", help="Rodada da indicação (padrão: a aberta).")
    ] = None,
    clube_id: Annotated[UUID | None, typer.Option("--clube-id", help="Clube da rodada.")] = None,
) -> None:
    """Registra a indicação semanal de um membro."""
    contexto = obter_contexto(ctx)
    rodada = resolver_rodada(contexto, rodada_id, clube_id)
    indicacao = contexto.indicar_filme.executar(
        rodada_id=rodada.id,
        membro_id=MembroId(membro_id),
        filme_id=FilmeId(filme_id),
    )
    echo_resultado(f"Indicação registrada: {indicacao.id}")


@app.command("democracia")
def democracia(
    ctx: typer.Context,
    filme_id: Annotated[UUID, typer.Option("--filme-id", help="Filme escolhido em grupo.")],
    clube_id: Annotated[UUID | None, typer.Option("--clube-id", help="Clube da rodada.")] = None,
) -> None:
    """Adiciona uma sessão extra escolhida em grupo, fora da cota da rodada."""
    contexto = obter_contexto(ctx)
    clube = resolver_clube(contexto, clube_id)
    indicacao = contexto.adicionar_filme_democracia.executar(
        clube_id=clube.id, filme_id=FilmeId(filme_id)
    )
    echo_resultado(f"Sessão democracia registrada: {indicacao.id}")


@app.command("sortear")
def sortear(
    ctx: typer.Context,
    rodada_id: Annotated[
        UUID | None, typer.Option("--rodada-id", help="Rodada do sorteio (padrão: a aberta).")
    ] = None,
    clube_id: Annotated[UUID | None, typer.Option("--clube-id", help="Clube da rodada.")] = None,
) -> None:
    """Sorteia uma das indicações pendentes para a próxima sessão."""
    contexto = obter_contexto(ctx)
    rodada = resolver_rodada(contexto, rodada_id, clube_id)
    sorteio = contexto.realizar_sorteio.executar(rodada_id=rodada.id)

    indicacao = contexto.indicacoes.buscar_por_id(sorteio.indicacao_sorteada_id)
    filme = contexto.filmes.buscar_por_id(indicacao.filme_id) if indicacao is not None else None
    titulo = filme.titulo if filme is not None else str(sorteio.indicacao_sorteada_id)
    echo_resultado(f"Sorteado: {titulo} (indicação {sorteio.indicacao_sorteada_id})")
