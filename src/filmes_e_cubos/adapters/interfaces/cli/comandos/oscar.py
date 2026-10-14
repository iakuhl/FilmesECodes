"""Comandos do Óscar do Filmes e Cubos: temporadas, categorias, votação e apuração.

Os comandos estão agrupados em dois sub-apps (`temporada` e `categoria`)
mais as ações diretas, que acompanham as etapas reais do evento: montar
a edição, nomear os concorrentes (`nomear`), votar (`votacao`, `votar` e
`confirmar`), mandar o placar a quem monta a cerimônia (`enviar-placar`)
e, depois dela, registrar os vencedores (`premiar`).

O voto é secreto (decisão 26 de docs/PENDENCIAS.md): nenhum comando
mostra em que alguém votou, nem o placar.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

import typer

from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.adapters.interfaces.cli.apresentacao import (
    echo_aviso,
    echo_resultado,
    echo_tabela,
    echo_titulo,
    formatar_opcional,
)
from filmes_e_cubos.adapters.interfaces.cli.contexto import obter_contexto
from filmes_e_cubos.adapters.interfaces.cli.conversores import TipoCategoriaCli
from filmes_e_cubos.adapters.interfaces.cli.resolucao import (
    resolver_clube,
    resolver_escolhas,
    resolver_temporada,
)
from filmes_e_cubos.adapters.interfaces.convencoes import nome_padrao_da_temporada
from filmes_e_cubos.adapters.interfaces.situacao_da_votacao import situacao_da_votacao
from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar
from filmes_e_cubos.domain.entities.temporada_oscar import NOMEACOES_POR_CATEGORIA_PADRAO
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    FilmeId,
    MembroId,
    NomeacaoOscarId,
)
from filmes_e_cubos.domain.value_objects.status import ModoDeVotacao

app = typer.Typer(help="Óscar do Filmes e Cubos.", no_args_is_help=True)

_COMO_VOTAR = {
    ModoDeVotacao.DUPLA: "vote na 1ª e na 2ª opção",
    ModoDeVotacao.CLASSIFICACAO: "ordene todas as candidatas",
}

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


@categoria_app.command("nomeacoes")
def categoria_nomeacoes(
    ctx: typer.Context,
    categoria_id: Annotated[UUID, typer.Argument(help="Categoria cujas nomeações listar.")],
) -> None:
    """Lista as nomeações de uma categoria: posição, id, filme e quem indicou."""
    contexto = obter_contexto(ctx)
    categoria = contexto.categorias.buscar_por_id(CategoriaOscarId(categoria_id))
    if categoria is None:
        raise EntidadeNaoEncontradaError(f"Categoria {categoria_id} não encontrada.")
    echo_tabela(
        ("#", "NOMEAÇÃO", "FILME", "INDICADO POR"),
        [
            (str(posicao), str(nomeacao.id), *_filme_e_indicador(contexto, nomeacao))
            for posicao, nomeacao in enumerate(
                contexto.nomeacoes.listar_por_categoria(categoria.id), start=1
            )
        ],
        vazio=f"Nenhuma nomeação em {categoria.nome}.",
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


@app.command("votacao")
def votacao(
    ctx: typer.Context,
    temporada_id: Annotated[
        UUID | None,
        typer.Option("--temporada-id", help="Temporada da votação (padrão: a do ano corrente)."),
    ] = None,
    clube_id: Annotated[UUID | None, typer.Option("--clube-id", help="Clube da temporada.")] = None,
) -> None:
    """Mostra o turno atual da votação: as categorias em disputa e quem já votou.

    As candidatas aparecem numeradas: `oscar votar` aceita essas posições.
    De cada eleitor, só se vê em quantas categorias já votou — nunca em quê.
    """
    contexto = obter_contexto(ctx)
    temporada = resolver_temporada(contexto, temporada_id, clube_id)
    situacao = situacao_da_votacao(contexto, temporada)
    if situacao.votacao.encerrada:
        echo_resultado(f"A votação de {temporada.nome} terminou: o placar já pode ser enviado.")
    else:
        echo_titulo(f"{temporada.nome}: {situacao.votacao.turno_atual}º turno da votação")
    for disputa in situacao.disputas:
        typer.echo()
        echo_titulo(
            f"{disputa.categoria.nome} ({disputa.categoria.id}) — {_COMO_VOTAR[disputa.turno.modo]}"
        )
        echo_tabela(
            ("#", "NOMEAÇÃO", "FILME", "INDICADO POR"),
            [
                (str(posicao), str(nomeacao.id), *_filme_e_indicador(contexto, nomeacao))
                for posicao, nomeacao in enumerate(disputa.candidatas, start=1)
            ],
        )
    typer.echo()
    echo_titulo("Eleitores")
    echo_tabela(
        ("MEMBRO", "CÉDULA"),
        [
            (
                eleitor.membro.nome,
                "confirmada"
                if eleitor.confirmou
                else f"votou em {eleitor.categorias_votadas} de {len(situacao.disputas)}",
            )
            for eleitor in situacao.eleitores
        ],
    )


@app.command("votar")
def votar(
    ctx: typer.Context,
    escolhas: Annotated[
        list[str],
        typer.Argument(
            help="As nomeações escolhidas, em ordem de preferência — pela posição que "
            "`oscar votacao` mostra (1, 2...) ou pelo id. Na votação dupla, a 1ª e a 2ª "
            "opção; na classificação, todas as candidatas.",
            show_default=False,
        ),
    ],
    membro_id: Annotated[UUID, typer.Option("--membro-id", help="Quem vota.")],
    categoria_id: Annotated[UUID, typer.Option("--categoria-id", help="Categoria votada.")],
) -> None:
    """Registra (ou troca) o voto de um eleitor numa categoria do turno atual.

    O voto vale até a cédula ser confirmada com `oscar confirmar`.
    """
    contexto = obter_contexto(ctx)
    categoria = CategoriaOscarId(categoria_id)
    cedula = contexto.registrar_voto.executar(
        categoria_id=categoria,
        membro_id=MembroId(membro_id),
        escolhas=resolver_escolhas(contexto, categoria, escolhas),
    )
    echo_resultado(
        f"Voto registrado na cédula do {cedula.turno}º turno. Quando votar em todas as "
        "categorias, confirme com `oscar confirmar`."
    )


@app.command("confirmar")
def confirmar(
    ctx: typer.Context,
    membro_id: Annotated[UUID, typer.Option("--membro-id", help="Dono da cédula.")],
    temporada_id: Annotated[
        UUID | None,
        typer.Option("--temporada-id", help="Temporada da votação (padrão: a do ano corrente)."),
    ] = None,
    clube_id: Annotated[UUID | None, typer.Option("--clube-id", help="Clube da temporada.")] = None,
) -> None:
    """Confirma a cédula do eleitor no turno atual — depois disso, os votos não mudam.

    A última confirmação encerra o turno: o sistema apura sem mostrar nada
    e, se houve empate em alguma categoria, abre o turno seguinte.
    """
    contexto = obter_contexto(ctx)
    temporada = resolver_temporada(contexto, temporada_id, clube_id)
    resultado = contexto.confirmar_cedula.executar(
        temporada_id=temporada.id, membro_id=MembroId(membro_id)
    )
    echo_resultado("Cédula confirmada.")
    if not resultado.turno_encerrado:
        pendentes = sorted(_nome_do_membro(contexto, membro) for membro in resultado.pendentes)
        echo_aviso(f"Ainda faltam confirmar: {', '.join(pendentes)}.")
    elif resultado.votacao.encerrada:
        echo_resultado("Todos confirmaram: a votação terminou, e o placar já pode ser enviado.")
    else:
        echo_resultado(
            "Todos confirmaram. Houve empate no topo de alguma categoria: começou o "
            f"{resultado.votacao.turno_atual}º turno (veja `oscar votacao`)."
        )


@app.command("enviar-placar")
def enviar_placar(
    ctx: typer.Context,
    destinatario: Annotated[
        str, typer.Argument(help="E-mail de quem monta a cerimônia.", show_default=False)
    ],
    temporada_id: Annotated[
        UUID | None,
        typer.Option("--temporada-id", help="Temporada da votação (padrão: a do ano corrente)."),
    ] = None,
    clube_id: Annotated[UUID | None, typer.Option("--clube-id", help="Clube da temporada.")] = None,
) -> None:
    """Envia o placar da votação terminada por e-mail — sem mostrá-lo aqui.

    O placar não aparece em nenhuma tela (decisão 27): vai direto para o
    endereço informado. Pode ser reenviado até a edição ser encerrada.
    """
    contexto = obter_contexto(ctx)
    temporada = resolver_temporada(contexto, temporada_id, clube_id)
    endereco = contexto.enviar_placar_oscar.executar(
        temporada_id=temporada.id, destinatario=destinatario
    )
    echo_resultado(f"Placar de {temporada.nome} enviado para {endereco}.")


@app.command("premiar")
def premiar(
    ctx: typer.Context,
    categoria_id: Annotated[UUID, typer.Argument(help="Categoria premiada.")],
    nomeacao_id: Annotated[
        UUID | None,
        typer.Option(
            "--nomeacao-id",
            help="Nomeação vencedora (veja `oscar categoria nomeacoes`). Sem ela, é um "
            "empate absoluto.",
        ),
    ] = None,
    membro_escolhido_id: Annotated[
        UUID | None,
        typer.Option(
            "--membro-escolhido-id",
            help="Quem o grupo escolheu para levar o troféu: obrigatório quando o filme "
            "vencedor veio de uma sessão democracia e num empate absoluto.",
        ),
    ] = None,
) -> None:
    """Registra, depois da cerimônia, o vencedor da categoria e emite o troféu.

    A apuração acontece fora do sistema, com o placar que foi por e-mail;
    aqui se registra só o resultado. O troféu vai para quem indicou o
    filme vencedor.
    """
    contexto = obter_contexto(ctx)
    trofeu = contexto.registrar_vencedor_oscar.executar(
        categoria_id=CategoriaOscarId(categoria_id),
        nomeacao_id=NomeacaoOscarId(nomeacao_id) if nomeacao_id is not None else None,
        membro_escolhido_id=(
            MembroId(membro_escolhido_id) if membro_escolhido_id is not None else None
        ),
    )
    vencedor = _nome_do_membro(contexto, trofeu.membro_vencedor_id)
    echo_resultado(f"Troféu para {vencedor} ({trofeu.id})")


def _filme_e_indicador(contexto: Contexto, nomeacao: NomeacaoOscar) -> tuple[str, str]:
    filme = contexto.filmes.buscar_por_id(nomeacao.filme_id)
    titulo = filme.titulo if filme is not None else str(nomeacao.filme_id)
    if nomeacao.indicado_por_membro_id is None:
        return titulo, "democracia"
    return titulo, _nome_do_membro(contexto, nomeacao.indicado_por_membro_id)


def _nome_do_membro(contexto: Contexto, membro_id: MembroId) -> str:
    membro = contexto.membros.buscar_por_id(membro_id)
    return membro.nome if membro is not None else str(membro_id)


def _vencedor(contexto: Contexto, categoria_id: CategoriaOscarId) -> str:
    trofeu = contexto.trofeus.buscar_por_categoria(categoria_id)
    if trofeu is None:
        return formatar_opcional(None)
    membro = contexto.membros.buscar_por_id(trofeu.membro_vencedor_id)
    return membro.nome if membro is not None else str(trofeu.membro_vencedor_id)
