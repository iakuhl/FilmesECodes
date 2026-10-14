"""Teste de ponta a ponta: uma temporada inteira do clube pela API.

Os demais arquivos testam cada grupo de rotas isoladamente. Este percorre
o ciclo real do Filmes e Cubos de uma ponta à outra — fundar o clube,
rodar uma rodada completa, assistir, avaliar, votar no Óscar, mandar o
placar e premiar — para garantir que as rotas combinam entre si, e não
apenas funcionam sozinhas.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.adapters.interfaces.servidor import criar_aplicacao
from tests.adapters.interfaces.api.conftest import ApiDeTeste
from tests.application.fakes.enviador_de_email_fake import EnviadorDeEmailFake

MEMBROS = ("Iano", "Bia", "Caio")
FILMES = ("Parasita", "Interestelar", "Cidade de Deus")


@pytest.fixture
def correio() -> EnviadorDeEmailFake:
    return EnviadorDeEmailFake()


@pytest.fixture
def api(engine_de_teste: Engine, correio: EnviadorDeEmailFake) -> Iterator[ApiDeTeste]:
    """A API com um correio que guarda o placar em vez de enviá-lo."""
    with TestClient(criar_aplicacao(Contexto(engine_de_teste, enviador=correio))) as cliente:
        yield ApiDeTeste(cliente)


def test_temporada_completa_do_clube(api: ApiDeTeste, correio: EnviadorDeEmailFake) -> None:
    clube = api.criar("/clubes", {"nome": "Filmes e Cubos", "configuracao": {"tamanho_rodada": 3}})
    membros = {
        nome: api.criar(f"/clubes/{clube['id']}/membros", {"nome": nome})["id"] for nome in MEMBROS
    }
    filmes = {titulo: api.criar("/filmes", {"titulo": titulo})["id"] for titulo in FILMES}

    rodada = api.criar(f"/clubes/{clube['id']}/rodadas")
    indicacoes = {
        titulo: api.criar(
            f"/rodadas/{rodada['id']}/indicacoes",
            {"membro_id": membros[nome], "filme_id": filmes[titulo]},
        )["id"]
        for nome, titulo in zip(MEMBROS, FILMES, strict=True)
    }

    # A rodada só fecha quando as três indicações tiverem sido assistidas.
    assert api.post(f"/rodadas/{rodada['id']}/encerrar").status_code == 409

    # A cada semana o clube sorteia e assiste ao que saiu — nessa ordem.
    sessoes = {}
    for _ in indicacoes:
        sorteada = api.criar(f"/rodadas/{rodada['id']}/sorteios")["indicacao_sorteada_id"]
        titulo = next(t for t, i in indicacoes.items() if i == sorteada)
        sessoes[titulo] = api.criar(f"/indicacoes/{sorteada}/sessao")["id"]
    assert set(sessoes) == set(FILMES)

    # Cada membro avalia; Caio cochilou na sessão de "Parasita".
    for nome, membro_id in membros.items():
        nota = None if nome == "Caio" else "4.5"
        api.criar(
            f"/sessoes/{sessoes['Parasita']}/avaliacoes", {"membro_id": membro_id, "nota": nota}
        )
    avaliacoes = api.obter(f"/sessoes/{sessoes['Parasita']}/avaliacoes")
    assert sorted(a["status"] for a in avaliacoes) == [
        "dorminhoco",
        "nota_registrada",
        "nota_registrada",
    ]

    api.executar(f"/rodadas/{rodada['id']}/encerrar")
    assert api.criar(f"/clubes/{clube['id']}/rodadas")["numero"] == 2

    # Óscar: uma categoria com dois concorrentes. Os três votam, o placar vai
    # por e-mail e, depois da cerimônia, registra-se o vencedor.
    temporada = api.criar(f"/clubes/{clube['id']}/oscar/temporadas", {"nomeacoes_por_categoria": 2})
    categoria = api.criar(
        f"/oscar/temporadas/{temporada['id']}/categorias", {"nome": "Melhor veículo"}
    )
    api.executar(f"/oscar/temporadas/{temporada['id']}/avancar")
    nomeacoes = {
        titulo: api.criar(
            f"/oscar/categorias/{categoria['id']}/nomeacoes", {"filme_id": filmes[titulo]}
        )["id"]
        for titulo in ("Parasita", "Interestelar")
    }
    api.executar(f"/oscar/temporadas/{temporada['id']}/avancar")

    # Todos põem Interestelar em primeiro e confirmam a cédula.
    for membro_id in membros.values():
        api.atualizar(
            f"/oscar/categorias/{categoria['id']}/votos/{membro_id}",
            {"escolhas": [nomeacoes["Interestelar"], nomeacoes["Parasita"]]},
        )
        confirmacao = api.executar(
            f"/oscar/temporadas/{temporada['id']}/votacao/cedulas/{membro_id}/confirmacao"
        )
    assert confirmacao["votacao"]["encerrada_em"] is not None

    api.executar(
        f"/oscar/temporadas/{temporada['id']}/placar/envios",
        {"destinatario": "cerimonia@clube.com"},
    )
    assert "6 pontos  Interestelar — indicado por Bia" in correio.enviadas[0].corpo

    # "Interestelar" foi indicado por Bia: o troféu é de quem indicou.
    trofeu = api.criar(
        f"/oscar/categorias/{categoria['id']}/trofeu", {"nomeacao_id": nomeacoes["Interestelar"]}
    )
    assert trofeu["membro_vencedor_id"] == membros["Bia"]
    assert api.obter(f"/oscar/categorias/{categoria['id']}/trofeu") == trofeu
    assert api.executar(f"/oscar/temporadas/{temporada['id']}/avancar")["status"] == "apurada"
