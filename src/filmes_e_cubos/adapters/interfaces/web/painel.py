"""O painel do clube: o que está acontecendo agora, montado para a página.

Listagem de leitura (ADR 7): vai direto aos repositórios. Junta a rodada
aberta com as suas indicações (filme, quem indicou e a sessão, se já
houve), os membros ativos e a edição do Óscar do ano.
"""

from __future__ import annotations

from dataclasses import dataclass

from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.filme import Filme
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.entities.sessao_exibicao import SessaoExibicao
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar


@dataclass(frozen=True)
class IndicacaoNaPagina:
    """Uma indicação com o que a página mostra dela."""

    indicacao: Indicacao
    filme: Filme | None
    membro: Membro | None
    """`None` numa indicação democracia, que não tem quem indicou."""
    sessao: SessaoExibicao | None


@dataclass(frozen=True)
class Painel:
    rodada: Rodada | None
    indicacoes: list[IndicacaoNaPagina]
    membros_ativos: list[Membro]
    temporada_do_ano: TemporadaOscar | None


def indicacoes_da_rodada(contexto: Contexto, rodada: Rodada) -> list[IndicacaoNaPagina]:
    return [
        IndicacaoNaPagina(
            indicacao=indicacao,
            filme=contexto.filmes.buscar_por_id(indicacao.filme_id),
            membro=(
                contexto.membros.buscar_por_id(indicacao.membro_id)
                if indicacao.membro_id is not None
                else None
            ),
            sessao=contexto.sessoes.buscar_por_indicacao(indicacao.id),
        )
        for indicacao in contexto.indicacoes.listar_por_rodada(rodada.id)
    ]


def montar_painel(contexto: Contexto, clube: Clube) -> Painel:
    rodada = contexto.rodadas.buscar_aberta_por_clube(clube.id)
    return Painel(
        rodada=rodada,
        indicacoes=indicacoes_da_rodada(contexto, rodada) if rodada is not None else [],
        membros_ativos=contexto.membros.listar_ativos_por_clube(clube.id),
        temporada_do_ano=contexto.temporadas.buscar_por_clube_e_ano(
            clube.id, contexto.relogio.hoje().year
        ),
    )
