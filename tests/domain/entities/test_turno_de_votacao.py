"""Testes da entidade TurnoDeVotacao: a contagem dos votos e os desempates."""

from datetime import datetime
from uuid import uuid4

import pytest

from filmes_e_cubos.domain.entities.turno_de_votacao import TurnoDeVotacao
from filmes_e_cubos.domain.exceptions.oscar import (
    NumeroDeNomeacoesInvalidoError,
    VotacaoEncerradaError,
    VotoInvalidoError,
)
from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    NomeacaoOscarId,
    TurnoDeVotacaoId,
)
from filmes_e_cubos.domain.value_objects.status import ModoDeVotacao

MOMENTO = datetime(2024, 12, 20, 21, 0)
A, B, C, D = (NomeacaoOscarId(uuid4()) for _ in range(4))


def _turno(
    *candidatas: NomeacaoOscarId, modo: ModoDeVotacao = ModoDeVotacao.DUPLA
) -> TurnoDeVotacao:
    return TurnoDeVotacao(
        id=TurnoDeVotacaoId(uuid4()),
        categoria_id=CategoriaOscarId(uuid4()),
        numero=1,
        modo=modo,
        candidatas=candidatas,
    )


def test_primeiro_turno_e_uma_votacao_dupla_entre_todas_as_nomeacoes() -> None:
    turno = TurnoDeVotacao.abrir_primeiro(categoria_id=CategoriaOscarId(uuid4()), candidatas=[A, B])

    assert turno.numero == 1
    assert turno.modo is ModoDeVotacao.DUPLA
    assert turno.candidatas == (A, B)
    assert turno.aberto
    assert turno.pontuacao is None
    assert turno.lideres == ()


def test_turno_precisa_de_duas_nomeacoes_distintas() -> None:
    with pytest.raises(NumeroDeNomeacoesInvalidoError):
        _turno(A)
    with pytest.raises(NumeroDeNomeacoesInvalidoError):
        _turno(A, A)


def test_votacao_dupla_da_2_pontos_a_1a_opcao_e_1_a_2a() -> None:
    turno = _turno(A, B, C)

    seguinte = turno.apurar([(A, B), (A, C), (B, A)], momento=MOMENTO)

    assert seguinte is None
    assert turno.pontuacao == (5, 3, 1)
    assert turno.lideres == (A,)
    assert not turno.aberto
    assert turno.apurado_em == MOMENTO
    assert not turno.empate_absoluto


def test_empate_no_topo_entre_parte_das_candidatas_abre_um_turno_duplo_so_com_elas() -> None:
    """Decisão 8.4: o 2º turno reúne só as empatadas, na ordem original."""
    turno = _turno(A, B, C, D)

    seguinte = turno.apurar([(D, B), (B, D), (C, A)], momento=MOMENTO)

    assert turno.lideres == (B, D)
    assert seguinte is not None
    assert seguinte.numero == 2
    assert seguinte.modo is ModoDeVotacao.DUPLA
    assert seguinte.candidatas == (B, D)
    assert seguinte.categoria_id == turno.categoria_id
    assert seguinte.aberto


def test_empate_geral_na_votacao_dupla_leva_a_classificacao_com_as_mesmas() -> None:
    """Decisões 8.5 e 16."""
    turno = _turno(A, B)

    seguinte = turno.apurar([(A, B), (B, A)], momento=MOMENTO)

    assert seguinte is not None
    assert seguinte.modo is ModoDeVotacao.CLASSIFICACAO
    assert seguinte.candidatas == (A, B)
    assert not turno.empate_absoluto


def test_classificacao_da_pesos_do_numero_de_candidatas_ate_1() -> None:
    turno = _turno(A, B, C, modo=ModoDeVotacao.CLASSIFICACAO)

    seguinte = turno.apurar([(C, A, B), (A, C, B)], momento=MOMENTO)

    assert turno.pontuacao == (5, 2, 5)
    assert seguinte is not None  # A e C empataram no topo


def test_empate_parcial_na_classificacao_volta_a_votacao_dupla() -> None:
    """Interpretação 2 de docs/PENDENCIAS.md."""
    turno = _turno(A, B, C, modo=ModoDeVotacao.CLASSIFICACAO)

    seguinte = turno.apurar([(A, B, C), (B, A, C)], momento=MOMENTO)

    assert seguinte is not None
    assert seguinte.modo is ModoDeVotacao.DUPLA
    assert seguinte.candidatas == (A, B)


def test_classificacao_com_topo_unico_decide_a_categoria() -> None:
    turno = _turno(A, B, modo=ModoDeVotacao.CLASSIFICACAO)

    assert turno.apurar([(B, A), (B, A)], momento=MOMENTO) is None
    assert turno.lideres == (B,)


def test_empate_geral_na_classificacao_e_empate_absoluto() -> None:
    """Decisão 8.6: nenhuma vence, e não há turno seguinte."""
    turno = _turno(A, B, modo=ModoDeVotacao.CLASSIFICACAO)

    assert turno.apurar([(A, B), (B, A)], momento=MOMENTO) is None
    assert turno.empate_absoluto
    assert turno.lideres == (A, B)


def test_turno_apurado_nao_e_apurado_de_novo() -> None:
    turno = _turno(A, B)
    turno.apurar([(A, B)], momento=MOMENTO)

    with pytest.raises(VotacaoEncerradaError):
        turno.apurar([(A, B)], momento=MOMENTO)


def test_duas_nomeacoes_do_mesmo_filme_sao_opcoes_diferentes() -> None:
    """Decisão 24: vota-se em nomeações; A e B podem ser o mesmo filme."""
    assert _turno(A, B).conferir_escolhas([B, A]) == (B, A)


@pytest.mark.parametrize(
    ("escolhas", "trecho"),
    [
        ([A], "duas nomeações"),
        ([A, B, C], "duas nomeações"),
        ([A, A], "uma vez só"),
        ([A, D], "não concorre"),
    ],
)
def test_voto_duplo_invalido_e_recusado(escolhas: list[NomeacaoOscarId], trecho: str) -> None:
    with pytest.raises(VotoInvalidoError, match=trecho):
        _turno(A, B, C).conferir_escolhas(escolhas)


def test_voto_de_classificacao_ordena_todas_as_candidatas() -> None:
    turno = _turno(A, B, C, modo=ModoDeVotacao.CLASSIFICACAO)

    assert turno.conferir_escolhas([C, A, B]) == (C, A, B)
    with pytest.raises(VotoInvalidoError, match="todas as 3"):
        turno.conferir_escolhas([C, A])


def test_voto_invalido_na_apuracao_e_recusado() -> None:
    turno = _turno(A, B)

    with pytest.raises(VotoInvalidoError):
        turno.apurar([(A, D)], momento=MOMENTO)
    assert turno.aberto
