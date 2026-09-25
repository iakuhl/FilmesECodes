"""Testes da entidade TemporadaOscar."""

from datetime import date
from uuid import uuid4

import pytest

from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.exceptions.oscar import (
    AcaoForaDaFaseError,
    NumeroDeNomeacoesInvalidoError,
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


def _na_fase(clube: Clube, status: StatusTemporadaOscar) -> TemporadaOscar:
    return TemporadaOscar(
        id=TemporadaOscarId(uuid4()), clube_id=clube.id, ano=2024, nome="Óscar", status=status
    )


def test_ciclo_completo_passa_pela_votacao(clube: Clube) -> None:
    temporada = TemporadaOscar.abrir(clube_id=clube.id, ano=2024, nome="Óscar 2024")
    visitados = [temporada.status]

    while (proximo := temporada.proximo_status) is not None:
        temporada.avancar_para(proximo)
        visitados.append(temporada.status)

    assert visitados == [
        StatusTemporadaOscar.EM_PREPARACAO,
        StatusTemporadaOscar.ABERTA_PARA_INDICACOES,
        StatusTemporadaOscar.EM_VOTACAO,
        StatusTemporadaOscar.APURADA,
        StatusTemporadaOscar.ENCERRADA,
    ]


def test_nomeacoes_por_categoria_padrao_e_escolhida(clube: Clube) -> None:
    padrao = TemporadaOscar.abrir(clube_id=clube.id, ano=2024, nome="Óscar 2024")
    escolhida = TemporadaOscar.abrir(
        clube_id=clube.id, ano=2025, nome="Óscar 2025", nomeacoes_por_categoria=3
    )

    assert padrao.nomeacoes_por_categoria == 5
    assert escolhida.nomeacoes_por_categoria == 3


@pytest.mark.parametrize("quantidade", [1, 0, -5])
def test_categoria_precisa_de_ao_menos_duas_nomeacoes(clube: Clube, quantidade: int) -> None:
    with pytest.raises(NumeroDeNomeacoesInvalidoError):
        TemporadaOscar.abrir(
            clube_id=clube.id, ano=2024, nome="Óscar", nomeacoes_por_categoria=quantidade
        )


@pytest.mark.parametrize(
    ("status", "aceita"),
    [
        (StatusTemporadaOscar.EM_PREPARACAO, True),
        (StatusTemporadaOscar.ABERTA_PARA_INDICACOES, True),
        (StatusTemporadaOscar.EM_VOTACAO, False),
        (StatusTemporadaOscar.APURADA, False),
        (StatusTemporadaOscar.ENCERRADA, False),
    ],
)
def test_fases_que_aceitam_categorias(
    clube: Clube, status: StatusTemporadaOscar, aceita: bool
) -> None:
    temporada = _na_fase(clube, status)

    if aceita:
        temporada.verificar_aceita_categorias()
    else:
        with pytest.raises(AcaoForaDaFaseError):
            temporada.verificar_aceita_categorias()


@pytest.mark.parametrize("status", list(StatusTemporadaOscar))
def test_so_a_fase_de_indicacoes_aceita_nomeacoes(
    clube: Clube, status: StatusTemporadaOscar
) -> None:
    temporada = _na_fase(clube, status)

    if status is StatusTemporadaOscar.ABERTA_PARA_INDICACOES:
        temporada.verificar_aceita_nomeacoes()
    else:
        with pytest.raises(AcaoForaDaFaseError):
            temporada.verificar_aceita_nomeacoes()
