"""Caso de uso: um membro avalia o filme assistido em uma sessão."""

from __future__ import annotations

from filmes_e_cubos.application.ports.avaliacao_repository import AvaliacaoRepository
from filmes_e_cubos.application.ports.clube_repository import ClubeRepository
from filmes_e_cubos.application.ports.membro_repository import MembroRepository
from filmes_e_cubos.application.ports.sessao_repository import SessaoRepository
from filmes_e_cubos.domain.entities.avaliacao import Avaliacao
from filmes_e_cubos.domain.exceptions.avaliacao import AvaliacaoDuplicadaError
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId, MembroId, SessaoExibicaoId
from filmes_e_cubos.domain.value_objects.nota import Nota


class AvaliarFilme:
    """Registra a nota (e comentário opcional) de um membro para uma sessão."""

    def __init__(
        self,
        avaliacao_repository: AvaliacaoRepository,
        sessao_repository: SessaoRepository,
        membro_repository: MembroRepository,
        clube_repository: ClubeRepository,
    ) -> None:
        self._avaliacoes = avaliacao_repository
        self._sessoes = sessao_repository
        self._membros = membro_repository
        self._clubes = clube_repository

    def executar(
        self,
        *,
        sessao_id: SessaoExibicaoId,
        membro_id: MembroId,
        clube_id: ClubeId,
        nota: Nota,
        comentario: str | None = None,
    ) -> Avaliacao:
        if self._sessoes.buscar_por_id(sessao_id) is None:
            raise EntidadeNaoEncontradaError(f"Sessão {sessao_id} não encontrada.")

        if self._membros.buscar_por_id(membro_id) is None:
            raise EntidadeNaoEncontradaError(f"Membro {membro_id} não encontrado.")

        if self._avaliacoes.buscar_por_sessao_e_membro(sessao_id, membro_id) is not None:
            raise AvaliacaoDuplicadaError(f"Membro {membro_id} já avaliou a sessão {sessao_id}.")

        clube = self._clubes.buscar_por_id(clube_id)
        if clube is None:
            raise EntidadeNaoEncontradaError(f"Clube {clube_id} não encontrado.")

        avaliacao = Avaliacao.criar(
            sessao_id=sessao_id,
            membro_id=membro_id,
            nota=nota,
            escala=clube.configuracao.escala_avaliacao,
            comentario=comentario,
        )
        self._avaliacoes.salvar(avaliacao)
        return avaliacao
