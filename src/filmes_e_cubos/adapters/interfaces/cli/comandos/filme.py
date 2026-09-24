"""Comandos do catálogo de filmes.

O catálogo é compartilhado entre clubes (um `Filme` não pertence a um
clube), por isso nenhum comando aqui precisa resolver um clube.
"""

from __future__ import annotations

from typing import Annotated

import typer

from filmes_e_cubos.adapters.interfaces.cli.apresentacao import (
    echo_resultado,
    echo_tabela,
    formatar_opcional,
)
from filmes_e_cubos.adapters.interfaces.cli.contexto import obter_contexto

app = typer.Typer(help="Catálogo de filmes disponíveis para indicação.", no_args_is_help=True)


@app.command("cadastrar")
def cadastrar(
    ctx: typer.Context,
    titulo: Annotated[str, typer.Argument(help="Título do filme.")],
    ano: Annotated[int | None, typer.Option("--ano", help="Ano de lançamento.")] = None,
    diretor: Annotated[str | None, typer.Option("--diretor", help="Nome do diretor.")] = None,
    id_externo: Annotated[
        str | None,
        typer.Option("--id-externo", help="Identificador em uma base externa (IMDb, TMDB...)."),
    ] = None,
) -> None:
    """Cadastra um filme no catálogo."""
    contexto = obter_contexto(ctx)
    filme = contexto.cadastrar_filme.executar(
        titulo=titulo,
        ano_lancamento=ano,
        diretor=diretor,
        identificador_externo=id_externo,
    )
    echo_resultado(f"Filme cadastrado: {filme.titulo} ({filme.id})")


@app.command("listar")
def listar(ctx: typer.Context) -> None:
    """Lista os filmes do catálogo."""
    contexto = obter_contexto(ctx)
    filmes = contexto.filmes.listar_todos()
    echo_tabela(
        ("ID", "TÍTULO", "ANO", "DIRETOR"),
        [
            (
                str(filme.id),
                filme.titulo,
                formatar_opcional(filme.ano_lancamento),
                formatar_opcional(filme.diretor),
            )
            for filme in filmes
        ],
        vazio="Nenhum filme cadastrado.",
    )
