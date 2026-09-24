"""Convenções compartilhadas pelas interfaces (CLI, API HTTP e web).

Algumas informações o usuário não precisa informar, porque a interface
consegue deduzi-las de um jeito razoável: o nome padrão de uma edição do
Óscar, quem estava presente numa sessão (todos os membros ativos do
clube) e a qual clube uma sessão pertence (para saber qual escala de
notas vale).

Nada aqui é regra de negócio — os casos de uso continuam recebendo tudo
explicitamente. São conveniências de interface, reunidas em um módulo só
para que as interfaces se comportem igual. As funções recebem apenas os
ports de que precisam, e só leem: nunca alteram estado.
"""

from __future__ import annotations

from filmes_e_cubos.application.ports.indicacao_repository import IndicacaoRepository
from filmes_e_cubos.application.ports.membro_repository import MembroRepository
from filmes_e_cubos.application.ports.rodada_repository import RodadaRepository
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.entities.sessao_exibicao import SessaoExibicao
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId, MembroId


def nome_padrao_da_temporada(nome_do_clube: str, ano: int) -> str:
    """Nome de uma edição do Óscar quando quem a abre não escolhe outro."""
    return f"Óscar do {nome_do_clube} {ano}"


def presenca_padrao(
    indicacao: Indicacao, rodadas: RodadaRepository, membros: MembroRepository
) -> frozenset[MembroId]:
    """Presentes de uma sessão quando ninguém os informa: todos os membros
    ativos do clube dono da rodada da indicação.
    """
    rodada = _rodada_da_indicacao(indicacao, rodadas)
    return frozenset(membro.id for membro in membros.listar_ativos_por_clube(rodada.clube_id))


def clube_da_sessao(
    sessao: SessaoExibicao, indicacoes: IndicacaoRepository, rodadas: RodadaRepository
) -> ClubeId:
    """O clube a que a sessão pertence: o dono da rodada em que o filme foi indicado."""
    indicacao = indicacoes.buscar_por_id(sessao.indicacao_id)
    if indicacao is None:
        raise EntidadeNaoEncontradaError(
            f"Indicação {sessao.indicacao_id} da sessão {sessao.id} não encontrada."
        )
    return _rodada_da_indicacao(indicacao, rodadas).clube_id


def _rodada_da_indicacao(indicacao: Indicacao, rodadas: RodadaRepository) -> Rodada:
    rodada = rodadas.buscar_por_id(indicacao.rodada_id)
    if rodada is None:
        raise EntidadeNaoEncontradaError(
            f"Rodada {indicacao.rodada_id} da indicação {indicacao.id} não encontrada."
        )
    return rodada
