"""Testes da entidade Sorteio."""

from datetime import datetime
from uuid import uuid4

from filmes_e_cubos.domain.entities.sorteio import Sorteio
from filmes_e_cubos.domain.value_objects.identificadores import IndicacaoId, RodadaId


def test_registrar_sorteio_guarda_dados_informados() -> None:
    rodada_id = RodadaId(uuid4())
    indicacao_id = IndicacaoId(uuid4())
    data_sorteio = datetime(2024, 1, 7, 20, 0)

    sorteio = Sorteio.registrar(
        rodada_id=rodada_id,
        indicacao_sorteada_id=indicacao_id,
        data_sorteio=data_sorteio,
        metodo="sorteio_aleatorio_uniforme",
    )

    assert sorteio.rodada_id == rodada_id
    assert sorteio.indicacao_sorteada_id == indicacao_id
    assert sorteio.data_sorteio == data_sorteio
    assert sorteio.metodo == "sorteio_aleatorio_uniforme"
