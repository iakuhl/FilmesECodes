"""Ligação entre a CLI e o composition root.

O grafo de dependências em si (repositórios, serviços e casos de uso) é
montado em `filmes_e_cubos.adapters.composicao`, compartilhado por todas
as interfaces. Este módulo cuida apenas do que é específico da CLI:
quando montar esse grafo.
"""

from __future__ import annotations

from functools import cached_property
from pathlib import Path

import typer

from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.adapters.interfaces.cli.erros import CliError
from filmes_e_cubos.adapters.persistence.sqlite.fabrica_engine import (
    criar_engine,
    criar_engine_da_url,
)
from filmes_e_cubos.application.ports.enviador_de_email import EnviadorDeEmail
from filmes_e_cubos.application.ports.relogio_service import RelogioService
from filmes_e_cubos.application.ports.sorteador_service import SorteadorService


class FabricaDeContexto:
    """Adia a montagem do `Contexto` até que um comando precise mesmo dele.

    Abrir o banco cria o arquivo SQLite (`criar_engine` roda
    `metadata.create_all`). Como o callback raiz do Typer roda *antes* do
    parsing do subcomando, montar o contexto ali faria um simples
    `filmes-e-cubos clube --help` criar um banco vazio no diretório atual.
    Guardando apenas o caminho e construindo sob demanda, só comandos que
    de fato tocam dados criam o arquivo.

    Os parâmetros opcionais são o ponto de injeção de implementações
    alternativas dos ports que não vêm do banco (relógio, sorteador,
    e-mail), usado por testes e por eventuais embarcadores da CLI.
    """

    def __init__(
        self,
        caminho_banco: Path,
        *,
        url_banco: str | None = None,
        relogio: RelogioService | None = None,
        sorteador: SorteadorService | None = None,
        enviador: EnviadorDeEmail | None = None,
    ) -> None:
        self.caminho_banco = caminho_banco
        self.url_banco = url_banco
        self._relogio = relogio
        self._sorteador = sorteador
        self._enviador = enviador

    @cached_property
    def contexto(self) -> Contexto:
        engine = (
            criar_engine_da_url(self.url_banco)
            if self.url_banco
            else criar_engine(self.caminho_banco)
        )
        return Contexto(
            engine,
            relogio=self._relogio,
            sorteador=self._sorteador,
            enviador=self._enviador,
        )


def obter_contexto(ctx: typer.Context) -> Contexto:
    """Recupera o `Contexto` da fábrica que o callback raiz guardou em `ctx.obj`."""
    return _obter_fabrica(ctx).contexto


def _obter_fabrica(ctx: typer.Context) -> FabricaDeContexto:
    """`find_object` sobe a cadeia de contextos do Typer, então funciona
    igual em um comando de primeiro nível e em um sub-app aninhado.
    """
    fabrica = ctx.find_object(FabricaDeContexto)
    if fabrica is None:
        raise CliError("Contexto da CLI não foi inicializado.")
    return fabrica
