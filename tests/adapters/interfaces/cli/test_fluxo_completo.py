"""Teste de ponta a ponta: uma temporada inteira do clube pela CLI.

Os demais arquivos testam cada grupo de comandos isoladamente. Este
percorre o ciclo real do Filmes e Cubos de uma ponta à outra — fundar o
clube, rodar uma rodada completa, assistir, avaliar, votar no Óscar,
mandar o placar e premiar — para
garantir que os comandos combinam entre si, e não apenas funcionam
sozinhos.
"""

from __future__ import annotations

from filmes_e_cubos.adapters.interfaces.cli.contexto import FabricaDeContexto
from filmes_e_cubos.adapters.interfaces.cli.main import app
from tests.adapters.interfaces.cli.conftest import _UUID, CliDeTeste
from tests.application.fakes.enviador_de_email_fake import EnviadorDeEmailFake

MEMBROS = ("Iano", "Bia", "Caio")
FILMES = ("Parasita", "Interestelar", "Cidade de Deus")


def test_temporada_completa_do_clube(cli: CliDeTeste) -> None:
    cli.executar_ok("clube", "criar", "Filmes e Cubos", "--tamanho-rodada", "3")
    membros = {nome: cli.criar("membro", "cadastrar", nome) for nome in MEMBROS}
    filmes = {titulo: cli.criar("filme", "cadastrar", titulo) for titulo in FILMES}

    cli.executar_ok("rodada", "abrir")
    indicacoes = {
        titulo: cli.criar(
            "indicacao", "indicar", "--membro-id", membros[nome], "--filme-id", filmes[titulo]
        )
        for nome, titulo in zip(MEMBROS, FILMES, strict=True)
    }

    # A rodada só fecha quando as três indicações tiverem sido assistidas.
    assert cli.executar("rodada", "encerrar").exit_code == 1

    # A cada semana o clube sorteia e assiste ao que saiu — nessa ordem.
    sessoes = {}
    for _ in indicacoes:
        sorteada = cli.criar("indicacao", "sortear")
        titulo = next(t for t, i in indicacoes.items() if i == sorteada)
        sessoes[titulo] = cli.criar("sessao", "registrar", sorteada)

    assert set(sessoes) == set(FILMES)

    # Cada membro avalia; um deles cochilou na sessão de "Parasita".
    for nome, membro in membros.items():
        if nome == "Caio":
            cli.executar_ok(
                "avaliacao", "registrar", "--sessao-id", sessoes["Parasita"], "--membro-id", membro
            )
        else:
            cli.executar_ok(
                "avaliacao",
                "registrar",
                "--sessao-id",
                sessoes["Parasita"],
                "--membro-id",
                membro,
                "--nota",
                "4,5",
            )

    avaliacoes = cli.executar_ok("avaliacao", "listar", sessoes["Parasita"]).stdout
    assert avaliacoes.count("4,5") == 2
    assert "dorminhoco" in avaliacoes

    cli.executar_ok("rodada", "encerrar")
    assert "Rodada 2 aberta" in cli.executar_ok("rodada", "abrir").stdout

    # Óscar: uma categoria com dois concorrentes. Os três votam, o placar vai
    # por e-mail e, depois da cerimônia, registra-se o vencedor.
    cli.executar_ok("oscar", "temporada", "abrir", "--nomeacoes-por-categoria", "2")
    categoria = cli.criar("oscar", "categoria", "definir", "Melhor veículo", "--tipo", "variavel")
    cli.executar_ok("oscar", "temporada", "avancar")
    for titulo in ("Parasita", "Interestelar"):
        cli.executar_ok(
            "oscar", "nomear", "--categoria-id", categoria, "--filme-id", filmes[titulo]
        )
    cli.executar_ok("oscar", "temporada", "avancar")

    # Todos põem Interestelar (a 2ª nomeação) em primeiro e confirmam a cédula.
    for membro in membros.values():
        cli.executar_ok(
            "oscar", "votar", "--membro-id", membro, "--categoria-id", categoria, "2", "1"
        )
        cli.executar_ok("oscar", "confirmar", "--membro-id", membro)

    correio = EnviadorDeEmailFake()
    envio = cli.runner.invoke(
        app,
        ["--db-path", str(cli.caminho_banco), "oscar", "enviar-placar", "cerimonia@clube.com"],
        obj=FabricaDeContexto(cli.caminho_banco, enviador=correio),
    )
    assert envio.exit_code == 0, envio.output
    assert "6 pontos  Interestelar — indicado por Bia" in correio.enviadas[0].corpo

    # "Interestelar" foi indicado por Bia: o troféu é de quem indicou.
    nomeacoes = cli.executar_ok("oscar", "categoria", "nomeacoes", categoria).stdout
    [interestelar] = _UUID.findall(
        next(linha for linha in nomeacoes.splitlines() if "Interestelar" in linha)
    )
    premiacao = cli.executar_ok("oscar", "premiar", categoria, "--nomeacao-id", interestelar)
    assert "Troféu para Bia" in premiacao.stdout
    assert "Bia" in cli.executar_ok("oscar", "categoria", "listar").stdout
    assert "apurada" in cli.executar_ok("oscar", "temporada", "avancar").stdout
