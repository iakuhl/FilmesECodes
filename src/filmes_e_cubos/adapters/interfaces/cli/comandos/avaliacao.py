"""Comandos de avaliação do filme assistido em uma sessão."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

import typer

from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.adapters.interfaces.cli.apresentacao import (
    echo_resultado,
    echo_tabela,
    formatar_decimal,
    formatar_opcional,
)
from filmes_e_cubos.adapters.interfaces.cli.contexto import obter_contexto
from filmes_e_cubos.adapters.interfaces.cli.conversores import converter_nota
from filmes_e_cubos.adapters.interfaces.estrelas import media_em_estrelas
from filmes_e_cubos.domain.entities.avaliacao import Avaliacao
from filmes_e_cubos.domain.value_objects.identificadores import MembroId, SessaoExibicaoId
from filmes_e_cubos.domain.value_objects.status_avaliacao import StatusAvaliacao

app = typer.Typer(help="Notas dos membros para as sessões assistidas.", no_args_is_help=True)


@app.command("registrar")
def registrar(
    ctx: typer.Context,
    sessao_id: Annotated[UUID, typer.Option("--sessao-id", help="Sessão avaliada.")],
    membro_id: Annotated[UUID, typer.Option("--membro-id", help="Membro que avalia.")],
    nota: Annotated[
        str | None,
        typer.Option(
            "--nota",
            help="Nota dada. Sem nota, o membro fica registrado como dorminhoco.",
        ),
    ] = None,
    comentario: Annotated[
        str | None, typer.Option("--comentario", help="Comentário do membro sobre o filme.")
    ] = None,
) -> None:
    """Registra a nota de um membro presente — ou que ele cochilou, se `--nota` for omitida.

    A escala de notas é a do clube dono da sessão.
    """
    contexto = obter_contexto(ctx)
    avaliacao = contexto.avaliar_filme.executar(
        sessao_id=SessaoExibicaoId(sessao_id),
        membro_id=MembroId(membro_id),
        nota=converter_nota(nota),
        comentario=comentario,
    )
    echo_resultado(f"Avaliação registrada: {_resultado(avaliacao)} ({avaliacao.id})")
    _echo_media(contexto, avaliacao.sessao_id)


@app.command("listar")
def listar(
    ctx: typer.Context,
    sessao_id: Annotated[UUID, typer.Argument(help="Sessão cujas avaliações listar.")],
) -> None:
    """Lista as avaliações de uma sessão."""
    contexto = obter_contexto(ctx)
    avaliacoes = contexto.avaliacoes.listar_por_sessao(SessaoExibicaoId(sessao_id))
    echo_tabela(
        ("MEMBRO", "NOTA", "COMENTÁRIO"),
        [
            (
                _nome_do_membro(contexto, avaliacao),
                _resultado(avaliacao),
                formatar_opcional(avaliacao.comentario),
            )
            for avaliacao in avaliacoes
        ],
        vazio="Nenhuma avaliação registrada para esta sessão.",
    )
    if avaliacoes:
        _echo_media(contexto, SessaoExibicaoId(sessao_id))


def _resultado(avaliacao: Avaliacao) -> str:
    """Nota formatada, ou o rótulo de dorminhoco quando não há nota."""
    if avaliacao.status is StatusAvaliacao.DORMINHOCO or avaliacao.nota is None:
        return "dorminhoco"
    return formatar_decimal(avaliacao.nota.valor)


def _echo_media(contexto: Contexto, sessao_id: SessaoExibicaoId) -> None:
    """A média da sessão em estrelas, ou o aviso de que só houve dorminhocos."""
    sessao = contexto.sessoes.buscar_por_id(sessao_id)
    media = sessao.media_das_notas if sessao is not None else None
    if media is None:
        typer.echo("Média da sessão: sem notas (só dorminhocos).")
        return
    notas = "nota" if media.quantidade == 1 else "notas"
    typer.echo(f"Média da sessão: {media_em_estrelas(media.valor)} ({media.quantidade} {notas})")


def _nome_do_membro(contexto: Contexto, avaliacao: Avaliacao) -> str:
    membro = contexto.membros.buscar_por_id(avaliacao.membro_id)
    return membro.nome if membro is not None else str(avaliacao.membro_id)
