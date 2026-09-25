"""Testes da entidade TemporadaOscar."""

from datetime import date
from uuid import uuid4

import pytest

from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.exceptions.oscar import (
    AcaoForaDaFaseError,
    TemporadaOscarInvalidaError,
)
from filmes_e_cubos.domain.value_objects.identificadores import TemporadaOscarId
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


def test_data_do_evento_pode_ser_remarcada_ate_o_encerramento(clube: Clube) -> None:
    temporada = TemporadaOscar.abrir(clube_id=clube.id, ano=2024, nome="Óscar 2024")

    temporada.definir_data_evento(date(2025, 1, 18))
    temporada.definir_data_evento(date(2025, 1, 25))

    assert temporada.data_evento == date(2025, 1, 25)


def test_edicao_encerrada_nao_muda_a_data_do_evento(clube: Clube) -> None:
    temporada = TemporadaOscar(
        id=TemporadaOscarId(uuid4()),
        clube_id=clube.id,
        ano=2024,
        nome="Óscar 2024",
        status=StatusTemporadaOscar.ENCERRADA,
        data_evento=date(2025, 1, 18),
    )

    with pytest.raises(AcaoForaDaFaseError):
        temporada.definir_data_evento(date(2025, 2, 1))
    assert temporada.data_evento == date(2025, 1, 18)
