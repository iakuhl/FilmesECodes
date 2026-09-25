"""Apoio aos casos de uso da votação do Óscar: achar a votação em andamento.

Votar e confirmar a cédula começam pelas mesmas conferências — a edição
está em votação, a votação dela existe e ainda não terminou, e quem age
é um dos eleitores —, reunidas aqui para que as duas ações recusem do
mesmo jeito.
"""

from __future__ import annotations

from filmes_e_cubos.application.ports.votacao_oscar_repository import VotacaoOscarRepository
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.entities.votacao_oscar import VotacaoOscar
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import MembroId


def votacao_do_eleitor(
    votacoes: VotacaoOscarRepository, temporada: TemporadaOscar, membro_id: MembroId
) -> VotacaoOscar:
    """A votação em andamento da edição, conferindo que o membro é eleitor nela."""
    temporada.verificar_em_votacao()
    votacao = votacoes.buscar_por_temporada(temporada.id)
    if votacao is None:
        raise EntidadeNaoEncontradaError(f"A edição {temporada.nome} não tem votação iniciada.")
    votacao.verificar_aberta()
    votacao.verificar_eleitor(membro_id)
    return votacao
