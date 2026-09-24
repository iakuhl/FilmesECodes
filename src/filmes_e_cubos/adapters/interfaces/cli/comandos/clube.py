"""Comandos de gestão de clubes."""

from __future__ import annotations

from typing import Annotated

import typer

from filmes_e_cubos.adapters.interfaces.cli.apresentacao import (
    echo_resultado,
    echo_tabela,
    formatar_decimal,
)
from filmes_e_cubos.adapters.interfaces.cli.contexto import obter_contexto
from filmes_e_cubos.adapters.interfaces.cli.conversores import converter_decimal
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.value_objects.configuracao_clube import ConfiguracaoClube
from filmes_e_cubos.domain.value_objects.escala_avaliacao import EscalaAvaliacao

app = typer.Typer(help="Criação e consulta de clubes.", no_args_is_help=True)

# Os padrões exibidos na ajuda são lidos do próprio domínio, para que a CLI
# nunca contradiga a configuração padrão de um clube.
_PADRAO = ConfiguracaoClube.padrao()


@app.command("criar")
def criar(
    ctx: typer.Context,
    nome: Annotated[str, typer.Argument(help="Nome do clube.")],
    tamanho_rodada: Annotated[
        int | None,
        typer.Option(
            "--tamanho-rodada",
            help=f"Indicações que fecham uma rodada (padrão: {_PADRAO.tamanho_rodada}).",
        ),
    ] = None,
    nota_minima: Annotated[
        str | None,
        typer.Option(
            "--nota-minima",
            help=f"Menor nota aceita (padrão: {_PADRAO.escala_avaliacao.nota_minima}).",
        ),
    ] = None,
    nota_maxima: Annotated[
        str | None,
        typer.Option(
            "--nota-maxima",
            help=f"Maior nota aceita (padrão: {_PADRAO.escala_avaliacao.nota_maxima}).",
        ),
    ] = None,
    passo: Annotated[
        str | None,
        typer.Option(
            "--passo",
            help=f"Granularidade das notas (padrão: {_PADRAO.escala_avaliacao.passo}).",
        ),
    ] = None,
) -> None:
    """Cria um clube, com a configuração padrão ou ajustada."""
    contexto = obter_contexto(ctx)
    escala = EscalaAvaliacao(
        nota_minima=(
            converter_decimal(nota_minima, opcao="--nota-minima")
            if nota_minima is not None
            else _PADRAO.escala_avaliacao.nota_minima
        ),
        nota_maxima=(
            converter_decimal(nota_maxima, opcao="--nota-maxima")
            if nota_maxima is not None
            else _PADRAO.escala_avaliacao.nota_maxima
        ),
        passo=(
            converter_decimal(passo, opcao="--passo")
            if passo is not None
            else _PADRAO.escala_avaliacao.passo
        ),
    )
    configuracao = ConfiguracaoClube(
        tamanho_rodada=tamanho_rodada if tamanho_rodada is not None else _PADRAO.tamanho_rodada,
        escala_avaliacao=escala,
    )
    clube = contexto.criar_clube.executar(nome=nome, configuracao=configuracao)
    echo_resultado(f"Clube criado: {clube.nome} ({clube.id})")


@app.command("listar")
def listar(ctx: typer.Context) -> None:
    """Lista os clubes cadastrados."""
    contexto = obter_contexto(ctx)
    clubes = contexto.clubes.listar_todos()
    echo_tabela(
        ("ID", "NOME", "RODADA", "ESCALA"),
        [
            (str(clube.id), clube.nome, str(clube.configuracao.tamanho_rodada), _escala(clube))
            for clube in clubes
        ],
        vazio="Nenhum clube cadastrado.",
    )


def _escala(clube: Clube) -> str:
    escala = clube.configuracao.escala_avaliacao
    return (
        f"{formatar_decimal(escala.nota_minima)} a {formatar_decimal(escala.nota_maxima)} "
        f"(passo {formatar_decimal(escala.passo)})"
    )
