"""Comandos de registro da sessão em que o clube assistiu a um filme."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

import typer

from filmes_e_cubos.adapters.interfaces.cli.apresentacao import echo_resultado
from filmes_e_cubos.adapters.interfaces.cli.contexto import obter_contexto
from filmes_e_cubos.adapters.interfaces.cli.erros import CliError
from filmes_e_cubos.adapters.interfaces.convencoes import presenca_padrao
from filmes_e_cubos.domain.value_objects.identificadores import IndicacaoId, MembroId

app = typer.Typer(help="Registro das sessões assistidas.", no_args_is_help=True)


@app.command("registrar")
def registrar(
    ctx: typer.Context,
    indicacao_id: Annotated[UUID, typer.Argument(help="Indicação do filme assistido.")],
    presentes: Annotated[
        list[UUID] | None,
        typer.Option(
            "--presente",
            help="Membro presente na sessão; repita a opção. "
            "Sem nenhuma, assume todos os membros ativos do clube.",
        ),
    ] = None,
) -> None:
    """Registra a sessão e marca a indicação como assistida."""
    contexto = obter_contexto(ctx)
    indicacao = contexto.indicacoes.buscar_por_id(IndicacaoId(indicacao_id))
    if indicacao is None:
        raise CliError(f"Indicação {indicacao_id} não encontrada.")

    membros_presentes = (
        frozenset(MembroId(membro_id) for membro_id in presentes)
        if presentes
        else presenca_padrao(indicacao, contexto.rodadas, contexto.membros)
    )
    sessao = contexto.registrar_sessao_exibicao.executar(
        indicacao_id=indicacao.id, membros_presentes=membros_presentes
    )
    echo_resultado(
        f"Sessão registrada em {sessao.data_sessao} com "
        f"{len(sessao.membros_presentes)} presente(s) ({sessao.id})"
    )
