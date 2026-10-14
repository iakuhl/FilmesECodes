"""O Óscar montado para as páginas: edições, categorias, nomeações e cédulas.

Listagens de leitura (ADR 7), direto dos repositórios. O voto é secreto
(decisão 26 de docs/PENDENCIAS.md): a cédula de um eleitor aparece só
como "já votou nesta categoria" — nunca as escolhas, nem o placar.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.adapters.interfaces.consultas import obter_categoria, obter_temporada
from filmes_e_cubos.domain.entities.categoria_oscar import CategoriaOscar
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.filme import Filme
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.entities.trofeu import Trofeu
from filmes_e_cubos.domain.entities.votacao_oscar import VotacaoOscar
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.status import StatusIndicacao


def temporada_do_clube(contexto: Contexto, clube: Clube, temporada_id: UUID) -> TemporadaOscar:
    temporada = obter_temporada(contexto.temporadas, temporada_id)
    if temporada.clube_id != clube.id:
        raise EntidadeNaoEncontradaError(f"Edição {temporada_id} não encontrada em {clube.nome}.")
    return temporada


def categoria_da_temporada(
    contexto: Contexto, temporada: TemporadaOscar, categoria_id: UUID
) -> CategoriaOscar:
    categoria = obter_categoria(contexto.categorias, categoria_id)
    if categoria.temporada_id != temporada.id:
        raise EntidadeNaoEncontradaError(f"Categoria {categoria_id} não encontrada nesta edição.")
    return categoria


@dataclass(frozen=True)
class NomeacaoNaPagina:
    nomeacao: NomeacaoOscar
    filme: Filme | None
    indicado_por: Membro | None
    """`None` quando o filme veio de uma sessão democracia."""


@dataclass(frozen=True)
class CategoriaNaPagina:
    categoria: CategoriaOscar
    nomeacoes: list[NomeacaoNaPagina]
    trofeu: Trofeu | None


@dataclass(frozen=True)
class EdicaoNaPagina:
    temporada: TemporadaOscar
    categorias: list[CategoriaNaPagina]
    votacao: VotacaoOscar | None


def nomeacao_na_pagina(contexto: Contexto, nomeacao: NomeacaoOscar) -> NomeacaoNaPagina:
    indicador = nomeacao.indicado_por_membro_id
    return NomeacaoNaPagina(
        nomeacao=nomeacao,
        filme=contexto.filmes.buscar_por_id(nomeacao.filme_id),
        indicado_por=contexto.membros.buscar_por_id(indicador) if indicador else None,
    )


def categoria_na_pagina(contexto: Contexto, categoria: CategoriaOscar) -> CategoriaNaPagina:
    return CategoriaNaPagina(
        categoria=categoria,
        nomeacoes=[
            nomeacao_na_pagina(contexto, nomeacao)
            for nomeacao in contexto.nomeacoes.listar_por_categoria(categoria.id)
        ],
        trofeu=contexto.trofeus.buscar_por_categoria(categoria.id),
    )


def edicao_na_pagina(contexto: Contexto, temporada: TemporadaOscar) -> EdicaoNaPagina:
    return EdicaoNaPagina(
        temporada=temporada,
        categorias=[
            categoria_na_pagina(contexto, categoria)
            for categoria in contexto.categorias.listar_por_temporada(temporada.id)
        ],
        votacao=contexto.votacoes.buscar_por_temporada(temporada.id),
    )


def filmes_assistidos_no_ano(contexto: Contexto, clube: Clube, ano: int) -> list[Filme]:
    """Os filmes que o clube assistiu no ano — os que podem ser nomeados (decisão do domínio:
    só concorrem filmes assistidos pelo próprio clube no ano da edição).
    """
    filmes: dict[UUID, Filme] = {}
    for rodada in contexto.rodadas.listar_por_clube(clube.id):
        for indicacao in contexto.indicacoes.listar_por_rodada(rodada.id):
            if indicacao.status is not StatusIndicacao.ASSISTIDA or indicacao.filme_id in filmes:
                continue
            sessao = contexto.sessoes.buscar_por_indicacao(indicacao.id)
            filme = contexto.filmes.buscar_por_id(indicacao.filme_id)
            if sessao is not None and sessao.data_sessao.year == ano and filme is not None:
                filmes[filme.id] = filme
    return sorted(filmes.values(), key=lambda filme: filme.titulo.casefold())
