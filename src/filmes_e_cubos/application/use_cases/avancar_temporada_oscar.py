"""Caso de uso: levar uma edição do Óscar à fase seguinte do seu ciclo."""

from __future__ import annotations

from filmes_e_cubos.application.ports.categoria_oscar_repository import CategoriaOscarRepository
from filmes_e_cubos.application.ports.membro_repository import MembroRepository
from filmes_e_cubos.application.ports.nomeacao_oscar_repository import NomeacaoOscarRepository
from filmes_e_cubos.application.ports.relogio_service import RelogioService
from filmes_e_cubos.application.ports.temporada_oscar_repository import TemporadaOscarRepository
from filmes_e_cubos.application.ports.trofeu_repository import TrofeuRepository
from filmes_e_cubos.application.ports.turno_de_votacao_repository import (
    TurnoDeVotacaoRepository,
)
from filmes_e_cubos.application.ports.votacao_oscar_repository import VotacaoOscarRepository
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.entities.turno_de_votacao import TurnoDeVotacao
from filmes_e_cubos.domain.entities.votacao_oscar import VotacaoOscar
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.oscar import (
    TemporadaIncompletaError,
    TemporadaOscarInvalidaError,
)
from filmes_e_cubos.domain.value_objects.identificadores import TemporadaOscarId
from filmes_e_cubos.domain.value_objects.status import StatusTemporadaOscar


class AvancarTemporadaOscar:
    """Avança a edição um passo, conferindo o que a fase atual precisa ter cumprido.

    O avanço é sempre manual e de um passo por vez (decisão 7 de
    docs/PENDENCIAS.md). Ir à votação exige ao menos uma categoria e,
    em cada uma, exatamente o número de nomeações da edição; ir a
    *apurada* exige que toda categoria tenha resultado.

    Entrar em votação inicia a votação da edição: os eleitores são os
    membros ativos do clube naquele momento (decisão 23), e cada
    categoria abre o 1º turno com todas as suas nomeações, na ordem em
    que foram feitas.
    """

    def __init__(
        self,
        temporada_repository: TemporadaOscarRepository,
        categoria_repository: CategoriaOscarRepository,
        nomeacao_repository: NomeacaoOscarRepository,
        trofeu_repository: TrofeuRepository,
        membro_repository: MembroRepository,
        votacao_repository: VotacaoOscarRepository,
        turno_repository: TurnoDeVotacaoRepository,
        relogio: RelogioService,
    ) -> None:
        self._temporadas = temporada_repository
        self._categorias = categoria_repository
        self._nomeacoes = nomeacao_repository
        self._trofeus = trofeu_repository
        self._membros = membro_repository
        self._votacoes = votacao_repository
        self._turnos = turno_repository
        self._relogio = relogio

    def executar(self, *, temporada_id: TemporadaOscarId) -> TemporadaOscar:
        temporada = self._temporadas.buscar_por_id(temporada_id)
        if temporada is None:
            raise EntidadeNaoEncontradaError(f"Temporada {temporada_id} não encontrada.")

        proximo = temporada.proximo_status
        if proximo is None:
            raise TemporadaOscarInvalidaError(f"A edição {temporada.nome} já está encerrada.")
        # Tudo é conferido e montado antes de gravar qualquer coisa.
        votacao: VotacaoOscar | None = None
        turnos: list[TurnoDeVotacao] = []
        if proximo is StatusTemporadaOscar.EM_VOTACAO:
            turnos = self._exigir_nomeacoes_completas(temporada)
            ativos = self._membros.listar_ativos_por_clube(temporada.clube_id)
            votacao = VotacaoOscar.iniciar(
                temporada_id=temporada.id,
                eleitores=[membro.id for membro in ativos],
                momento=self._relogio.agora(),
            )
        if proximo is StatusTemporadaOscar.APURADA:
            self._exigir_categorias_apuradas(temporada)

        temporada.avancar_para(proximo)
        if votacao is not None:
            self._votacoes.salvar(votacao)
        for turno in turnos:
            self._turnos.salvar(turno)
        self._temporadas.salvar(temporada)
        return temporada

    def _exigir_nomeacoes_completas(self, temporada: TemporadaOscar) -> list[TurnoDeVotacao]:
        """Confere as nomeações e já devolve o 1º turno de cada categoria."""
        categorias = self._categorias.listar_por_temporada(temporada.id)
        if not categorias:
            raise TemporadaIncompletaError(
                f"A edição {temporada.nome} não tem nenhuma categoria para votar."
            )
        nomeacoes = {
            categoria.id: self._nomeacoes.listar_por_categoria(categoria.id)
            for categoria in categorias
        }
        incompletas = [
            f"{categoria.nome} ({quantas}/{temporada.nomeacoes_por_categoria})"
            for categoria in categorias
            if (quantas := len(nomeacoes[categoria.id])) != temporada.nomeacoes_por_categoria
        ]
        if incompletas:
            raise TemporadaIncompletaError(
                "Toda categoria precisa de exatamente "
                f"{temporada.nomeacoes_por_categoria} nomeações antes da votação; "
                f"faltam em: {', '.join(incompletas)}."
            )
        return [
            TurnoDeVotacao.abrir_primeiro(
                categoria_id=categoria.id,
                candidatas=[nomeacao.id for nomeacao in nomeacoes[categoria.id]],
            )
            for categoria in categorias
        ]

    def _exigir_categorias_apuradas(self, temporada: TemporadaOscar) -> None:
        pendentes = [
            categoria.nome
            for categoria in self._categorias.listar_por_temporada(temporada.id)
            if self._trofeus.buscar_por_categoria(categoria.id) is None
        ]
        if pendentes:
            raise TemporadaIncompletaError(
                f"Ainda há categorias sem resultado: {', '.join(pendentes)}."
            )
