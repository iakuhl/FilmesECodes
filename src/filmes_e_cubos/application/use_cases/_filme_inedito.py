"""Regra "filme não se repete no clube", compartilhada pelas duas formas de indicar.

Tanto a indicação semanal (`IndicarFilme`) quanto a sessão democracia
(`AdicionarFilmeDemocracia`) põem um filme no caminho do clube, e as duas
precisam recusar o mesmo filme duas vezes (decisão 5 de docs/PENDENCIAS.md).
"""

from __future__ import annotations

from filmes_e_cubos.application.ports.indicacao_repository import IndicacaoRepository
from filmes_e_cubos.application.ports.rodada_repository import RodadaRepository
from filmes_e_cubos.domain.exceptions.indicacao import FilmeRepetidoNoClubeError
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId, FilmeId
from filmes_e_cubos.domain.value_objects.status import StatusIndicacao


def verificar_filme_inedito_no_clube(
    *,
    filme_id: FilmeId,
    clube_id: ClubeId,
    indicacoes: IndicacaoRepository,
    rodadas: RodadaRepository,
) -> None:
    """Recusa o filme se ele já tem qualquer indicação no clube.

    Como uma rodada só se encerra com todas as indicações assistidas, toda
    indicação do clube ou já foi assistida, ou está pendente na rodada
    aberta — e, nos dois casos, o filme não pode ser indicado de novo.
    """
    for indicacao in indicacoes.listar_por_filme(filme_id):
        rodada = rodadas.buscar_por_id(indicacao.rodada_id)
        if rodada is None or rodada.clube_id != clube_id:
            continue
        if indicacao.status is StatusIndicacao.ASSISTIDA:
            raise FilmeRepetidoNoClubeError(f"O filme {filme_id} já foi assistido pelo clube.")
        raise FilmeRepetidoNoClubeError(
            f"O filme {filme_id} já está indicado no clube e ainda não foi assistido."
        )
