"""Testes do caso de uso CadastrarFilme."""

from filmes_e_cubos.application.use_cases.cadastrar_filme import CadastrarFilme
from tests.application.fakes.filme_repositorio_fake import FilmeRepositorioFake


def test_cadastrar_filme_com_dados_completos() -> None:
    filmes = FilmeRepositorioFake()
    caso_de_uso = CadastrarFilme(filmes)

    filme = caso_de_uso.executar(titulo="Duna", ano_lancamento=2021, diretor="Denis Villeneuve")

    assert filmes.buscar_por_id(filme.id) is filme
    assert filme.titulo == "Duna"
    assert filme.diretor == "Denis Villeneuve"


def test_cadastrar_filme_apenas_com_titulo() -> None:
    filmes = FilmeRepositorioFake()
    caso_de_uso = CadastrarFilme(filmes)

    filme = caso_de_uso.executar(titulo="Arrival")

    assert filme.ano_lancamento is None
    assert filme.diretor is None
