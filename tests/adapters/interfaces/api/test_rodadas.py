"""Testes das rotas do ciclo de vida de uma rodada."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

from tests.adapters.interfaces.api.conftest import ApiDeTeste, Json, assert_problema


def test_abrir_rodada(api: ApiDeTeste, clube: Json) -> None:
    rodada = api.criar(f"/clubes/{clube['id']}/rodadas")

    assert rodada["numero"] == 1
    assert rodada["status"] == "aberta"
    assert rodada["clube_id"] == clube["id"]
    assert rodada["data_inicio"] == date.today().isoformat()
    assert rodada["data_encerramento"] is None


def test_nao_abre_duas_rodadas_ao_mesmo_tempo(api: ApiDeTeste, clube: Json, rodada: Json) -> None:
    assert_problema(api.post(f"/clubes/{clube['id']}/rodadas"), 409, "rodada_ja_aberta")


def test_consultar_a_rodada_aberta(api: ApiDeTeste, clube: Json, rodada: Json) -> None:
    assert api.obter(f"/clubes/{clube['id']}/rodadas/aberta") == rodada
    assert api.obter(f"/rodadas/{rodada['id']}") == rodada


def test_sem_rodada_aberta_e_404(api: ApiDeTeste, clube: Json) -> None:
    corpo = assert_problema(
        api.get(f"/clubes/{clube['id']}/rodadas/aberta"), 404, "entidade_nao_encontrada"
    )

    assert "não tem rodada aberta" in corpo["detail"]


def test_nao_encerra_com_indicacao_por_assistir(
    api: ApiDeTeste, rodada: Json, indicacao: Json
) -> None:
    resposta = api.post(f"/rodadas/{rodada['id']}/encerrar")

    assert_problema(resposta, 409, "rodada_nao_encerravel")


def test_nao_encerra_rodada_sem_indicacoes(api: ApiDeTeste, rodada: Json) -> None:
    assert_problema(api.post(f"/rodadas/{rodada['id']}/encerrar"), 409, "rodada_nao_encerravel")


def test_encerrar_e_abrir_a_proxima(
    api: ApiDeTeste, clube: Json, rodada: Json, sessao: Json
) -> None:
    encerrada = api.executar(f"/rodadas/{rodada['id']}/encerrar")
    seguinte = api.criar(f"/clubes/{clube['id']}/rodadas")

    assert encerrada["status"] == "encerrada"
    assert encerrada["data_encerramento"] == date.today().isoformat()
    assert seguinte["numero"] == 2
    historico = api.obter(f"/clubes/{clube['id']}/rodadas")
    assert [(r["numero"], r["status"]) for r in historico] == [(1, "encerrada"), (2, "aberta")]


def test_encerrar_duas_vezes_e_conflito(api: ApiDeTeste, rodada: Json, sessao: Json) -> None:
    api.executar(f"/rodadas/{rodada['id']}/encerrar")

    assert_problema(api.post(f"/rodadas/{rodada['id']}/encerrar"), 409, "rodada_ja_encerrada")


def test_clube_ou_rodada_inexistente_e_404(api: ApiDeTeste) -> None:
    assert_problema(api.post(f"/clubes/{uuid4()}/rodadas"), 404, "entidade_nao_encontrada")
    assert_problema(api.get(f"/clubes/{uuid4()}/rodadas"), 404, "entidade_nao_encontrada")
    assert_problema(api.get(f"/rodadas/{uuid4()}"), 404, "entidade_nao_encontrada")
    assert_problema(api.post(f"/rodadas/{uuid4()}/encerrar"), 404, "entidade_nao_encontrada")
