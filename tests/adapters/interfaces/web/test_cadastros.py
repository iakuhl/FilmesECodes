"""Testes das páginas de membros e de filmes."""

from __future__ import annotations

from tests.adapters.interfaces.web.conftest import (
    WebDeTeste,
    avisos,
    cadastrar_filme,
    cadastrar_membro,
    textos,
)


def test_cadastrar_membro(web: WebDeTeste, clube_id: str) -> None:
    pagina = web.agir(f"/clubes/{clube_id}/membros", nome="Iano", apelido="Ianinho")

    assert avisos(pagina) == ["Iano entrou no clube."]
    [linha] = textos(pagina, "tbody tr")
    assert "Iano" in linha
    assert "Ianinho" in linha
    assert "Ativo" in linha


def test_membro_ativo_so_pode_ser_desativado_e_inativo_so_reativado(
    web: WebDeTeste, clube_id: str
) -> None:
    """Decisão 33: reativar não aparece para quem já está ativo."""
    bia = cadastrar_membro(web, clube_id, "Bia")
    ativo = web.abrir(f"/clubes/{clube_id}/membros")
    assert ativo.select_one(f"form[action$='/{bia}/reativar']") is None

    pagina = web.agir(f"/clubes/{clube_id}/membros/{bia}/desativar")
    assert avisos(pagina) == ["Bia foi desativado."]
    assert pagina.select_one(f"form[action$='/{bia}/desativar']") is None

    pagina = web.agir(f"/clubes/{clube_id}/membros/{bia}/reativar")
    assert avisos(pagina) == ["Bia voltou a ser ativo."]
    assert "Ativo" in textos(pagina, "tbody tr")[0]


def test_reativar_quem_ja_esta_ativo_nao_e_erro(web: WebDeTeste, clube_id: str) -> None:
    """Decisão 33: um clique repetido (latência) não vira erro."""
    bia = cadastrar_membro(web, clube_id, "Bia")

    assert avisos(web.agir(f"/clubes/{clube_id}/membros/{bia}/reativar")) == [
        "Bia voltou a ser ativo."
    ]


def test_membro_de_outro_clube_nao_e_alterado_por_este(web: WebDeTeste, clube_id: str) -> None:
    outro = web.api("POST", "/clubes", {"nome": "Cine Vizinhança"})
    duda = web.api("POST", f"/clubes/{outro['id']}/membros", {"nome": "Duda"})

    pagina = web.agir(f"/clubes/{clube_id}/membros/{duda['id']}/desativar")

    assert "não encontrado" in avisos(pagina)[0]
    assert web.api("GET", f"/membros/{duda['id']}")["ativo"] is True


def test_cadastrar_filme_com_todos_os_dados(web: WebDeTeste, clube_id: str) -> None:
    pagina = web.agir(
        f"/clubes/{clube_id}/filmes",
        titulo="Parasita",
        ano_lancamento="2019",
        diretor="Bong Joon-ho",
        duracao_minutos="132",
    )

    assert avisos(pagina) == ["Parasita entrou no catálogo."]
    [linha] = textos(pagina, "tbody tr")
    assert "2019" in linha
    assert "Bong Joon-ho" in linha
    assert "2h12" in linha


def test_ano_que_nao_e_numero_vira_aviso(web: WebDeTeste, clube_id: str) -> None:
    pagina = web.agir(f"/clubes/{clube_id}/filmes", titulo="Parasita", ano_lancamento="dois mil")

    assert "não é um número inteiro" in avisos(pagina)[0]
    assert textos(pagina, "tbody tr") == []


def test_corrigir_a_duracao(web: WebDeTeste, clube_id: str) -> None:
    filme = cadastrar_filme(web, clube_id, "Interestelar")

    pagina = web.agir(f"/clubes/{clube_id}/filmes/{filme}/duracao", duracao_minutos="169")

    assert avisos(pagina) == ["Duração de Interestelar atualizada."]
    assert "2h49" in textos(pagina, "tbody tr")[0]


def test_duracao_vazia_e_recusada(web: WebDeTeste, clube_id: str) -> None:
    filme = cadastrar_filme(web, clube_id, "Interestelar")

    pagina = web.agir(f"/clubes/{clube_id}/filmes/{filme}/duracao", duracao_minutos="")

    assert avisos(pagina) == ["Informe a duração, em minutos."]
