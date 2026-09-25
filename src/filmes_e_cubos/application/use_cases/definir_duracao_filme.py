"""Caso de uso: informar ou corrigir a duração de um filme do catálogo."""

from __future__ import annotations

from filmes_e_cubos.application.ports.filme_repository import FilmeRepository
from filmes_e_cubos.domain.entities.filme import Filme
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import FilmeId


class DefinirDuracaoFilme:
    """Grava a duração (em minutos) de um filme já cadastrado.

    Existe porque a duração só passou a ser registrada depois de o
    catálogo já ter filmes — e é ela que permite somar o tempo assistido
    no ano (ver docs/PENDENCIAS.md, decisão 10).
    """

    def __init__(self, filme_repository: FilmeRepository) -> None:
        self._filmes = filme_repository

    def executar(self, *, filme_id: FilmeId, duracao_minutos: int) -> Filme:
        filme = self._filmes.buscar_por_id(filme_id)
        if filme is None:
            raise EntidadeNaoEncontradaError(f"Filme {filme_id} não encontrado.")
        filme.definir_duracao(duracao_minutos)
        self._filmes.salvar(filme)
        return filme
