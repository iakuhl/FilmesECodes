"""Erros de uso da CLI e sua tradução para a saída do terminal.

Contrato de erro da interface: qualquer `DomainError` (violação de
invariante do domínio) ou `CliError` (problema de uso da própria
interface) vira uma mensagem em `stderr` e código de saída 1. A tradução
acontece em um único ponto — `GrupoComTratamentoDeErros` — para que
nenhum comando precise repetir `try/except`, e para que um comando novo
já nasça com o comportamento correto.
"""

from __future__ import annotations

from typing import Any

import typer
from typer.core import TyperGroup

from filmes_e_cubos.domain.exceptions.base import DomainError

CODIGO_DE_SAIDA_ERRO = 1


class CliError(Exception):
    """Erro causado pelo uso da CLI, não por violação de regra de negócio.

    Existe separado de `DomainError` porque nada que ele sinaliza é uma
    regra do clube: são situações que só fazem sentido para uma interface
    de linha de comando, como não conseguir decidir sozinha a qual clube
    um comando se refere.
    """


class GrupoComTratamentoDeErros(TyperGroup):
    """Grupo raiz que converte erros esperados em saída amigável.

    `TyperGroup.invoke` despacha o subcomando de dentro da própria
    chamada (inclusive para sub-apps aninhados), então tratar aqui cobre
    toda a árvore de comandos.
    """

    # `ctx` é tipado como `Any` de propósito: a classe base o declara com
    # o `Context` do click vendorizado dentro do typer (`typer._click`),
    # um módulo privado que esta camada não deve importar. Estreitar o
    # tipo para `typer.Context` quebraria a substituição do método.
    def invoke(self, ctx: Any) -> Any:
        try:
            return super().invoke(ctx)
        except (DomainError, CliError) as erro:
            typer.secho(f"Erro: {erro}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=CODIGO_DE_SAIDA_ERRO) from erro
