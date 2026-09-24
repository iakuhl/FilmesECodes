"""Ponto de entrada da CLI: monta o app raiz a partir dos grupos de comando.

Convenção de comandos adotada em toda a interface:

- o alvo evidente de um comando é um argumento posicional
  (`membro desativar <MEMBRO_ID>`, `filme cadastrar "<TÍTULO>"`);
- todo o resto são opções nomeadas;
- ids que a CLI consegue deduzir sozinha (clube, rodada aberta, temporada
  do ano) são opcionais — ver `resolucao.py`;
- erros esperados saem em `stderr` com código 1 — ver `erros.py`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from filmes_e_cubos.adapters.interfaces.cli.comandos import (
    avaliacao,
    clube,
    filme,
    indicacao,
    membro,
    oscar,
    rodada,
    sessao,
)
from filmes_e_cubos.adapters.interfaces.cli.contexto import (
    CAMINHO_BANCO_PADRAO,
    VARIAVEL_DE_AMBIENTE_BANCO,
    FabricaDeContexto,
)
from filmes_e_cubos.adapters.interfaces.cli.erros import GrupoComTratamentoDeErros

app = typer.Typer(
    cls=GrupoComTratamentoDeErros,
    help="Gestão do clube de cinema Filmes e Cubos.",
    no_args_is_help=True,
)

app.add_typer(clube.app, name="clube")
app.add_typer(membro.app, name="membro")
app.add_typer(filme.app, name="filme")
app.add_typer(rodada.app, name="rodada")
app.add_typer(indicacao.app, name="indicacao")
app.add_typer(sessao.app, name="sessao")
app.add_typer(avaliacao.app, name="avaliacao")
app.add_typer(oscar.app, name="oscar")


@app.callback()
def principal(
    ctx: typer.Context,
    db_path: Annotated[
        Path,
        typer.Option(
            "--db-path",
            envvar=VARIAVEL_DE_AMBIENTE_BANCO,
            help="Arquivo SQLite onde os dados do clube são guardados.",
        ),
    ] = CAMINHO_BANCO_PADRAO,
) -> None:
    """Guarda em `ctx.obj` a fábrica que os comandos usam para obter o contexto.

    Se `ctx.obj` já vier preenchido (um teste ou outro programa pode
    passar `obj=` ao invocar o app), essa configuração é respeitada — é o
    ponto de injeção para trocar relógio, sorteador ou critério de
    apuração sem mexer na CLI.
    """
    if ctx.obj is None:
        ctx.obj = FabricaDeContexto(db_path)
