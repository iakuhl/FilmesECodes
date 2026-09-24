"""Implementação de `CriterioApuracaoOscar` que pergunta ao usuário.

O mecanismo de apuração de uma categoria do Óscar (votação, média de
notas, júri) continua em aberto no produto — ver docs/ROADMAP.md. Este
adapter não resolve essa questão: ele a delega a quem está rodando a
CLI, listando as nomeações e pedindo que a pessoa aponte a vencedora.

Isso não é um atalho, é exatamente o propósito do port: o caso de uso
`ApurarCategoriaOscar` permanece ignorante do critério, e o dia em que o
clube decidir um mecanismo automático bastará escrever outro adapter e
trocá-lo no composition root — sem tocar em domínio nem em aplicação.
"""

from __future__ import annotations

import typer

from filmes_e_cubos.application.ports.filme_repository import FilmeRepository
from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar


class CriterioApuracaoInterativo:
    """Escolhe a nomeação vencedora perguntando a quem opera a CLI.

    Depende de `FilmeRepository` apenas para mostrar o título de cada
    filme nomeado: escolher por id seria hostil com o usuário.
    """

    def __init__(self, filme_repository: FilmeRepository) -> None:
        self._filmes = filme_repository

    def escolher_vencedora(self, nomeacoes: list[NomeacaoOscar]) -> NomeacaoOscar:
        typer.echo("\nNomeações desta categoria:")
        for posicao, nomeacao in enumerate(nomeacoes, start=1):
            typer.echo(f"  {posicao}) {self._descrever(nomeacao)}")

        while True:
            escolha: int = typer.prompt("\nNúmero da nomeação vencedora", type=int)
            if 1 <= escolha <= len(nomeacoes):
                return nomeacoes[escolha - 1]
            typer.secho(
                f"Escolha um número entre 1 e {len(nomeacoes)}.",
                fg=typer.colors.YELLOW,
                err=True,
            )

    def _descrever(self, nomeacao: NomeacaoOscar) -> str:
        filme = self._filmes.buscar_por_id(nomeacao.filme_id)
        titulo = (
            filme.titulo if filme is not None else f"(filme {nomeacao.filme_id} não encontrado)"
        )
        return f"{titulo}  [nomeação {nomeacao.id}]"
