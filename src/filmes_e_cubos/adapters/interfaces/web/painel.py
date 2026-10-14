"""O painel do clube: o que está acontecendo agora, montado para a página.

Listagem de leitura (ADR 7): vai direto aos repositórios. Junta a rodada
aberta com as suas indicações (filme, quem indicou e a sessão, se já
houve), os membros ativos e a edição do Óscar do ano.
"""

from __future__ import annotations

from dataclasses import dataclass

from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.domain.entities.avaliacao import Avaliacao
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.filme import Filme
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.entities.sessao_exibicao import SessaoExibicao
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar


@dataclass(frozen=True)
class IndicacaoNaPagina:
    """Uma indicação com o que a página mostra dela."""

    indicacao: Indicacao
    filme: Filme | None
    membro: Membro | None
    """`None` numa indicação democracia, que não tem quem indicou."""
    sessao: SessaoExibicao | None


@dataclass(frozen=True)
class Painel:
    rodada: Rodada | None
    indicacoes: list[IndicacaoNaPagina]
    membros_ativos: list[Membro]
    temporada_do_ano: TemporadaOscar | None
    filmes: list[Filme]
    """O catálogo, para os formulários de indicação."""


def indicacoes_da_rodada(contexto: Contexto, rodada: Rodada) -> list[IndicacaoNaPagina]:
    return [
        IndicacaoNaPagina(
            indicacao=indicacao,
            filme=contexto.filmes.buscar_por_id(indicacao.filme_id),
            membro=(
                contexto.membros.buscar_por_id(indicacao.membro_id)
                if indicacao.membro_id is not None
                else None
            ),
            sessao=contexto.sessoes.buscar_por_indicacao(indicacao.id),
        )
        for indicacao in contexto.indicacoes.listar_por_rodada(rodada.id)
    ]


def montar_painel(contexto: Contexto, clube: Clube) -> Painel:
    rodada = contexto.rodadas.buscar_aberta_por_clube(clube.id)
    return Painel(
        rodada=rodada,
        indicacoes=indicacoes_da_rodada(contexto, rodada) if rodada is not None else [],
        membros_ativos=contexto.membros.listar_ativos_por_clube(clube.id),
        temporada_do_ano=contexto.temporadas.buscar_por_clube_e_ano(
            clube.id, contexto.relogio.hoje().year
        ),
        filmes=contexto.filmes.listar_todos() if rodada is not None else [],
    )


@dataclass(frozen=True)
class AvaliacaoNaPagina:
    avaliacao: Avaliacao
    membro: Membro | None


@dataclass(frozen=True)
class SessaoNaPagina:
    sessao: SessaoExibicao
    indicacao: Indicacao | None
    filme: Filme | None
    indicado_por: Membro | None
    presentes: list[Membro]
    avaliacoes: list[AvaliacaoNaPagina]
    faltam_avaliar: list[Membro]
    """Os presentes que ainda não avaliaram — os únicos que podem (decisão 4)."""


def sessao_na_pagina(contexto: Contexto, sessao: SessaoExibicao) -> SessaoNaPagina:
    indicacao = contexto.indicacoes.buscar_por_id(sessao.indicacao_id)
    presentes = sorted(
        (
            membro
            for membro_id in sessao.membros_presentes
            if (membro := contexto.membros.buscar_por_id(membro_id)) is not None
        ),
        key=lambda membro: membro.nome.casefold(),
    )
    avaliacoes = [
        AvaliacaoNaPagina(avaliacao, contexto.membros.buscar_por_id(avaliacao.membro_id))
        for avaliacao in contexto.avaliacoes.listar_por_sessao(sessao.id)
    ]
    ja_avaliaram = {item.avaliacao.membro_id for item in avaliacoes}
    return SessaoNaPagina(
        sessao=sessao,
        indicacao=indicacao,
        filme=contexto.filmes.buscar_por_id(indicacao.filme_id) if indicacao else None,
        indicado_por=(
            contexto.membros.buscar_por_id(indicacao.membro_id)
            if indicacao is not None and indicacao.membro_id is not None
            else None
        ),
        presentes=presentes,
        avaliacoes=avaliacoes,
        faltam_avaliar=[membro for membro in presentes if membro.id not in ja_avaliaram],
    )
