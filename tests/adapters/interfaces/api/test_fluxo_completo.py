"""Teste de ponta a ponta: uma temporada inteira do clube pela API.

Os demais arquivos testam cada grupo de rotas isoladamente. Este percorre
o ciclo real do Filmes e Cubos de uma ponta à outra — fundar o clube,
rodar uma rodada completa, assistir, avaliar e premiar — para garantir
que as rotas combinam entre si, e não apenas funcionam sozinhas.
"""

from __future__ import annotations

from tests.adapters.interfaces.api.conftest import ApiDeTeste

MEMBROS = ("Iano", "Bia", "Caio")
FILMES = ("Parasita", "Interestelar", "Cidade de Deus")


def test_temporada_completa_do_clube(api: ApiDeTeste) -> None:
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

    # Óscar: uma categoria com dois concorrentes; o grupo escolhe "Interestelar".
    temporada = api.criar(f"/clubes/{clube['id']}/oscar/temporadas")
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

    trofeu = api.criar(
        f"/oscar/categorias/{categoria['id']}/apuracao",
        {"nomeacao_vencedora_id": nomeacoes["Interestelar"]},
    )

    # "Interestelar" foi indicado por Bia: o troféu é de quem indicou.
    assert trofeu["membro_vencedor_id"] == membros["Bia"]
    assert api.obter(f"/oscar/categorias/{categoria['id']}/trofeu") == trofeu
