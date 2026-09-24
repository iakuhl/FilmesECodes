"""Caso de uso: apurar o vencedor de uma categoria do Óscar e emitir seu troféu."""

from __future__ import annotations

from filmes_e_cubos.application.ports.categoria_oscar_repository import CategoriaOscarRepository
from filmes_e_cubos.application.ports.criterio_apuracao_oscar import CriterioApuracaoOscar
from filmes_e_cubos.application.ports.nomeacao_oscar_repository import NomeacaoOscarRepository
from filmes_e_cubos.application.ports.relogio_service import RelogioService
from filmes_e_cubos.application.ports.trofeu_repository import TrofeuRepository
from filmes_e_cubos.domain.entities.trofeu import Trofeu
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.oscar import (
    CategoriaJaApuradaError,
    NomeacaoInvalidaError,
    VencedorDemocraciaNaoInformadoError,
)
from filmes_e_cubos.domain.value_objects.identificadores import CategoriaOscarId, MembroId


class ApurarCategoriaOscar:
    """Calcula o vencedor de uma categoria e emite o troféu para quem indicou o filme."""

    def __init__(
        self,
        trofeu_repository: TrofeuRepository,
        nomeacao_repository: NomeacaoOscarRepository,
        categoria_repository: CategoriaOscarRepository,
        criterio: CriterioApuracaoOscar,
        relogio: RelogioService,
    ) -> None:
        self._trofeus = trofeu_repository
        self._nomeacoes = nomeacao_repository
        self._categorias = categoria_repository
        self._criterio = criterio
        self._relogio = relogio

    def executar(
        self,
        *,
        categoria_id: CategoriaOscarId,
        membro_vencedor_manual_id: MembroId | None = None,
    ) -> Trofeu:
        if self._categorias.buscar_por_id(categoria_id) is None:
            raise EntidadeNaoEncontradaError(f"Categoria {categoria_id} não encontrada.")
        if self._trofeus.buscar_por_categoria(categoria_id) is not None:
            raise CategoriaJaApuradaError(f"Categoria {categoria_id} já foi apurada.")

        nomeacoes = self._nomeacoes.listar_por_categoria(categoria_id)
        if not nomeacoes:
            raise EntidadeNaoEncontradaError(
                f"Categoria {categoria_id} não tem nenhuma nomeação para apurar."
            )

        vencedora = self._criterio.escolher_vencedora(nomeacoes)
        if vencedora.categoria_id != categoria_id:
            raise NomeacaoInvalidaError(
                f"Nomeação vencedora {vencedora.id} não pertence à categoria {categoria_id}."
            )

        membro_vencedor_id = vencedora.indicado_por_membro_id or membro_vencedor_manual_id
        if membro_vencedor_id is None:
            raise VencedorDemocraciaNaoInformadoError(
                f"Nomeação {vencedora.id} não tem indicador automático (veio de um filme "
                "DEMOCRACIA) — informe membro_vencedor_manual_id com a escolha do grupo."
            )

        trofeu = Trofeu.emitir(
            categoria_id=categoria_id,
            nomeacao_vencedora_id=vencedora.id,
            membro_vencedor_id=membro_vencedor_id,
            data_apuracao=self._relogio.hoje(),
        )
        self._trofeus.salvar(trofeu)
        return trofeu
