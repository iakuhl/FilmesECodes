"""O que vem no endereço precisa pertencer ao clube da página.

As páginas moram em `/clubes/{clube_id}/...`. Um id de membro, rodada,
indicação ou sessão de *outro* clube não pode ser lido nem alterado por
ali: para quem navega, é uma página que não existe (404), e numa ação,
um aviso de "não encontrado".
"""

from __future__ import annotations

from uuid import UUID

from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.adapters.interfaces.consultas import (
    obter_indicacao,
    obter_membro,
    obter_rodada,
    obter_sessao,
)
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.entities.sessao_exibicao import SessaoExibicao
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError


def membro_do_clube(contexto: Contexto, clube: Clube, membro_id: UUID) -> Membro:
    membro = obter_membro(contexto.membros, membro_id)
    if membro.clube_id != clube.id:
        raise EntidadeNaoEncontradaError(f"Membro {membro_id} não encontrado em {clube.nome}.")
    return membro


def rodada_do_clube(contexto: Contexto, clube: Clube, rodada_id: UUID) -> Rodada:
    rodada = obter_rodada(contexto.rodadas, rodada_id)
    if rodada.clube_id != clube.id:
        raise EntidadeNaoEncontradaError(f"Rodada {rodada_id} não encontrada em {clube.nome}.")
    return rodada


def indicacao_do_clube(contexto: Contexto, clube: Clube, indicacao_id: UUID) -> Indicacao:
    indicacao = obter_indicacao(contexto.indicacoes, indicacao_id)
    rodada_do_clube(contexto, clube, indicacao.rodada_id)
    return indicacao


def sessao_do_clube(contexto: Contexto, clube: Clube, sessao_id: UUID) -> SessaoExibicao:
    sessao = obter_sessao(contexto.sessoes, sessao_id)
    indicacao_do_clube(contexto, clube, sessao.indicacao_id)
    return sessao
