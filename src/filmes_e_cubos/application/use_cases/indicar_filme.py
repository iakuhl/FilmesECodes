"""Caso de uso: registrar a indicação de um filme por um membro na rodada corrente."""

from __future__ import annotations

from filmes_e_cubos.application.ports.clube_repository import ClubeRepository
from filmes_e_cubos.application.ports.filme_repository import FilmeRepository
from filmes_e_cubos.application.ports.indicacao_repository import IndicacaoRepository
from filmes_e_cubos.application.ports.membro_repository import MembroRepository
from filmes_e_cubos.application.ports.relogio_service import RelogioService
from filmes_e_cubos.application.ports.rodada_repository import RodadaRepository
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.indicacao import IndicacaoDuplicadaError
from filmes_e_cubos.domain.exceptions.membro import MembroInativoError
from filmes_e_cubos.domain.exceptions.rodada import RodadaJaEncerradaError, RodadaLotadaError
from filmes_e_cubos.domain.value_objects.identificadores import FilmeId, MembroId, RodadaId
from filmes_e_cubos.domain.value_objects.tipo_indicacao import TipoIndicacao


class IndicarFilme:
    """Registra a indicação de um filme por um membro ativo na rodada aberta."""

    def __init__(
        self,
        indicacao_repository: IndicacaoRepository,
        rodada_repository: RodadaRepository,
        membro_repository: MembroRepository,
        filme_repository: FilmeRepository,
        clube_repository: ClubeRepository,
        relogio: RelogioService,
    ) -> None:
        self._indicacoes = indicacao_repository
        self._rodadas = rodada_repository
        self._membros = membro_repository
        self._filmes = filme_repository
        self._clubes = clube_repository
        self._relogio = relogio

    def executar(self, *, rodada_id: RodadaId, membro_id: MembroId, filme_id: FilmeId) -> Indicacao:
        rodada = self._rodadas.buscar_por_id(rodada_id)
        if rodada is None:
            raise EntidadeNaoEncontradaError(f"Rodada {rodada_id} não encontrada.")
        if not rodada.esta_aberta:
            raise RodadaJaEncerradaError(f"Rodada {rodada_id} não está aberta.")

        membro = self._membros.buscar_por_id(membro_id)
        if membro is None:
            raise EntidadeNaoEncontradaError(f"Membro {membro_id} não encontrado.")
        if not membro.ativo:
            raise MembroInativoError(f"Membro {membro_id} está inativo.")

        if self._filmes.buscar_por_id(filme_id) is None:
            raise EntidadeNaoEncontradaError(f"Filme {filme_id} não encontrado.")

        indicacoes_normais_da_rodada = [
            indicacao
            for indicacao in self._indicacoes.listar_por_rodada(rodada_id)
            if indicacao.tipo is TipoIndicacao.NORMAL
        ]
        if any(indicacao.membro_id == membro_id for indicacao in indicacoes_normais_da_rodada):
            raise IndicacaoDuplicadaError(f"Membro {membro_id} já indicou um filme nesta rodada.")

        clube = self._clubes.buscar_por_id(rodada.clube_id)
        if clube is None:
            raise EntidadeNaoEncontradaError(f"Clube {rodada.clube_id} não encontrado.")
        if len(indicacoes_normais_da_rodada) >= clube.configuracao.tamanho_rodada:
            raise RodadaLotadaError(f"Rodada {rodada_id} já atingiu o tamanho máximo.")

        indicacao = Indicacao.criar(
            rodada_id=rodada_id,
            membro_id=membro_id,
            filme_id=filme_id,
            data_indicacao=self._relogio.hoje(),
        )
        self._indicacoes.salvar(indicacao)
        return indicacao
