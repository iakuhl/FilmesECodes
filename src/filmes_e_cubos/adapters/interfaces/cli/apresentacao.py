"""Formatação da saída da CLI: tabelas, rótulos e mensagens de resultado.

Concentrar a formatação aqui mantém os módulos de comando com uma única
responsabilidade — traduzir argumentos em chamadas de caso de uso — e
garante que toda a CLI fale com a mesma voz.

A tabela é montada à mão, sem biblioteca de terminal. `rich` só está
instalado como dependência transitiva do `typer` (que oferece a variante
`typer-slim`, sem ela); depender dele sem declará-lo deixaria a CLI
refém de um detalhe de empacotamento de terceiros.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

import typer

AUSENTE = "—"
"""Preenchimento para um campo opcional não informado."""


def formatar_opcional(valor: object | None) -> str:
    """Texto de uma célula que pode não ter valor."""
    return AUSENTE if valor is None else str(valor)


def formatar_duracao(minutos: int | None) -> str:
    """Duração de um filme: `148 min`, ou o marcador de ausente."""
    return AUSENTE if minutos is None else f"{minutos} min"


def formatar_decimal(valor: Decimal) -> str:
    """Decimal em notação brasileira (vírgula decimal)."""
    return str(valor).replace(".", ",")


def echo_resultado(mensagem: str) -> None:
    """Confirmação de uma ação que alterou dados."""
    typer.secho(f"✔ {mensagem}", fg=typer.colors.GREEN)


def echo_aviso(mensagem: str) -> None:
    """Informação que não é erro, mas pede atenção (ex.: lista vazia)."""
    typer.secho(mensagem, fg=typer.colors.YELLOW)


def echo_titulo(mensagem: str) -> None:
    """Cabeçalho de um bloco de saída."""
    typer.secho(mensagem, bold=True)


def echo_tabela(
    cabecalho: Sequence[str],
    linhas: Sequence[Sequence[str]],
    *,
    vazio: str = "Nada a exibir.",
) -> None:
    """Imprime uma tabela de largura fixa por coluna.

    Com `linhas` vazio, imprime `vazio` em vez de um cabeçalho solitário.
    """
    if not linhas:
        echo_aviso(vazio)
        return

    larguras = [
        max(len(cabecalho[coluna]), *(len(linha[coluna]) for linha in linhas))
        for coluna in range(len(cabecalho))
    ]

    def formatar(celulas: Sequence[str]) -> str:
        return "  ".join(
            texto.ljust(largura) for texto, largura in zip(celulas, larguras, strict=True)
        )

    typer.secho(formatar(cabecalho), bold=True)
    typer.echo("  ".join("-" * largura for largura in larguras))
    for linha in linhas:
        typer.echo(formatar(linha))
