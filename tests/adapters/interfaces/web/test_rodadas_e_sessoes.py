"""Testes da rotina semanal pela web: rodada, indicações, sorteio, sessões e avaliações."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from tests.adapters.interfaces.web.conftest import (
    WebDeTeste,
    avisos,
    cadastrar_filme,
    cadastrar_membro,
    textos,
)


@dataclass(frozen=True)
class Clube:
    id: str
    iano: str
    bia: str
    parasita: str
    interestelar: str
    duna: str


@pytest.fixture
def clube(web: WebDeTeste, clube_id: str) -> Clube:
    """Um clube com dois membros, três filmes e a rodada 1 aberta."""
    iano = cadastrar_membro(web, clube_id, "Iano")
    bia = cadastrar_membro(web, clube_id, "Bia")
    filmes = [cadastrar_filme(web, clube_id, t) for t in ("Parasita", "Interestelar", "Duna")]
    web.agir(f"/clubes/{clube_id}/rodadas")
    return Clube(clube_id, iano, bia, *filmes)


def _rodada(web: WebDeTeste, clube: Clube) -> str:
    return str(web.api("GET", f"/clubes/{clube.id}/rodadas")[-1]["id"])


def _indicar(web: WebDeTeste, clube: Clube, membro: str, filme: str) -> list[str]:
    caminho = f"/clubes/{clube.id}/rodadas/{_rodada(web, clube)}/indicacoes"
    return avisos(web.agir(caminho, membro_id=membro, filme_id=filme))


def _indicacao_de(web: WebDeTeste, clube: Clube, filme: str) -> str:
    indicacoes = web.api("GET", f"/rodadas/{_rodada(web, clube)}/indicacoes")
    return next(i["id"] for i in indicacoes if i["filme_id"] == filme)


def test_abrir_rodada_pelo_painel(web: WebDeTeste, clube_id: str) -> None:
    painel = web.abrir(f"/clubes/{clube_id}")
    assert painel.select_one(f"form[action='/clubes/{clube_id}/rodadas']") is not None

    pagina = web.agir(f"/clubes/{clube_id}/rodadas")

    assert avisos(pagina) == ["Rodada 1 aberta."]
    assert "Rodada 1" in textos(pagina, "h2")


def test_indicar_e_democracia(web: WebDeTeste, clube: Clube) -> None:
    assert _indicar(web, clube, clube.iano, clube.parasita) == ["Iano indicou Parasita."]
    pagina = web.agir(f"/clubes/{clube.id}/democracia", filme_id=clube.duna)

    assert avisos(pagina) == ["Sessão democracia com Duna."]
    linhas = textos(pagina, "tbody tr")
    assert any("Parasita" in linha and "Iano" in linha for linha in linhas)
    assert any("Duna" in linha and "Democracia" in linha for linha in linhas)


def test_filme_repetido_no_clube_e_recusado(web: WebDeTeste, clube: Clube) -> None:
    _indicar(web, clube, clube.iano, clube.parasita)

    assert _indicar(web, clube, clube.bia, clube.parasita) == [
        "Esse filme já passou pelo clube: foi assistido ou já está indicado."
    ]


def test_formulario_sem_escolha_vira_aviso(web: WebDeTeste, clube: Clube) -> None:
    assert _indicar(web, clube, "", clube.parasita) == ["Escolha quem indica."]


def test_sortear_anuncia_o_filme(web: WebDeTeste, clube: Clube) -> None:
    _indicar(web, clube, clube.iano, clube.parasita)

    pagina = web.agir(f"/clubes/{clube.id}/rodadas/{_rodada(web, clube)}/sorteio")

    assert avisos(pagina) == ["Sorteado: Parasita, indicado por Iano."]
    assert "Sorteada" in textos(pagina, "tbody tr")[0]


def test_sessao_com_presenca_e_avaliacoes(web: WebDeTeste, clube: Clube) -> None:
    _indicar(web, clube, clube.iano, clube.parasita)
    indicacao = _indicacao_de(web, clube, clube.parasita)

    formulario = web.abrir(f"/clubes/{clube.id}/indicacoes/{indicacao}/sessao")
    marcados = [c["value"] for c in formulario.select("input[name='presentes'][checked]")]
    assert sorted(marcados) == sorted([clube.iano, clube.bia])

    sessao = web.agir(f"/clubes/{clube.id}/indicacoes/{indicacao}/sessao", presentes=[clube.iano])
    assert avisos(sessao) == ["Sessão registrada. Agora é avaliar!"]
    assert textos(sessao, "select[name='membro_id'] option") == ["Iano"]

    url = f"/clubes/{clube.id}/sessoes/{_sessao(web, indicacao)}"
    pagina = web.agir(f"{url}/avaliacoes", membro_id=clube.iano, nota="4,5", comentario="Genial")
    assert avisos(pagina) == ["Avaliação de Iano registrada."]
    [linha] = textos(pagina, "tbody tr")
    assert "4,5" in linha
    assert "Genial" in linha
    assert pagina.select_one(".cabecalho .estrelas").get_text() == "★★★★½"
    assert pagina.select_one("select[name='membro_id']") is None


def test_so_quem_esteve_presente_avalia(web: WebDeTeste, clube: Clube) -> None:
    _indicar(web, clube, clube.iano, clube.parasita)
    indicacao = _indicacao_de(web, clube, clube.parasita)
    web.agir(f"/clubes/{clube.id}/indicacoes/{indicacao}/sessao", presentes=[clube.iano])
    url = f"/clubes/{clube.id}/sessoes/{_sessao(web, indicacao)}"

    pagina = web.agir(f"{url}/avaliacoes", membro_id=clube.bia, nota="3")

    assert avisos(pagina) == ["Só quem esteve na sessão pode avaliá-la."]


def test_dorminhoco(web: WebDeTeste, clube: Clube) -> None:
    _indicar(web, clube, clube.iano, clube.parasita)
    indicacao = _indicacao_de(web, clube, clube.parasita)
    web.agir(f"/clubes/{clube.id}/indicacoes/{indicacao}/sessao", presentes=[clube.iano])
    url = f"/clubes/{clube.id}/sessoes/{_sessao(web, indicacao)}"

    pagina = web.agir(f"{url}/avaliacoes", membro_id=clube.iano, nota="dorminhoco")

    assert "Dorminhoco" in textos(pagina, "tbody tr")[0]


def test_sessao_ja_registrada_leva_a_ela(web: WebDeTeste, clube: Clube) -> None:
    _indicar(web, clube, clube.iano, clube.parasita)
    indicacao = _indicacao_de(web, clube, clube.parasita)
    web.agir(f"/clubes/{clube.id}/indicacoes/{indicacao}/sessao", presentes=[clube.iano])

    resposta = web.cliente.get(
        f"/clubes/{clube.id}/indicacoes/{indicacao}/sessao", follow_redirects=False
    )

    assert resposta.status_code == 303
    assert resposta.headers["location"].endswith(_sessao(web, indicacao))


def test_encerrar_a_rodada_e_ver_o_historico(web: WebDeTeste, clube: Clube) -> None:
    _indicar(web, clube, clube.iano, clube.parasita)
    rodada = _rodada(web, clube)
    recusa = web.agir(f"/clubes/{clube.id}/rodadas/{rodada}/encerrar")
    assert "todas as indicações tiverem sido assistidas" in avisos(recusa)[0]

    indicacao = _indicacao_de(web, clube, clube.parasita)
    web.agir(f"/clubes/{clube.id}/indicacoes/{indicacao}/sessao", presentes=[clube.iano])
    pagina = web.agir(f"/clubes/{clube.id}/rodadas/{rodada}/encerrar")

    assert avisos(pagina) == ["Rodada 1 encerrada."]
    assert "Nenhuma rodada aberta." in pagina.get_text()
    historico = web.abrir(f"/clubes/{clube.id}/rodadas")
    assert "Rodada 1" in textos(historico, "tbody tr")[0]
    detalhe = web.abrir(f"/clubes/{clube.id}/rodadas/{rodada}")
    assert "Parasita" in textos(detalhe, "tbody tr")[0]
    assert detalhe.select_one("a.botao") is None


def test_sessao_de_outro_clube_nao_abre_por_este(web: WebDeTeste, clube: Clube) -> None:
    _indicar(web, clube, clube.iano, clube.parasita)
    indicacao = _indicacao_de(web, clube, clube.parasita)
    web.agir(f"/clubes/{clube.id}/indicacoes/{indicacao}/sessao", presentes=[clube.iano])
    outro = web.api("POST", "/clubes", {"nome": "Cine Vizinhança"})

    resposta = web.cliente.get(f"/clubes/{outro['id']}/sessoes/{_sessao(web, indicacao)}")

    assert resposta.status_code == 404


def _sessao(web: WebDeTeste, indicacao: str) -> str:
    return str(web.api("GET", f"/indicacoes/{indicacao}/sessao")["id"])
