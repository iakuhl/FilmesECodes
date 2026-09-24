"""Caso de uso: registrar que o filme sorteado de uma indicação foi assistido."""

from __future__ import annotations

from filmes_e_cubos.application.ports.indicacao_repository import IndicacaoRepository
from filmes_e_cubos.application.ports.relogio_service import RelogioService
from filmes_e_cubos.application.ports.sessao_repository import SessaoRepository
from filmes_e_cubos.domain.entities.sessao_exibicao import SessaoExibicao
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import IndicacaoId, MembroId


class RegistrarSessaoExibicao:
    """Registra a sessão em que o clube assistiu ao filme sorteado.

    A regra "só é possível para uma indicação sorteada" é garantida por
    `Indicacao.marcar_assistida()`, que levanta `TransicaoDeStatusInvalidaError`
    se a indicação não estiver com status `SORTEADA` — não há necessidade
    de replicar essa checagem aqui.
    """

    def __init__(
        self,
        sessao_repository: SessaoRepository,
        indicacao_repository: IndicacaoRepository,
        relogio: RelogioService,
    ) -> None:
        self._sessoes = sessao_repository
        self._indicacoes = indicacao_repository
        self._relogio = relogio

    def executar(
        self, *, indicacao_id: IndicacaoId, membros_presentes: frozenset[MembroId]
    ) -> SessaoExibicao:
        indicacao = self._indicacoes.buscar_por_id(indicacao_id)
        if indicacao is None:
            raise EntidadeNaoEncontradaError(f"Indicação {indicacao_id} não encontrada.")

        indicacao.marcar_assistida()
        self._indicacoes.salvar(indicacao)

        sessao = SessaoExibicao.registrar(
            indicacao_id=indicacao_id,
            data_sessao=self._relogio.hoje(),
            membros_presentes=membros_presentes,
        )
        self._sessoes.salvar(sessao)
        return sessao
