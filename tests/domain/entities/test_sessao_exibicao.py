"""Testes da entidade SessaoExibicao."""

from datetime import date
from uuid import uuid4

from filmes_e_cubos.domain.entities.sessao_exibicao import SessaoExibicao
from filmes_e_cubos.domain.value_objects.identificadores import IndicacaoId, MembroId


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
