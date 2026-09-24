"""Rotas do Óscar do Filmes e Cubos: temporadas, categorias, nomeações e apuração."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, status

from filmes_e_cubos.adapters.interfaces.api.dependencias import ContextoDep
from filmes_e_cubos.adapters.interfaces.api.esquemas import (
    CategoriaSaida,
    NomeacaoSaida,
    NovaCategoria,
    NovaNomeacao,
    NovaTemporada,
    PedidoDeApuracao,
    TemporadaSaida,
    TrofeuSaida,
)
from filmes_e_cubos.adapters.interfaces.consultas import (
    obter_categoria,
    obter_clube,
    obter_nomeacao,
    obter_temporada,
)
from filmes_e_cubos.adapters.interfaces.convencoes import nome_padrao_da_temporada
from filmes_e_cubos.adapters.servicos.criterio_apuracao_escolha_informada import (
    CriterioEscolhaInformada,
)
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    FilmeId,
    MembroId,
    NomeacaoOscarId,
    TemporadaOscarId,
)

roteador = APIRouter(tags=["óscar"])


@roteador.get("/clubes/{clube_id}/oscar/temporadas", summary="Lista as edições do Óscar")
def listar_temporadas(clube_id: UUID, contexto: ContextoDep) -> list[TemporadaSaida]:
    clube = obter_clube(contexto.clubes, clube_id)
    return [
        TemporadaSaida.de_dominio(temporada)
        for temporada in contexto.temporadas.listar_por_clube(clube.id)
    ]


@roteador.post(
    "/clubes/{clube_id}/oscar/temporadas",
    status_code=status.HTTP_201_CREATED,
    summary="Abre uma edição do Óscar",
    description="O corpo é opcional: sem `ano`, usa o ano corrente; sem `nome`, "
    '"Óscar do <clube> <ano>".',
)
def abrir_temporada(
    clube_id: UUID,
    contexto: ContextoDep,
    nova: Annotated[NovaTemporada | None, Body()] = None,
) -> TemporadaSaida:
    clube = obter_clube(contexto.clubes, clube_id)
    pedido = nova or NovaTemporada()
    ano = pedido.ano if pedido.ano is not None else contexto.relogio.hoje().year
    temporada = contexto.abrir_temporada_oscar.executar(
        clube_id=clube.id,
        ano=ano,
        nome=pedido.nome if pedido.nome is not None else nome_padrao_da_temporada(clube.nome, ano),
    )
    return TemporadaSaida.de_dominio(temporada)


@roteador.get("/oscar/temporadas/{temporada_id}", summary="Consulta uma edição do Óscar")
def consultar_temporada(temporada_id: UUID, contexto: ContextoDep) -> TemporadaSaida:
    return TemporadaSaida.de_dominio(obter_temporada(contexto.temporadas, temporada_id))


@roteador.get(
    "/oscar/temporadas/{temporada_id}/categorias", summary="Lista as categorias de uma edição"
)
def listar_categorias(temporada_id: UUID, contexto: ContextoDep) -> list[CategoriaSaida]:
    temporada = obter_temporada(contexto.temporadas, temporada_id)
    return [
        CategoriaSaida.de_dominio(categoria)
        for categoria in contexto.categorias.listar_por_temporada(temporada.id)
    ]


@roteador.post(
    "/oscar/temporadas/{temporada_id}/categorias",
    status_code=status.HTTP_201_CREATED,
    summary="Define uma categoria",
)
def definir_categoria(
    temporada_id: UUID, nova: NovaCategoria, contexto: ContextoDep
) -> CategoriaSaida:
    categoria = contexto.definir_categoria_oscar.executar(
        temporada_id=TemporadaOscarId(temporada_id),
        nome=nova.nome,
        tipo=nova.tipo.para_dominio(),
        descricao=nova.descricao,
    )
    return CategoriaSaida.de_dominio(categoria)


@roteador.get("/oscar/categorias/{categoria_id}", summary="Consulta uma categoria")
def consultar_categoria(categoria_id: UUID, contexto: ContextoDep) -> CategoriaSaida:
    return CategoriaSaida.de_dominio(obter_categoria(contexto.categorias, categoria_id))


@roteador.get(
    "/oscar/categorias/{categoria_id}/nomeacoes", summary="Lista as nomeações de uma categoria"
)
def listar_nomeacoes(categoria_id: UUID, contexto: ContextoDep) -> list[NomeacaoSaida]:
    categoria = obter_categoria(contexto.categorias, categoria_id)
    return [
        NomeacaoSaida.de_dominio(nomeacao)
        for nomeacao in contexto.nomeacoes.listar_por_categoria(categoria.id)
    ]


@roteador.post(
    "/oscar/categorias/{categoria_id}/nomeacoes",
    status_code=status.HTTP_201_CREATED,
    summary="Nomeia um filme para a categoria",
    description="O filme precisa ter sido assistido pelo clube dentro do ano da edição. A "
    "nomeação herda quem indicou o filme — é essa pessoa que leva o troféu.",
)
def nomear(categoria_id: UUID, nova: NovaNomeacao, contexto: ContextoDep) -> NomeacaoSaida:
    nomeacao = contexto.indicar_filme_para_categoria.executar(
        categoria_id=CategoriaOscarId(categoria_id), filme_id=FilmeId(nova.filme_id)
    )
    return NomeacaoSaida.de_dominio(nomeacao)


@roteador.get("/oscar/nomeacoes/{nomeacao_id}", summary="Consulta uma nomeação")
def consultar_nomeacao(nomeacao_id: UUID, contexto: ContextoDep) -> NomeacaoSaida:
    return NomeacaoSaida.de_dominio(obter_nomeacao(contexto.nomeacoes, nomeacao_id))


@roteador.post(
    "/oscar/categorias/{categoria_id}/apuracao",
    status_code=status.HTTP_201_CREATED,
    summary="Apura a categoria e emite o troféu",
    description="O mecanismo de apuração ainda está em aberto no produto, então a API não "
    "escolhe a vencedora: registra a escolha do grupo. O troféu vai para quem indicou o "
    "filme vencedor; se ele veio de uma sessão democracia, `membro_vencedor_id` é obrigatório.",
)
def apurar(categoria_id: UUID, pedido: PedidoDeApuracao, contexto: ContextoDep) -> TrofeuSaida:
    criterio = CriterioEscolhaInformada(NomeacaoOscarId(pedido.nomeacao_vencedora_id))
    trofeu = contexto.apurar_categoria_oscar(criterio).executar(
        categoria_id=CategoriaOscarId(categoria_id),
        membro_vencedor_manual_id=(
            MembroId(pedido.membro_vencedor_id) if pedido.membro_vencedor_id is not None else None
        ),
    )
    return TrofeuSaida.de_dominio(trofeu)


@roteador.get(
    "/oscar/categorias/{categoria_id}/trofeu",
    summary="Consulta o troféu de uma categoria",
    description="404 enquanto a categoria não tiver sido apurada.",
)
def consultar_trofeu(categoria_id: UUID, contexto: ContextoDep) -> TrofeuSaida:
    categoria = obter_categoria(contexto.categorias, categoria_id)
    trofeu = contexto.trofeus.buscar_por_categoria(categoria.id)
    if trofeu is None:
        raise EntidadeNaoEncontradaError(f"A categoria {categoria.nome} ainda não foi apurada.")
    return TrofeuSaida.de_dominio(trofeu)
