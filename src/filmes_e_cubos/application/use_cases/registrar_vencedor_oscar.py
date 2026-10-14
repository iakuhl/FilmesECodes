"""Caso de uso: registrar, depois da cerimônia, o vencedor de uma categoria do Óscar."""

from __future__ import annotations

from filmes_e_cubos.application.ports.categoria_oscar_repository import CategoriaOscarRepository
from filmes_e_cubos.application.ports.membro_repository import MembroRepository
from filmes_e_cubos.application.ports.nomeacao_oscar_repository import NomeacaoOscarRepository
from filmes_e_cubos.application.ports.relogio_service import RelogioService
from filmes_e_cubos.application.ports.temporada_oscar_repository import TemporadaOscarRepository
from filmes_e_cubos.application.ports.trofeu_repository import TrofeuRepository
from filmes_e_cubos.application.ports.votacao_oscar_repository import VotacaoOscarRepository
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.entities.trofeu import Trofeu
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.oscar import (
    CategoriaJaApuradaError,
    EscolhaDoGrupoNecessariaError,
    MembroDeOutroClubeError,
    NomeacaoInvalidaError,
    VotacaoEmAndamentoError,
)
from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    MembroId,
    NomeacaoOscarId,
)


class RegistrarVencedorOscar:
    """Registra quem levou o troféu de uma categoria (decisão 29 de docs/PENDENCIAS.md).

    A apuração acontece fora do sistema, com o placar que foi por e-mail
    (decisão 27): depois da cerimônia, quem administra informa a nomeação
    vencedora — o troféu vai para quem a indicou — ou, numa vitória de
    filme democracia ou num empate absoluto (sem nomeação), o membro que o
    grupo escolheu. O sistema não confere a escolha com o placar.

    Só com a votação terminada e a edição ainda em votação; a edição fica
    *apurada* quando toda categoria tiver vencedor. Uma vez registrado, o
    vencedor da categoria não muda (interpretação 14).
    """

    def __init__(
        self,
        trofeu_repository: TrofeuRepository,
        categoria_repository: CategoriaOscarRepository,
        nomeacao_repository: NomeacaoOscarRepository,
        temporada_repository: TemporadaOscarRepository,
        votacao_repository: VotacaoOscarRepository,
        membro_repository: MembroRepository,
        relogio: RelogioService,
    ) -> None:
        self._trofeus = trofeu_repository
        self._categorias = categoria_repository
        self._nomeacoes = nomeacao_repository
        self._temporadas = temporada_repository
        self._votacoes = votacao_repository
        self._membros = membro_repository
        self._relogio = relogio

    def executar(
        self,
        *,
        categoria_id: CategoriaOscarId,
        nomeacao_id: NomeacaoOscarId | None = None,
        membro_escolhido_id: MembroId | None = None,
    ) -> Trofeu:
        categoria = self._categorias.buscar_por_id(categoria_id)
        if categoria is None:
            raise EntidadeNaoEncontradaError(f"Categoria {categoria_id} não encontrada.")
        temporada = self._temporadas.buscar_por_id(categoria.temporada_id)
        if temporada is None:
            raise EntidadeNaoEncontradaError(f"Temporada {categoria.temporada_id} não encontrada.")
        temporada.verificar_em_votacao()
        votacao = self._votacoes.buscar_por_temporada(temporada.id)
        if votacao is None or not votacao.encerrada:
            raise VotacaoEmAndamentoError(
                f"A votação de {temporada.nome} ainda não terminou: o vencedor é registrado "
                "depois dela."
            )
        if self._trofeus.buscar_por_categoria(categoria.id) is not None:
            raise CategoriaJaApuradaError(f"A categoria {categoria.nome} já tem vencedor.")

        indicador: MembroId | None = None
        if nomeacao_id is not None:
            nomeacao = self._nomeacoes.buscar_por_id(nomeacao_id)
            if nomeacao is None or nomeacao.categoria_id != categoria.id:
                raise NomeacaoInvalidaError(
                    f"A nomeação {nomeacao_id} não concorre na categoria {categoria.nome}."
                )
            indicador = nomeacao.indicado_por_membro_id
        vencedor = indicador or membro_escolhido_id
        if vencedor is None:
            raise EscolhaDoGrupoNecessariaError(
                "Sem nomeação vencedora (empate absoluto), informe o membro escolhido pelo grupo."
                if nomeacao_id is None
                else "A nomeação vencedora veio de uma sessão democracia: informe o membro "
                "escolhido pelo grupo."
            )
        if indicador is None:
            self._conferir_do_clube(vencedor, temporada)

        trofeu = Trofeu.emitir(
            categoria_id=categoria.id,
            nomeacao_vencedora_id=nomeacao_id,
            membro_vencedor_id=vencedor,
            data_apuracao=self._relogio.hoje(),
        )
        self._trofeus.salvar(trofeu)
        return trofeu

    def _conferir_do_clube(self, membro_id: MembroId, temporada: TemporadaOscar) -> None:
        """O membro escolhido pelo grupo precisa ser do clube, ativo ou não (interpretação 3)."""
        membro = self._membros.buscar_por_id(membro_id)
        if membro is None:
            raise EntidadeNaoEncontradaError(f"Membro {membro_id} não encontrado.")
        if membro.clube_id != temporada.clube_id:
            raise MembroDeOutroClubeError(f"{membro.nome} não é membro do clube desta edição.")
