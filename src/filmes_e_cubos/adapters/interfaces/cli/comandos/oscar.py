"""Comandos do Óscar do Filmes e Cubos: temporadas, categorias e apuração.

Os comandos estão agrupados em dois sub-apps (`temporada` e `categoria`)
mais duas ações diretas (`nomear` e `apurar`), acompanhando as três
etapas reais do evento: montar a edição, nomear os concorrentes e premiar.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

import typer

from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.adapters.interfaces.cli.apresentacao import (
    echo_resultado,
    echo_tabela,
    formatar_opcional,
)
from filmes_e_cubos.adapters.interfaces.cli.contexto import (
    obter_contexto,
    obter_criterio_apuracao,
)
from filmes_e_cubos.adapters.interfaces.cli.conversores import TipoCategoriaCli
from filmes_e_cubos.adapters.interfaces.cli.resolucao import resolver_clube, resolver_temporada
from filmes_e_cubos.adapters.interfaces.convencoes import nome_padrao_da_temporada
from filmes_e_cubos.domain.entities.temporada_oscar import NOMEACOES_POR_CATEGORIA_PADRAO
from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    FilmeId,
    MembroId,
)

app = typer.Typer(help="Óscar do Filmes e Cubos.", no_args_is_help=True)

temporada_app = typer.Typer(help="Edições anuais do Óscar.", no_args_is_help=True)
categoria_app = typer.Typer(help="Categorias de uma temporada.", no_args_is_help=True)
app.add_typer(temporada_app, name="temporada")
app.add_typer(categoria_app, name="categoria")


@temporada_app.command("abrir")
def temporada_abrir(
    ctx: typer.Context,
    ano: Annotated[
        int | None, typer.Option("--ano", help="Ano da edição (padrão: o ano corrente).")
    ] = None,
    nome: Annotated[
        str | None, typer.Option("--nome", help="Nome da edição (padrão: derivado do ano).")
    ] = None,
    nomeacoes_por_categoria: Annotated[
        int,
        typer.Option(
            "--nomeacoes-por-categoria",
            help="Quantas nomeações toda categoria da edição terá (mínimo 2).",
        ),
    ] = NOMEACOES_POR_CATEGORIA_PADRAO,
    clube_id: Annotated[UUID | None, typer.Option("--clube-id", help="Clube da edição.")] = None,
) -> None:
    """Abre uma edição anual do Óscar — uma por ano."""
    contexto = obter_contexto(ctx)
    clube = resolver_clube(contexto, clube_id)
    ano_da_edicao = ano if ano is not None else contexto.relogio.hoje().year
    temporada = contexto.abrir_temporada_oscar.executar(
        clube_id=clube.id,
        ano=ano_da_edicao,
        nome=nome if nome is not None else nome_padrao_da_temporada(clube.nome, ano_da_edicao),
        nomeacoes_por_categoria=nomeacoes_por_categoria,
    )
    echo_resultado(f"Temporada aberta: {temporada.nome} ({temporada.id})")


@temporada_app.command("listar")
def temporada_listar(
    ctx: typer.Context,
    clube_id: Annotated[UUID | None, typer.Option("--clube-id", help="Clube das edições.")] = None,
) -> None:
    """Lista as edições do Óscar de um clube."""
    contexto = obter_contexto(ctx)
    clube = resolver_clube(contexto, clube_id)
    temporadas = contexto.temporadas.listar_por_clube(clube.id)
    echo_tabela(
        ("ID", "ANO", "NOME", "SITUAÇÃO", "NOMEAÇÕES", "EVENTO"),
        [
            (
                str(t.id),
                str(t.ano),
                t.nome,
                t.status.name.lower(),
                f"{t.nomeacoes_por_categoria} por categoria",
                formatar_opcional(t.data_evento.isoformat() if t.data_evento else None),
            )
            for t in temporadas
        ],
        vazio=f"Nenhuma temporada do Óscar em {clube.nome}.",
    )


@temporada_app.command("avancar")
def temporada_avancar(
    ctx: typer.Context,
    temporada_id: Annotated[
        UUID | None,
        typer.Option("--temporada-id", help="Temporada a avançar (padrão: a do ano corrente)."),
    ] = None,
    clube_id: Annotated[UUID | None, typer.Option("--clube-id", help="Clube da temporada.")] = None,
) -> None:
    """Leva a edição à fase seguinte: preparação, indicações, votação, apurada, encerrada."""
    contexto = obter_contexto(ctx)
    temporada = resolver_temporada(contexto, temporada_id, clube_id)
    anterior = temporada.status
    temporada = contexto.avancar_temporada_oscar.executar(temporada_id=temporada.id)
    echo_resultado(f"{temporada.nome}: {anterior.name.lower()} -> {temporada.status.name.lower()}")


@temporada_app.command("data-evento")
def temporada_data_evento(
    ctx: typer.Context,
    data: Annotated[
        datetime,
        typer.Argument(
            formats=["%Y-%m-%d", "%d/%m/%Y"],
            help="Dia da cerimônia (AAAA-MM-DD ou DD/MM/AAAA).",
            show_default=False,
        ),
    ],
    temporada_id: Annotated[
        UUID | None,
        typer.Option("--temporada-id", help="Temporada do evento (padrão: a do ano corrente)."),
    ] = None,
    clube_id: Annotated[UUID | None, typer.Option("--clube-id", help="Clube da temporada.")] = None,
) -> None:
    """Marca (ou remarca) a data do evento de uma edição do Óscar."""
    contexto = obter_contexto(ctx)
    temporada = resolver_temporada(contexto, temporada_id, clube_id)
    temporada = contexto.definir_data_evento_oscar.executar(
        temporada_id=temporada.id, data_evento=data.date()
    )
    echo_resultado(f"Evento de {temporada.nome} marcado para {data.date().isoformat()}")


@categoria_app.command("definir")
def categoria_definir(
    ctx: typer.Context,
    nome: Annotated[str, typer.Argument(help='Nome da categoria (ex.: "Melhor veículo").')],
    tipo: Annotated[
        TipoCategoriaCli,
        typer.Option("--tipo", help="Categoria fixa do clube ou variável do ano."),
    ] = TipoCategoriaCli.VARIAVEL,
    descricao: Annotated[
        str | None, typer.Option("--descricao", help="O que a categoria premia.")
    ] = None,
    temporada_id: Annotated[
        UUID | None,
        typer.Option("--temporada-id", help="Temporada da categoria (padrão: a do ano corrente)."),
    ] = None,
    clube_id: Annotated[UUID | None, typer.Option("--clube-id", help="Clube da temporada.")] = None,
) -> None:
    """Adiciona uma categoria à temporada."""
    contexto = obter_contexto(ctx)
    temporada = resolver_temporada(contexto, temporada_id, clube_id)
    categoria = contexto.definir_categoria_oscar.executar(
        temporada_id=temporada.id,
        nome=nome,
        tipo=tipo.para_dominio(),
        descricao=descricao,
    )
    echo_resultado(f"Categoria definida: {categoria.nome} ({categoria.id})")


@categoria_app.command("listar")
def categoria_listar(
    ctx: typer.Context,
    temporada_id: Annotated[
        UUID | None,
        typer.Option("--temporada-id", help="Temporada a exibir (padrão: a do ano corrente)."),
    ] = None,
    clube_id: Annotated[UUID | None, typer.Option("--clube-id", help="Clube da temporada.")] = None,
) -> None:
    """Lista as categorias de uma temporada e quem já levou cada troféu."""
    contexto = obter_contexto(ctx)
    temporada = resolver_temporada(contexto, temporada_id, clube_id)
    categorias = contexto.categorias.listar_por_temporada(temporada.id)
    echo_tabela(
        ("ID", "CATEGORIA", "TIPO", "DESCRIÇÃO", "NOMEAÇÕES", "VENCEDOR"),
        [
            (
                str(categoria.id),
                categoria.nome,
                categoria.tipo.name.lower(),
                formatar_opcional(categoria.descricao),
                f"{len(contexto.nomeacoes.listar_por_categoria(categoria.id))}"
                f"/{temporada.nomeacoes_por_categoria}",
                _vencedor(contexto, categoria.id),
            )
            for categoria in categorias
        ],
        vazio=f"Nenhuma categoria definida em {temporada.nome}.",
    )


@app.command("nomear")
def nomear(
    ctx: typer.Context,
    categoria_id: Annotated[UUID, typer.Option("--categoria-id", help="Categoria disputada.")],
    filme_id: Annotated[UUID, typer.Option("--filme-id", help="Filme nomeado.")],
) -> None:
    """Nomeia um filme assistido no ano da temporada para uma categoria."""
    contexto = obter_contexto(ctx)
    nomeacao = contexto.indicar_filme_para_categoria.executar(
        categoria_id=CategoriaOscarId(categoria_id), filme_id=FilmeId(filme_id)
    )
    echo_resultado(f"Nomeação registrada: {nomeacao.id}")


@app.command("apurar")
def apurar(
    ctx: typer.Context,
    categoria_id: Annotated[UUID, typer.Argument(help="Categoria a apurar.")],
    membro_vencedor_id: Annotated[
        UUID | None,
        typer.Option(
            "--membro-vencedor-id",
            help="Quem leva o troféu quando o filme vencedor veio de uma sessão democracia "
            "(sem membro indicador).",
        ),
    ] = None,
) -> None:
    """Apura a categoria e emite o troféu.

    A vencedora é escolhida pelo critério de apuração da CLI — por padrão,
    `CriterioApuracaoInterativo`, que pergunta aqui mesmo.
    """
    contexto = obter_contexto(ctx)
    apuracao = contexto.apurar_categoria_oscar(obter_criterio_apuracao(ctx))
    trofeu = apuracao.executar(
        categoria_id=CategoriaOscarId(categoria_id),
        membro_vencedor_manual_id=(
            MembroId(membro_vencedor_id) if membro_vencedor_id is not None else None
        ),
    )
    membro = contexto.membros.buscar_por_id(trofeu.membro_vencedor_id)
    vencedor = membro.nome if membro is not None else str(trofeu.membro_vencedor_id)
    echo_resultado(f"Troféu para {vencedor} ({trofeu.id})")


def _vencedor(contexto: Contexto, categoria_id: CategoriaOscarId) -> str:
    trofeu = contexto.trofeus.buscar_por_categoria(categoria_id)
    if trofeu is None:
        return formatar_opcional(None)
    membro = contexto.membros.buscar_por_id(trofeu.membro_vencedor_id)
    return membro.nome if membro is not None else str(trofeu.membro_vencedor_id)
