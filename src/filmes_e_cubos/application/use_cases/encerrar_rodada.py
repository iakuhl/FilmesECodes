"""Caso de uso: encerrar uma rodada quando todas as indicações tiverem sido assistidas."""

from __future__ import annotations

from filmes_e_cubos.application.ports.indicacao_repository import IndicacaoRepository
from filmes_e_cubos.application.ports.relogio_service import RelogioService
from filmes_e_cubos.application.ports.rodada_repository import RodadaRepository
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.rodada import RodadaNaoEncerravelError
from filmes_e_cubos.domain.value_objects.identificadores import RodadaId
from filmes_e_cubos.domain.value_objects.status import StatusIndicacao


class EncerrarRodada:
    """Encerra a rodada, verificando que todas as suas indicações foram assistidas."""

    def __init__(
        self,
        rodada_repository: RodadaRepository,
        indicacao_repository: IndicacaoRepository,
        relogio: RelogioService,
    ) -> None:
        self._rodadas = rodada_repository
        self._indicacoes = indicacao_repository
        self._relogio = relogio

    def executar(self, *, rodada_id: RodadaId) -> Rodada:
        rodada = self._rodadas.buscar_por_id(rodada_id)
        if rodada is None:
            raise EntidadeNaoEncontradaError(f"Rodada {rodada_id} não encontrada.")

        indicacoes = self._indicacoes.listar_por_rodada(rodada_id)
        todas_assistidas = bool(indicacoes) and all(
            indicacao.status is StatusIndicacao.ASSISTIDA for indicacao in indicacoes
        )
        if not todas_assistidas:
            raise RodadaNaoEncerravelError(
                f"Rodada {rodada_id} tem indicações ainda não assistidas."
            )

        rodada.encerrar(data_encerramento=self._relogio.hoje())
        self._rodadas.salvar(rodada)
        return rodada
