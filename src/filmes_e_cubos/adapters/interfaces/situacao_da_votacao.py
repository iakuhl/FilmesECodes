"""A situação da votação do Óscar, do jeito que as telas podem mostrá-la.

O voto é secreto (decisão 26 de docs/PENDENCIAS.md): as telas mostram
quem já confirmou a cédula e em quantas categorias do turno cada
eleitor já votou — nunca em quê, nem o placar, que só sai por e-mail
(decisão 27). A montagem mora aqui, compartilhada pela CLI, pela API e
pela web, para que nenhuma interface mostre mais do que as outras.
"""

from __future__ import annotations

from dataclasses import dataclass

from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.adapters.interfaces.consultas import obter_membro, obter_nomeacao
from filmes_e_cubos.domain.entities.categoria_oscar import CategoriaOscar
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.entities.turno_de_votacao import TurnoDeVotacao
from filmes_e_cubos.domain.entities.votacao_oscar import VotacaoOscar
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError


@dataclass(frozen=True)
class Disputa:
    """Uma categoria em disputa no turno atual, com as candidatas na ordem da cédula."""

    categoria: CategoriaOscar
    turno: TurnoDeVotacao
    candidatas: list[NomeacaoOscar]


@dataclass(frozen=True)
class SituacaoDoEleitor:
    membro: Membro
    categorias_votadas: int
    confirmou: bool


@dataclass(frozen=True)
class SituacaoDaVotacao:
    votacao: VotacaoOscar
    disputas: list[Disputa]
    """Vazia depois que a votação termina."""
    eleitores: list[SituacaoDoEleitor]
    """Em ordem alfabética."""


def situacao_da_votacao(contexto: Contexto, temporada: TemporadaOscar) -> SituacaoDaVotacao:
    votacao = contexto.votacoes.buscar_por_temporada(temporada.id)
    if votacao is None:
        raise EntidadeNaoEncontradaError(f"A edição {temporada.nome} ainda não chegou à votação.")
    disputas = [
        Disputa(
            categoria=categoria,
            turno=turno,
            candidatas=[
                obter_nomeacao(contexto.nomeacoes, nomeacao_id) for nomeacao_id in turno.candidatas
            ],
        )
        for categoria in contexto.categorias.listar_por_temporada(temporada.id)
        for turno in contexto.turnos.listar_por_categoria(categoria.id)
        if turno.aberto
    ]
    cedulas = {
        cedula.membro_id: cedula
        for cedula in contexto.cedulas.listar_por_turno(votacao.id, votacao.turno_atual)
    }
    eleitores = []
    for membro_id in votacao.eleitores:
        cedula = cedulas.get(membro_id)
        eleitores.append(
            SituacaoDoEleitor(
                membro=obter_membro(contexto.membros, membro_id),
                categorias_votadas=len(cedula.categorias_votadas) if cedula is not None else 0,
                confirmou=cedula is not None and cedula.confirmada,
            )
        )
    eleitores.sort(key=lambda eleitor: eleitor.membro.nome.casefold())
    return SituacaoDaVotacao(votacao=votacao, disputas=disputas, eleitores=eleitores)
