"""Caso de uso: sortear uma indicação pendente da rodada corrente."""

from __future__ import annotations

from filmes_e_cubos.application.ports.indicacao_repository import IndicacaoRepository
from filmes_e_cubos.application.ports.relogio_service import RelogioService
from filmes_e_cubos.application.ports.rodada_repository import RodadaRepository
from filmes_e_cubos.application.ports.sorteador_service import SorteadorService
from filmes_e_cubos.application.ports.sorteio_repository import SorteioRepository
from filmes_e_cubos.domain.entities.sorteio import Sorteio
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.rodada import RodadaJaEncerradaError
from filmes_e_cubos.domain.exceptions.sorteio import (
    IndicacaoNaoElegivelParaSorteioError,
    NenhumaIndicacaoElegivelError,
)
from filmes_e_cubos.domain.value_objects.identificadores import RodadaId
from filmes_e_cubos.domain.value_objects.status import StatusIndicacao

_METODO_PADRAO = "sorteio_aleatorio_uniforme"


class RealizarSorteio:
    """Sorteia, entre as indicações pendentes da rodada, qual será assistida."""

    def __init__(
        self,
        indicacao_repository: IndicacaoRepository,
        rodada_repository: RodadaRepository,
        sorteio_repository: SorteioRepository,
        sorteador: SorteadorService,
        relogio: RelogioService,
    ) -> None:
        self._indicacoes = indicacao_repository
        self._rodadas = rodada_repository
        self._sorteios = sorteio_repository
        self._sorteador = sorteador
        self._relogio = relogio

    def executar(self, *, rodada_id: RodadaId) -> Sorteio:
        rodada = self._rodadas.buscar_por_id(rodada_id)
        if rodada is None:
            raise EntidadeNaoEncontradaError(f"Rodada {rodada_id} não encontrada.")
        if not rodada.esta_aberta:
            raise RodadaJaEncerradaError(f"Rodada {rodada_id} não está aberta.")

        indicacoes_pendentes = [
            indicacao
            for indicacao in self._indicacoes.listar_por_rodada(rodada_id)
            if indicacao.status is StatusIndicacao.PENDENTE
        ]
        if not indicacoes_pendentes:
            raise NenhumaIndicacaoElegivelError(
                f"Rodada {rodada_id} não tem indicações pendentes para sortear."
            )

        candidatos = [indicacao.id for indicacao in indicacoes_pendentes]
        sorteada_id = self._sorteador.sortear(candidatos)
        if sorteada_id not in candidatos:
            raise IndicacaoNaoElegivelParaSorteioError(
                f"Indicação sorteada {sorteada_id} não está entre as candidatas."
            )

        indicacao_sorteada = next(
            indicacao for indicacao in indicacoes_pendentes if indicacao.id == sorteada_id
        )
        indicacao_sorteada.marcar_sorteada()
        self._indicacoes.salvar(indicacao_sorteada)

        sorteio = Sorteio.registrar(
            rodada_id=rodada_id,
            indicacao_sorteada_id=sorteada_id,
            data_sorteio=self._relogio.agora(),
            metodo=_METODO_PADRAO,
        )
        self._sorteios.salvar(sorteio)
        return sorteio
