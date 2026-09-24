"""Fixtures dos testes da CLI.

Os testes exercitam a CLI de verdade — o app Typer real, o composition
root real e um banco SQLite real em arquivo temporário. Nada é fake aqui:
a Fase 2 já cobriu cada repositório isoladamente, então o que falta
verificar é justamente a costura entre comando, caso de uso e banco.

As fixtures encadeadas (`clube_id` -> `membro_id` -> `rodada_aberta` ->
`indicacao_id` -> `sessao_id`) montam o cenário sempre pela própria CLI,
e não inserindo linhas no banco: um teste que prepara o estado por fora
deixaria de perceber se o comando de preparo quebrou.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pytest
from typer.testing import CliRunner, Result

from filmes_e_cubos.adapters.interfaces.cli.main import app

_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


@dataclass(frozen=True)
class CliDeTeste:
    """Executa a CLI contra um banco temporário e ajuda a ler o resultado."""

    runner: CliRunner
    caminho_banco: Path

    def executar(self, *args: str, entrada: str | None = None) -> Result:
        return self.runner.invoke(
            app, ["--db-path", str(self.caminho_banco), *args], input=entrada
        )

    def executar_ok(self, *args: str, entrada: str | None = None) -> Result:
        """Executa esperando sucesso; falha o teste mostrando a saída se não for."""
        resultado = self.executar(*args, entrada=entrada)
        assert resultado.exit_code == 0, resultado.output
        return resultado

    def criar(self, *args: str, entrada: str | None = None) -> str:
        """Executa um comando de criação e devolve o id da entidade criada."""
        resultado = self.executar_ok(*args, entrada=entrada)
        ids = _UUID.findall(resultado.stdout)
        assert ids, f"Nenhum id na saída do comando: {resultado.stdout!r}"
        return str(ids[-1])


@pytest.fixture
def cli(tmp_path: Path) -> CliDeTeste:
    return CliDeTeste(runner=CliRunner(), caminho_banco=tmp_path / "filmes_e_cubos_teste.db")


@pytest.fixture
def clube_id(cli: CliDeTeste) -> str:
    return cli.criar("clube", "criar", "Filmes e Cubos")


@pytest.fixture
def membro_id(cli: CliDeTeste, clube_id: str) -> str:
    return cli.criar("membro", "cadastrar", "Iano")


@pytest.fixture
def outro_membro_id(cli: CliDeTeste, clube_id: str) -> str:
    return cli.criar("membro", "cadastrar", "Bia")


@pytest.fixture
def filme_id(cli: CliDeTeste) -> str:
    return cli.criar("filme", "cadastrar", "Parasita", "--ano", "2019", "--diretor", "Bong Joon-ho")


@pytest.fixture
def outro_filme_id(cli: CliDeTeste) -> str:
    return cli.criar("filme", "cadastrar", "Interestelar", "--ano", "2014")


@pytest.fixture
def rodada_aberta(cli: CliDeTeste, clube_id: str) -> str:
    return cli.criar("rodada", "abrir")


@pytest.fixture
def indicacao_id(cli: CliDeTeste, rodada_aberta: str, membro_id: str, filme_id: str) -> str:
    return cli.criar("indicacao", "indicar", "--membro-id", membro_id, "--filme-id", filme_id)


@pytest.fixture
def sessao_id(cli: CliDeTeste, indicacao_id: str) -> str:
    return cli.criar("sessao", "registrar", indicacao_id)
