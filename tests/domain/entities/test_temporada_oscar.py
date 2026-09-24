"""Testes da entidade TemporadaOscar."""

import pytest

from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.exceptions.oscar import TemporadaOscarInvalidaError
from filmes_e_cubos.domain.value_objects.status import StatusTemporadaOscar


def test_abrir_temporada_nasce_em_preparacao(clube: Clube) -> None:
    temporada = TemporadaOscar.abrir(
        clube_id=clube.id, ano=2024, nome="Óscar do Filmes e Cubos 2024"
    )

    assert temporada.status is StatusTemporadaOscar.EM_PREPARACAO


def test_avancar_para_o_proximo_status_da_sequencia(clube: Clube) -> None:
    temporada = TemporadaOscar.abrir(clube_id=clube.id, ano=2024, nome="Óscar 2024")

    temporada.avancar_para(StatusTemporadaOscar.ABERTA_PARA_INDICACOES)

    assert temporada.status is StatusTemporadaOscar.ABERTA_PARA_INDICACOES


def test_avancar_pulando_uma_etapa_levanta_erro(clube: Clube) -> None:
    temporada = TemporadaOscar.abrir(clube_id=clube.id, ano=2024, nome="Óscar 2024")

    with pytest.raises(TemporadaOscarInvalidaError):
        temporada.avancar_para(StatusTemporadaOscar.APURADA)
