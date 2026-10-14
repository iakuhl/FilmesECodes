"""Testes do início (escolher ou criar o clube) e do painel."""

from __future__ import annotations

from uuid import uuid4

from tests.adapters.interfaces.web.conftest import WebDeTeste, avisos, textos


def test_sem_clube_o_inicio_oferece_criar_um(web: WebDeTeste) -> None:
    pagina = web.abrir("/")

    assert "Bem-vindo" in pagina.select_one("h1").get_text()
    assert pagina.select_one("form[action='/clubes'] input[name='nome']") is not None


def test_criar_clube_leva_ao_painel(web: WebDeTeste) -> None:
    pagina = web.agir("/clubes", nome="Filmes e Cubos", tamanho_rodada="4")

    assert pagina.select_one("h1").get_text() == "Filmes e Cubos"
    assert avisos(pagina) == ["Clube Filmes e Cubos criado."]
    [clube] = web.api("GET", "/clubes")
    assert clube["configuracao"]["tamanho_rodada"] == 4


def test_com_um_clube_o_inicio_vai_direto_a_ele(web: WebDeTeste, clube_id: str) -> None:
    resposta = web.cliente.get("/", follow_redirects=False)

    assert resposta.status_code == 303
    assert resposta.headers["location"] == f"/clubes/{clube_id}"


def test_com_varios_clubes_o_inicio_lista_todos(web: WebDeTeste, clube_id: str) -> None:
    web.enviar("/clubes", nome="Cine Vizinhança")

    assert textos(web.abrir("/"), ".lista-de-cartoes a") == ["Cine Vizinhança", "Filmes e Cubos"]


def test_clube_sem_nome_vira_aviso_de_erro(web: WebDeTeste) -> None:
    pagina = web.agir("/clubes", nome="  ")

    assert avisos(pagina) == ["O nome do clube é obrigatório."]


def test_tamanho_de_rodada_que_nao_e_numero_vira_aviso(web: WebDeTeste) -> None:
    pagina = web.agir("/clubes", nome="Filmes e Cubos", tamanho_rodada="cinco")

    assert "não é um número inteiro" in avisos(pagina)[0]


def test_painel_de_clube_novo(web: WebDeTeste, clube_id: str) -> None:
    pagina = web.abrir(f"/clubes/{clube_id}")

    assert "Nenhuma rodada aberta." in pagina.get_text()
    assert "Nenhum membro cadastrado." in pagina.get_text()
    assert "Nenhuma edição neste ano." in pagina.get_text()
    assert pagina.select_one("nav a[aria-current='page']").get_text() == "Painel"


def test_painel_mostra_a_rodada_aberta(web: WebDeTeste, clube_id: str) -> None:
    iano = web.api("POST", f"/clubes/{clube_id}/membros", {"nome": "Iano"})
    filme = web.api("POST", "/filmes", {"titulo": "Parasita"})
    rodada = web.api("POST", f"/clubes/{clube_id}/rodadas")
    indicacao = web.api(
        "POST",
        f"/rodadas/{rodada['id']}/indicacoes",
        {"membro_id": iano["id"], "filme_id": filme["id"]},
    )
    sessao = web.api("POST", f"/indicacoes/{indicacao['id']}/sessao")
    web.api("POST", f"/sessoes/{sessao['id']}/avaliacoes", {"membro_id": iano["id"], "nota": "4"})

    pagina = web.abrir(f"/clubes/{clube_id}")

    assert "Rodada 1" in textos(pagina, "h2")
    [linha] = textos(pagina, "tbody tr")
    assert "Parasita" in linha
    assert "Iano" in linha
    assert "Assistida" in linha
    assert "★★★★" in linha


def test_clube_inexistente_e_pagina_nao_encontrada(web: WebDeTeste) -> None:
    resposta = web.cliente.get(f"/clubes/{uuid4()}")

    assert resposta.status_code == 404
    assert "Ops" in resposta.text


def test_endereco_com_id_malformado_tambem(web: WebDeTeste) -> None:
    resposta = web.cliente.get("/clubes/nao-e-um-id")

    assert resposta.status_code == 404
