"""Caso de uso: confirmar a cédula de um eleitor e, com a última, encerrar o turno."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from filmes_e_cubos.application.ports.categoria_oscar_repository import CategoriaOscarRepository
from filmes_e_cubos.application.ports.cedula_repository import CedulaRepository
from filmes_e_cubos.application.ports.relogio_service import RelogioService
from filmes_e_cubos.application.ports.temporada_oscar_repository import TemporadaOscarRepository
from filmes_e_cubos.application.ports.turno_de_votacao_repository import (
    TurnoDeVotacaoRepository,
)
from filmes_e_cubos.application.ports.votacao_oscar_repository import VotacaoOscarRepository
from filmes_e_cubos.application.use_cases._votacao import votacao_do_eleitor
from filmes_e_cubos.domain.entities.categoria_oscar import CategoriaOscar
from filmes_e_cubos.domain.entities.cedula import Cedula
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.entities.turno_de_votacao import TurnoDeVotacao
from filmes_e_cubos.domain.entities.votacao_oscar import VotacaoOscar
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.oscar import CedulaIncompletaError
from filmes_e_cubos.domain.value_objects.identificadores import MembroId, TemporadaOscarId


@dataclass(frozen=True)
class ResultadoDaConfirmacao:
    """O estado da votação depois da confirmação.

    `turno_encerrado` diz se esta foi a última cédula do turno. Nesse
    caso, `votacao.encerrada` diz se a votação terminou ou se começou o
    turno seguinte (`votacao.turno_atual`), com as categorias empatadas.
    """

    votacao: VotacaoOscar
    turno_encerrado: bool
    pendentes: frozenset[MembroId]


class ConfirmarCedula:
    """Trava a cédula do eleitor no turno atual e, se era a última, encerra o turno.

    A cédula só é confirmada com voto em todas as categorias do turno; a
    recusa diz quais faltam. Confirmada, não muda mais (decisão 25 de
    docs/PENDENCIAS.md).

    Encerrar o turno é apurar cada categoria sem mostrar nada a ninguém
    (decisões 26 e 27): as que empataram no topo ganham um turno seguinte
    (decisão 28) e as demais estão decididas. Sem turno novo, a votação
    termina, e o placar pode ser enviado.
    """

    def __init__(
        self,
        temporada_repository: TemporadaOscarRepository,
        categoria_repository: CategoriaOscarRepository,
        votacao_repository: VotacaoOscarRepository,
        turno_repository: TurnoDeVotacaoRepository,
        cedula_repository: CedulaRepository,
        relogio: RelogioService,
    ) -> None:
        self._temporadas = temporada_repository
        self._categorias = categoria_repository
        self._votacoes = votacao_repository
        self._turnos = turno_repository
        self._cedulas = cedula_repository
        self._relogio = relogio

    def executar(
        self, *, temporada_id: TemporadaOscarId, membro_id: MembroId
    ) -> ResultadoDaConfirmacao:
        temporada = self._temporadas.buscar_por_id(temporada_id)
        if temporada is None:
            raise EntidadeNaoEncontradaError(f"Temporada {temporada_id} não encontrada.")
        votacao = votacao_do_eleitor(self._votacoes, temporada, membro_id)
        em_disputa = self._em_disputa(temporada)

        cedula = self._cedulas.buscar(votacao.id, votacao.turno_atual, membro_id)
        if cedula is None:
            cedula = Cedula.criar(
                votacao_id=votacao.id, turno=votacao.turno_atual, membro_id=membro_id
            )
        cedula.verificar_aberta()
        faltando = [
            categoria.nome
            for categoria, _ in em_disputa
            if categoria.id not in cedula.categorias_votadas
        ]
        if faltando:
            raise CedulaIncompletaError(f"Falta votar em: {', '.join(faltando)}.")
        momento = self._relogio.agora()
        cedula.confirmar([categoria.id for categoria, _ in em_disputa], momento=momento)
        self._cedulas.salvar(cedula)

        confirmadas = [
            outra
            for outra in self._cedulas.listar_por_turno(votacao.id, votacao.turno_atual)
            if outra.confirmada and outra.membro_id in votacao.eleitores
        ]
        pendentes = votacao.pendentes(outra.membro_id for outra in confirmadas)
        if pendentes:
            return ResultadoDaConfirmacao(votacao, turno_encerrado=False, pendentes=pendentes)
        self._encerrar_turno(votacao, em_disputa, confirmadas, momento)
        return ResultadoDaConfirmacao(votacao, turno_encerrado=True, pendentes=frozenset())

    def _em_disputa(self, temporada: TemporadaOscar) -> list[tuple[CategoriaOscar, TurnoDeVotacao]]:
        """As categorias do turno atual, cada uma com o seu turno aberto."""
        em_disputa = []
        for categoria in self._categorias.listar_por_temporada(temporada.id):
            for turno in self._turnos.listar_por_categoria(categoria.id):
                if turno.aberto:
                    em_disputa.append((categoria, turno))
        return em_disputa

    def _encerrar_turno(
        self,
        votacao: VotacaoOscar,
        em_disputa: list[tuple[CategoriaOscar, TurnoDeVotacao]],
        cedulas: list[Cedula],
        momento: datetime,
    ) -> None:
        seguintes = []
        for categoria, turno in em_disputa:
            seguinte = turno.apurar(
                (cedula.escolhas[categoria.id] for cedula in cedulas), momento=momento
            )
            self._turnos.salvar(turno)
            if seguinte is not None:
                seguintes.append(seguinte)
        for turno in seguintes:
            self._turnos.salvar(turno)
        if seguintes:
            votacao.abrir_turno_seguinte()
        else:
            votacao.encerrar(momento)
        self._votacoes.salvar(votacao)
