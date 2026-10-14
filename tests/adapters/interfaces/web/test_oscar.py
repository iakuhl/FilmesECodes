"""Testes das telas do Óscar: edição, categorias, nomeações, votação e envio do placar."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import pytest
from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.adapters.interfaces.servidor import criar_aplicacao
from tests.adapters.interfaces.web.conftest import (
    WebDeTeste,
    avisos,
    cadastrar_filme,
    cadastrar_membro,
    textos,
)
from tests.application.fakes.enviador_de_email_fake import EnviadorDeEmailFake


@pytest.fixture
def correio() -> EnviadorDeEmailFake:
    return EnviadorDeEmailFake()


@pytest.fixture
def web(engine_de_teste: Engine, correio: EnviadorDeEmailFake) -> Iterator[WebDeTeste]:
    """O site com um correio que guarda as mensagens em vez de enviá-las."""
    with TestClient(criar_aplicacao(Contexto(engine_de_teste, enviador=correio))) as cliente:
        yield WebDeTeste(cliente)


@dataclass(frozen=True)
class Edicao:
    clube: str
    id: str
    categoria: str
    iano: str
    bia: str

    @property
    def caminho(self) -> str:
        return f"/clubes/{self.clube}/oscar/{self.id}"


@pytest.fixture
def edicao(web: WebDeTeste, clube_id: str) -> Edicao:
    """Iano e Bia assistiram a Parasita e Interestelar neste ano; a edição tem uma
    categoria de duas nomeações e está aberta para indicações.
    """
    iano = cadastrar_membro(web, clube_id, "Iano")
    bia = cadastrar_membro(web, clube_id, "Bia")
    web.agir(f"/clubes/{clube_id}/rodadas")
    rodada = web.api("GET", f"/clubes/{clube_id}/rodadas")[-1]["id"]
    for membro, titulo in ((iano, "Parasita"), (bia, "Interestelar")):
        filme = cadastrar_filme(web, clube_id, titulo)
        web.agir(
            f"/clubes/{clube_id}/rodadas/{rodada}/indicacoes", membro_id=membro, filme_id=filme
        )
        indicacao = next(
            i["id"]
            for i in web.api("GET", f"/rodadas/{rodada}/indicacoes")
            if i["filme_id"] == filme
        )
        web.agir(f"/clubes/{clube_id}/indicacoes/{indicacao}/sessao", presentes=[iano, bia])
    resposta = web.enviar(f"/clubes/{clube_id}/oscar", nomeacoes_por_categoria="2")
    temporada = str(resposta.headers["location"]).rsplit("/", 1)[-1]
    web.agir(f"/clubes/{clube_id}/oscar/{temporada}/categorias", nome="Melhor veículo")
    categoria = web.api("GET", f"/oscar/temporadas/{temporada}/categorias")[0]["id"]
    web.agir(f"/clubes/{clube_id}/oscar/{temporada}/avancar")
    return Edicao(clube_id, temporada, categoria, iano, bia)


def _nomear_tudo(web: WebDeTeste, edicao: Edicao) -> None:
    pagina = web.abrir(f"{edicao.caminho}/categorias/{edicao.categoria}")
    for opcao in pagina.select("select[name='filme_id'] option"):
        web.agir(
            f"{edicao.caminho}/categorias/{edicao.categoria}/nomeacoes", filme_id=opcao["value"]
        )


def _em_votacao(web: WebDeTeste, edicao: Edicao) -> None:
    _nomear_tudo(web, edicao)
    web.agir(f"{edicao.caminho}/avancar")


def _votar(
    web: WebDeTeste, edicao: Edicao, membro: str, primeira: int, segunda: int
) -> BeautifulSoup:
    cedula = web.abrir(f"{edicao.caminho}/votacao/{membro}")
    selects = cedula.select("select[name='escolhas']")
    escolhas = [
        selects[0].select("option")[primeira]["value"],
        selects[1].select("option")[segunda]["value"],
    ]
    return web.agir(f"{edicao.caminho}/votacao/{membro}/votos", escolhas=escolhas)


def test_abrir_edicao_pela_web(web: WebDeTeste, clube_id: str) -> None:
    pagina = web.agir(f"/clubes/{clube_id}/oscar", nome="Óscar dos Cubos")

    assert avisos(pagina) == ["Óscar dos Cubos aberta."]
    assert "Em preparação" in pagina.get_text()
    assert "Óscar dos Cubos" in textos(web.abrir(f"/clubes/{clube_id}/oscar"), "tbody tr")[0]


def test_categoria_e_nomeacoes(web: WebDeTeste, edicao: Edicao) -> None:
    categoria = web.abrir(f"{edicao.caminho}/categorias/{edicao.categoria}")
    assert textos(categoria, "select[name='filme_id'] option") == ["Interestelar", "Parasita"]

    _nomear_tudo(web, edicao)

    nomeacoes = textos(web.abrir(f"{edicao.caminho}/categorias/{edicao.categoria}"), "ol li")
    assert nomeacoes == ["Interestelar — indicado por Bia", "Parasita — indicado por Iano"]
    assert "2/2" in textos(web.abrir(edicao.caminho), "tbody tr")[0]


def test_votacao_exige_as_nomeacoes_completas(web: WebDeTeste, edicao: Edicao) -> None:
    pagina = web.agir(f"{edicao.caminho}/avancar")

    assert "Melhor veículo (0/2)" in avisos(pagina)[0]


def test_data_do_evento(web: WebDeTeste, edicao: Edicao) -> None:
    pagina = web.agir(f"{edicao.caminho}/data-evento", data_evento="2026-12-20")
    assert avisos(pagina) == ["Data do evento marcada."]
    assert "20/12/2026" in pagina.get_text()

    assert (
        "informe uma data válida"
        in avisos(web.agir(f"{edicao.caminho}/data-evento", data_evento="amanhã"))[0]
    )


def test_votacao_completa_ate_o_placar(
    web: WebDeTeste, edicao: Edicao, correio: EnviadorDeEmailFake
) -> None:
    _em_votacao(web, edicao)
    situacao = web.abrir(f"{edicao.caminho}/votacao")
    assert [linha.split()[0] for linha in textos(situacao, "tbody tr")] == ["Bia", "Iano"]

    assert avisos(_votar(web, edicao, edicao.iano, 1, 2)) == [
        "Votos de Iano gravados em: Melhor veículo."
    ]
    cedula = web.abrir(f"{edicao.caminho}/votacao/{edicao.iano}")
    assert "Você já votou aqui." in cedula.get_text()
    assert cedula.select("option[selected]") == []  # o voto gravado não volta à tela

    web.agir(f"{edicao.caminho}/votacao/{edicao.iano}/confirmacao")
    _votar(web, edicao, edicao.bia, 1, 2)
    fim = web.agir(f"{edicao.caminho}/votacao/{edicao.bia}/confirmacao")
    assert avisos(fim) == ["Cédula de Bia confirmada.", "Todos confirmaram: a votação terminou."]

    pagina = web.agir(f"{edicao.caminho}/placar", destinatario="cerimonia@clube.com")
    assert avisos(pagina) == ["Placar enviado para cerimonia@clube.com."]
    assert "pontos" not in pagina.get_text()
    [mensagem] = correio.enviadas
    assert "Interestelar — indicado por Bia" in mensagem.corpo


def test_cedula_incompleta_vira_aviso(web: WebDeTeste, edicao: Edicao) -> None:
    _em_votacao(web, edicao)
    cedula = web.abrir(f"{edicao.caminho}/votacao/{edicao.iano}")
    so_a_primeira = cedula.select("select[name='escolhas']")[0].select("option")[1]["value"]

    pagina = web.agir(f"{edicao.caminho}/votacao/{edicao.iano}/votos", escolhas=[so_a_primeira, ""])

    assert avisos(pagina) == ["Melhor veículo: escolha a 1ª e a 2ª opção."]


def test_confirmar_sem_votar_vira_aviso(web: WebDeTeste, edicao: Edicao) -> None:
    _em_votacao(web, edicao)

    pagina = web.agir(f"{edicao.caminho}/votacao/{edicao.iano}/confirmacao")

    assert avisos(pagina) == ["Falta votar em: Melhor veículo."]


def test_quem_entrou_depois_da_votacao_nao_tem_cedula(web: WebDeTeste, edicao: Edicao) -> None:
    _em_votacao(web, edicao)
    caio = cadastrar_membro(web, edicao.clube, "Caio")

    assert web.cliente.get(f"{edicao.caminho}/votacao/{caio}").status_code == 404


def test_placar_antes_do_fim_da_votacao(web: WebDeTeste, edicao: Edicao) -> None:
    _em_votacao(web, edicao)

    pagina = web.agir(f"{edicao.caminho}/placar", destinatario="cerimonia@clube.com")

    assert "ainda não terminou" in avisos(pagina)[0]


def test_registrar_o_vencedor_depois_da_votacao(web: WebDeTeste, edicao: Edicao) -> None:
    _em_votacao(web, edicao)
    categoria = f"{edicao.caminho}/categorias/{edicao.categoria}"
    assert web.abrir(categoria).select_one(f"form[action='{categoria}/trofeu']") is None
    for eleitor in (edicao.iano, edicao.bia):
        _votar(web, edicao, eleitor, 1, 2)
        web.agir(f"{edicao.caminho}/votacao/{eleitor}/confirmacao")

    formulario = web.abrir(categoria)
    vencedora = formulario.select("select[name='nomeacao_id'] option")[0]["value"]
    pagina = web.agir(f"{categoria}/trofeu", nomeacao_id=vencedora, membro_escolhido_id="")

    assert avisos(pagina) == ["Melhor veículo: troféu para Bia."]
    assert "Troféu para Bia." in pagina.get_text()
    assert "Bia" in textos(web.abrir(edicao.caminho), "tbody tr")[0]
    assert "Apurada" in web.agir(f"{edicao.caminho}/avancar").get_text()


def test_empate_absoluto_pela_web(web: WebDeTeste, edicao: Edicao) -> None:
    _em_votacao(web, edicao)
    for eleitor in (edicao.iano, edicao.bia):
        _votar(web, edicao, eleitor, 1, 2)
        web.agir(f"{edicao.caminho}/votacao/{eleitor}/confirmacao")
    categoria = f"{edicao.caminho}/categorias/{edicao.categoria}"

    recusa = web.agir(f"{categoria}/trofeu", nomeacao_id="", membro_escolhido_id="")
    pagina = web.agir(f"{categoria}/trofeu", nomeacao_id="", membro_escolhido_id=edicao.iano)

    assert "escolha quem leva o troféu" in avisos(recusa)[0]
    assert "Empate absoluto" in pagina.get_text()
    assert "Troféu para Iano." in pagina.get_text()
