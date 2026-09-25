"""Caso de uso: um membro avalia o filme assistido em uma sessão."""

from __future__ import annotations

from filmes_e_cubos.application.ports.avaliacao_repository import AvaliacaoRepository
from filmes_e_cubos.application.ports.clube_repository import ClubeRepository
from filmes_e_cubos.application.ports.indicacao_repository import IndicacaoRepository
from filmes_e_cubos.application.ports.membro_repository import MembroRepository
from filmes_e_cubos.application.ports.rodada_repository import RodadaRepository
from filmes_e_cubos.application.ports.sessao_repository import SessaoRepository
from filmes_e_cubos.domain.entities.avaliacao import Avaliacao
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.sessao_exibicao import SessaoExibicao
from filmes_e_cubos.domain.exceptions.avaliacao import AvaliacaoDuplicadaError
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import MembroId, SessaoExibicaoId
from filmes_e_cubos.domain.value_objects.nota import Nota


class AvaliarFilme:
    """Registra o resultado de um membro para uma sessão: uma nota, ou,
    sem `nota`, o registro de que o membro cochilou (`DORMINHOCO`).

    Só quem esteve presente avalia. A escala de notas é a do clube dono da
    sessão, deduzido da própria sessão (indicação, rodada, clube) em vez de
    informado por quem chama — assim não há como avaliar com a escala de
    outro clube. A cada avaliação, a média da sessão é refeita e gravada.
    """

    def __init__(
        self,
        avaliacao_repository: AvaliacaoRepository,
        sessao_repository: SessaoRepository,
        membro_repository: MembroRepository,
        indicacao_repository: IndicacaoRepository,
        rodada_repository: RodadaRepository,
        clube_repository: ClubeRepository,
    ) -> None:
        self._avaliacoes = avaliacao_repository
        self._sessoes = sessao_repository
        self._membros = membro_repository
        self._indicacoes = indicacao_repository
        self._rodadas = rodada_repository
        self._clubes = clube_repository

    def executar(
        self,
        *,
        sessao_id: SessaoExibicaoId,
        membro_id: MembroId,
        nota: Nota | None = None,
        comentario: str | None = None,
    ) -> Avaliacao:
        sessao = self._sessoes.buscar_por_id(sessao_id)
        if sessao is None:
            raise EntidadeNaoEncontradaError(f"Sessão {sessao_id} não encontrada.")

        if self._membros.buscar_por_id(membro_id) is None:
            raise EntidadeNaoEncontradaError(f"Membro {membro_id} não encontrado.")

        sessao.verificar_presenca(membro_id)

        if self._avaliacoes.buscar_por_sessao_e_membro(sessao_id, membro_id) is not None:
            raise AvaliacaoDuplicadaError(f"Membro {membro_id} já avaliou a sessão {sessao_id}.")

        clube = self._clube_da_sessao(sessao)
        avaliacao = Avaliacao.criar(
            sessao_id=sessao_id,
            membro_id=membro_id,
            nota=nota,
            escala=clube.configuracao.escala_avaliacao,
            comentario=comentario,
        )
        self._avaliacoes.salvar(avaliacao)

        sessao.recalcular_media(self._avaliacoes.listar_por_sessao(sessao_id))
        self._sessoes.salvar(sessao)
        return avaliacao

    def _clube_da_sessao(self, sessao: SessaoExibicao) -> Clube:
        indicacao = self._indicacoes.buscar_por_id(sessao.indicacao_id)
        if indicacao is None:
            raise EntidadeNaoEncontradaError(
                f"Indicação {sessao.indicacao_id} da sessão {sessao.id} não encontrada."
            )
        rodada = self._rodadas.buscar_por_id(indicacao.rodada_id)
        if rodada is None:
            raise EntidadeNaoEncontradaError(
                f"Rodada {indicacao.rodada_id} da indicação {indicacao.id} não encontrada."
            )
        clube = self._clubes.buscar_por_id(rodada.clube_id)
        if clube is None:
            raise EntidadeNaoEncontradaError(f"Clube {rodada.clube_id} não encontrado.")
        return clube
