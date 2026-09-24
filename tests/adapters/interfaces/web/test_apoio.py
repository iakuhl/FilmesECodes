"""Testes dos módulos de apoio da interface web: formatação, formulários e avisos."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

import pytest

from filmes_e_cubos.adapters.interfaces.web.formatacao import (
    ROTULOS,
    formatar_data,
    formatar_data_hora,
    formatar_decimal,
    notas_da_escala,
)
from filmes_e_cubos.adapters.interfaces.web.formularios import (
    decimal_opcional,
    inteiro_opcional,
    nota_ou_dorminhoco,
    texto_opcional,
)
from filmes_e_cubos.adapters.interfaces.web.mensagens import (
    Aviso,
    FormularioInvalidoError,
    avisar,
    consumir_avisos,
    recusas_viram_avisos,
)
from filmes_e_cubos.domain.exceptions.indicacao import IndicacaoDuplicadaError
from filmes_e_cubos.domain.exceptions.rodada import RodadaJaAbertaError
from filmes_e_cubos.domain.value_objects import status, status_avaliacao, tipo_indicacao
from filmes_e_cubos.domain.value_objects.escala_avaliacao import EscalaAvaliacao
from filmes_e_cubos.domain.value_objects.nota import Nota


@dataclass
class RequisicaoFalsa:
    """Só o que os avisos usam de uma requisição: a sessão."""

    session: dict[str, Any] = field(default_factory=dict)


def _enumeracoes_do_dominio() -> list[type[Enum]]:
    modulos = (status, status_avaliacao, tipo_indicacao)
    return [
        valor
        for modulo in modulos
        for valor in vars(modulo).values()
        if isinstance(valor, type)
        and issubclass(valor, Enum)
        and valor.__module__ == modulo.__name__
    ]


def test_todo_membro_de_enumeracao_do_dominio_tem_rotulo() -> None:
    sem_rotulo = [m for e in _enumeracoes_do_dominio() for m in e if m not in ROTULOS]

    assert not sem_rotulo


@pytest.mark.parametrize(
    ("valor", "texto"),
    [
        (Decimal("4.50"), "4,5"),
        (Decimal("5.0"), "5"),
        (Decimal("10"), "10"),
        (Decimal("0.5"), "0,5"),
        (Decimal("1E+1"), "10"),
    ],
)
def test_decimal_sai_com_virgula_e_sem_zeros_inuteis(valor: Decimal, texto: str) -> None:
    assert formatar_decimal(valor) == texto


def test_datas_no_formato_brasileiro() -> None:
    assert formatar_data(date(2026, 9, 24)) == "24/09/2026"
    assert formatar_data(None) == "—"
    assert formatar_data_hora(datetime(2026, 9, 24, 21, 5)) == "24/09/2026 21:05"


def test_notas_da_escala_padrao_da_maior_para_a_menor() -> None:
    notas = notas_da_escala(EscalaAvaliacao.padrao())

    assert notas[0] == Decimal("5.0")
    assert notas[-1] == Decimal("0.5")
    assert len(notas) == 10


def test_campos_opcionais_vazios_viram_none() -> None:
    assert texto_opcional("   ") is None
    assert inteiro_opcional("", campo="Ano") is None
    assert decimal_opcional(" ", campo="Nota") is None


def test_campos_numericos_aceitam_virgula_e_recusam_lixo() -> None:
    assert inteiro_opcional(" 2019 ", campo="Ano") == 2019
    assert decimal_opcional("4,5", campo="Nota") == Decimal("4.5")
    with pytest.raises(FormularioInvalidoError):
        inteiro_opcional("dois mil", campo="Ano")
    with pytest.raises(FormularioInvalidoError):
        decimal_opcional("NaN", campo="Nota")


def test_nota_do_formulario() -> None:
    assert nota_ou_dorminhoco("4.5") == Nota.criar("4.5")
    assert nota_ou_dorminhoco("dorminhoco") is None
    with pytest.raises(FormularioInvalidoError):
        nota_ou_dorminhoco("")  # ninguém vira dorminhoco por formulário incompleto


def test_avisos_sao_consumidos_uma_vez() -> None:
    requisicao = RequisicaoFalsa()

    avisar(requisicao, "sucesso", "Rodada aberta.")  # type: ignore[arg-type]

    assert consumir_avisos(requisicao) == [Aviso("sucesso", "Rodada aberta.")]  # type: ignore[arg-type]
    assert consumir_avisos(requisicao) == []  # type: ignore[arg-type]


def test_recusa_de_negocio_vira_aviso_amigavel() -> None:
    requisicao = RequisicaoFalsa()

    with recusas_viram_avisos(requisicao):  # type: ignore[arg-type]
        raise IndicacaoDuplicadaError("Membro 123 já indicou um filme nesta rodada.")

    (aviso,) = consumir_avisos(requisicao)  # type: ignore[arg-type]
    assert aviso.tipo == "erro"
    assert aviso.texto == "Esse membro já indicou um filme nesta rodada."


def test_formulario_invalido_vira_aviso_com_a_propria_mensagem() -> None:
    requisicao = RequisicaoFalsa()

    with recusas_viram_avisos(requisicao):  # type: ignore[arg-type]
        raise FormularioInvalidoError("Ano: 'x' não é um número inteiro.")

    assert consumir_avisos(requisicao)[0].texto == "Ano: 'x' não é um número inteiro."  # type: ignore[arg-type]


def test_erro_sem_mensagem_amigavel_mantem_a_do_dominio() -> None:
    requisicao = RequisicaoFalsa()

    with recusas_viram_avisos(requisicao):  # type: ignore[arg-type]
        raise RodadaJaAbertaError("texto do domínio")

    assert consumir_avisos(requisicao)[0].texto == "O clube já tem uma rodada aberta."  # type: ignore[arg-type]
