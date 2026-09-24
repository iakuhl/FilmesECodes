"""Caso de uso: abrir uma nova rodada de indicações para um clube."""

from __future__ import annotations

from filmes_e_cubos.application.ports.clube_repository import ClubeRepository
from filmes_e_cubos.application.ports.relogio_service import RelogioService
from filmes_e_cubos.application.ports.rodada_repository import RodadaRepository
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.rodada import RodadaJaAbertaError
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId


class AbrirNovaRodada:
    """Inicia uma nova rodada de indicações, desde que não haja outra aberta."""

    def __init__(
        self,
        rodada_repository: RodadaRepository,
        clube_repository: ClubeRepository,
        relogio: RelogioService,
    ) -> None:
        self._rodadas = rodada_repository
        self._clubes = clube_repository
        self._relogio = relogio

    def executar(self, *, clube_id: ClubeId) -> Rodada:
        if self._clubes.buscar_por_id(clube_id) is None:
            raise EntidadeNaoEncontradaError(f"Clube {clube_id} não encontrado.")
        if self._rodadas.buscar_aberta_por_clube(clube_id) is not None:
            raise RodadaJaAbertaError(f"Já existe uma rodada aberta para o clube {clube_id}.")

        numero = self._rodadas.contar_por_clube(clube_id) + 1
        rodada = Rodada.abrir(clube_id=clube_id, numero=numero, data_inicio=self._relogio.hoje())
        self._rodadas.salvar(rodada)
        return rodada
