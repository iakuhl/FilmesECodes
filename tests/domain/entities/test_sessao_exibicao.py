"""Testes da entidade SessaoExibicao."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from filmes_e_cubos.domain.entities.avaliacao import Avaliacao
from filmes_e_cubos.domain.entities.sessao_exibicao import SessaoExibicao
from filmes_e_cubos.domain.exceptions.avaliacao import MembroAusenteNaSessaoError
from filmes_e_cubos.domain.value_objects.escala_avaliacao import EscalaAvaliacao
from filmes_e_cubos.domain.value_objects.identificadores import IndicacaoId, MembroId
from filmes_e_cubos.domain.value_objects.media_das_notas import MediaDasNotas
from filmes_e_cubos.domain.value_objects.nota import Nota


def test_registrar_sessao_guarda_dados_informados() -> None:
    indicacao_id = IndicacaoId(uuid4())
    membros_presentes = frozenset({MembroId(uuid4()), MembroId(uuid4())})

    sessao = SessaoExibicao.registrar(
        indicacao_id=indicacao_id,
        data_sessao=date(2024, 1, 7),
        membros_presentes=membros_presentes,
    )

    assert sessao.indicacao_id == indicacao_id
    assert sessao.data_sessao == date(2024, 1, 7)
    assert sessao.membros_presentes == membros_presentes


def _sessao(*presentes: MembroId) -> SessaoExibicao:
    return SessaoExibicao.registrar(
        indicacao_id=IndicacaoId(uuid4()),
        data_sessao=date(2024, 1, 7),
        membros_presentes=frozenset(presentes),
    )


def _avaliacao(sessao: SessaoExibicao, nota: str | None) -> Avaliacao:
    return Avaliacao.criar(
        sessao_id=sessao.id,
        membro_id=MembroId(uuid4()),
        escala=EscalaAvaliacao.padrao(),
        nota=Nota.criar(nota) if nota is not None else None,
    )


def test_presente_pode_avaliar_e_ausente_nao() -> None:
    presente, ausente = MembroId(uuid4()), MembroId(uuid4())
    sessao = _sessao(presente)

    sessao.verificar_presenca(presente)
    with pytest.raises(MembroAusenteNaSessaoError):
        sessao.verificar_presenca(ausente)


def test_sessao_registrada_ainda_nao_tem_media() -> None:
    assert _sessao().media_das_notas is None


def test_recalcular_media_ignora_dorminhocos() -> None:
    sessao = _sessao()

    sessao.recalcular_media(
        [_avaliacao(sessao, "4"), _avaliacao(sessao, None), _avaliacao(sessao, "2.5")]
    )

    assert sessao.media_das_notas == MediaDasNotas(soma=Decimal("6.5"), quantidade=2)


def test_so_dorminhocos_deixam_a_sessao_sem_media() -> None:
    sessao = _sessao()

    sessao.recalcular_media([_avaliacao(sessao, None)])

    assert sessao.media_das_notas is None
