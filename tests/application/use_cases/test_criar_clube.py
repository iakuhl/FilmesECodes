"""Testes do caso de uso CriarClube."""

from filmes_e_cubos.application.use_cases.criar_clube import CriarClube
from filmes_e_cubos.domain.value_objects.configuracao_clube import ConfiguracaoClube
from tests.application.fakes.clube_repositorio_fake import ClubeRepositorioFake


def test_criar_clube_com_configuracao_padrao() -> None:
    clubes = ClubeRepositorioFake()
    caso_de_uso = CriarClube(clubes)

    clube = caso_de_uso.executar(nome="Filmes e Cubos")

    assert clubes.buscar_por_id(clube.id) is clube
    assert clube.configuracao == ConfiguracaoClube.padrao()


def test_criar_clube_com_configuracao_customizada() -> None:
    clubes = ClubeRepositorioFake()
    caso_de_uso = CriarClube(clubes)
    configuracao = ConfiguracaoClube(
        tamanho_rodada=8, escala_avaliacao=ConfiguracaoClube.padrao().escala_avaliacao
    )

    clube = caso_de_uso.executar(nome="Outro Clube", configuracao=configuracao)

    assert clube.configuracao.tamanho_rodada == 8
