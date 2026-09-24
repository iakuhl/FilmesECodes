"""Consultas por id que precisam encontrar a entidade, usadas pelas interfaces HTTP.

Os repositórios devolvem `None` quando não encontram nada; quem recebe um
id de fora (um caminho de URL, um campo de formulário) precisa
transformar essa ausência em erro. Estas funções fazem isso de um jeito
só, levantando `EntidadeNaoEncontradaError` — o mesmo erro que os casos de
uso usam —, para que a API e a web o traduzam do mesmo modo que traduzem
os erros vindos do domínio (um 404).
"""

from __future__ import annotations

from uuid import UUID

from filmes_e_cubos.application.ports.categoria_oscar_repository import CategoriaOscarRepository
from filmes_e_cubos.application.ports.clube_repository import ClubeRepository
from filmes_e_cubos.application.ports.filme_repository import FilmeRepository
from filmes_e_cubos.application.ports.indicacao_repository import IndicacaoRepository
from filmes_e_cubos.application.ports.membro_repository import MembroRepository
from filmes_e_cubos.application.ports.nomeacao_oscar_repository import NomeacaoOscarRepository
from filmes_e_cubos.application.ports.rodada_repository import RodadaRepository
from filmes_e_cubos.application.ports.sessao_repository import SessaoRepository
from filmes_e_cubos.application.ports.temporada_oscar_repository import TemporadaOscarRepository
from filmes_e_cubos.domain.entities.categoria_oscar import CategoriaOscar
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.filme import Filme
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.entities.sessao_exibicao import SessaoExibicao
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    ClubeId,
    FilmeId,
    IndicacaoId,
    MembroId,
    NomeacaoOscarId,
    RodadaId,
    SessaoExibicaoId,
    TemporadaOscarId,
)


def obter_clube(clubes: ClubeRepository, clube_id: UUID) -> Clube:
    clube = clubes.buscar_por_id(ClubeId(clube_id))
    if clube is None:
        raise EntidadeNaoEncontradaError(f"Clube {clube_id} não encontrado.")
    return clube


def obter_membro(membros: MembroRepository, membro_id: UUID) -> Membro:
    membro = membros.buscar_por_id(MembroId(membro_id))
    if membro is None:
        raise EntidadeNaoEncontradaError(f"Membro {membro_id} não encontrado.")
    return membro


def obter_filme(filmes: FilmeRepository, filme_id: UUID) -> Filme:
    filme = filmes.buscar_por_id(FilmeId(filme_id))
    if filme is None:
        raise EntidadeNaoEncontradaError(f"Filme {filme_id} não encontrado.")
    return filme


def obter_rodada(rodadas: RodadaRepository, rodada_id: UUID) -> Rodada:
    rodada = rodadas.buscar_por_id(RodadaId(rodada_id))
    if rodada is None:
        raise EntidadeNaoEncontradaError(f"Rodada {rodada_id} não encontrada.")
    return rodada


def obter_rodada_aberta(rodadas: RodadaRepository, clube: Clube) -> Rodada:
    rodada = rodadas.buscar_aberta_por_clube(clube.id)
    if rodada is None:
        raise EntidadeNaoEncontradaError(f"O clube {clube.nome} não tem rodada aberta.")
    return rodada


def obter_indicacao(indicacoes: IndicacaoRepository, indicacao_id: UUID) -> Indicacao:
    indicacao = indicacoes.buscar_por_id(IndicacaoId(indicacao_id))
    if indicacao is None:
        raise EntidadeNaoEncontradaError(f"Indicação {indicacao_id} não encontrada.")
    return indicacao


def obter_sessao(sessoes: SessaoRepository, sessao_id: UUID) -> SessaoExibicao:
    sessao = sessoes.buscar_por_id(SessaoExibicaoId(sessao_id))
    if sessao is None:
        raise EntidadeNaoEncontradaError(f"Sessão {sessao_id} não encontrada.")
    return sessao


def obter_temporada(temporadas: TemporadaOscarRepository, temporada_id: UUID) -> TemporadaOscar:
    temporada = temporadas.buscar_por_id(TemporadaOscarId(temporada_id))
    if temporada is None:
        raise EntidadeNaoEncontradaError(f"Temporada {temporada_id} não encontrada.")
    return temporada


def obter_categoria(categorias: CategoriaOscarRepository, categoria_id: UUID) -> CategoriaOscar:
    categoria = categorias.buscar_por_id(CategoriaOscarId(categoria_id))
    if categoria is None:
        raise EntidadeNaoEncontradaError(f"Categoria {categoria_id} não encontrada.")
    return categoria


def obter_nomeacao(nomeacoes: NomeacaoOscarRepository, nomeacao_id: UUID) -> NomeacaoOscar:
    nomeacao = nomeacoes.buscar_por_id(NomeacaoOscarId(nomeacao_id))
    if nomeacao is None:
        raise EntidadeNaoEncontradaError(f"Nomeação {nomeacao_id} não encontrada.")
    return nomeacao
