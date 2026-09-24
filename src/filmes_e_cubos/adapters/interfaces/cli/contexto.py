"""Ligação entre a CLI e o composition root.

O grafo de dependências em si (repositórios, serviços e casos de uso) é
montado em `filmes_e_cubos.adapters.composicao`, compartilhado por todas
as interfaces. Este módulo cuida apenas do que é específico da CLI:
quando montar esse grafo e qual critério de apuração do Óscar usar.
"""

from __future__ import annotations

from functools import cached_property
from pathlib import Path

import typer

from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.adapters.interfaces.cli.criterio_apuracao_interativo import (
    CriterioApuracaoInterativo,
)
from filmes_e_cubos.adapters.interfaces.cli.erros import CliError
from filmes_e_cubos.adapters.persistence.sqlite.fabrica_engine import criar_engine
from filmes_e_cubos.application.ports.criterio_apuracao_oscar import CriterioApuracaoOscar
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
    critério de apuração), usado por testes e por eventuais embarcadores
    da CLI.
    """

    def __init__(
        self,
        caminho_banco: Path,
        *,
        relogio: RelogioService | None = None,
        sorteador: SorteadorService | None = None,
        criterio_apuracao: CriterioApuracaoOscar | None = None,
    ) -> None:
        self.caminho_banco = caminho_banco
        self._relogio = relogio
        self._sorteador = sorteador
        self._criterio_apuracao = criterio_apuracao

    @cached_property
    def contexto(self) -> Contexto:
        return Contexto(
            criar_engine(self.caminho_banco),
            relogio=self._relogio,
            sorteador=self._sorteador,
        )

    @cached_property
    def criterio_apuracao(self) -> CriterioApuracaoOscar:
        """O critério injetado ou, por padrão, o que pergunta no terminal."""
        return self._criterio_apuracao or CriterioApuracaoInterativo(self.contexto.filmes)


def obter_contexto(ctx: typer.Context) -> Contexto:
    """Recupera o `Contexto` da fábrica que o callback raiz guardou em `ctx.obj`."""
    return _obter_fabrica(ctx).contexto


def obter_criterio_apuracao(ctx: typer.Context) -> CriterioApuracaoOscar:
    """Recupera o critério de apuração do Óscar que a CLI deve usar."""
    return _obter_fabrica(ctx).criterio_apuracao


def _obter_fabrica(ctx: typer.Context) -> FabricaDeContexto:
    """`find_object` sobe a cadeia de contextos do Typer, então funciona
    igual em um comando de primeiro nível e em um sub-app aninhado.
    """
    fabrica = ctx.find_object(FabricaDeContexto)
    if fabrica is None:
        raise CliError("Contexto da CLI não foi inicializado.")
    return fabrica
