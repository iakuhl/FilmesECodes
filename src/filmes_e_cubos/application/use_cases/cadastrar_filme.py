"""Caso de uso: cadastrar um filme no catálogo do sistema."""

from __future__ import annotations

from filmes_e_cubos.application.ports.filme_repository import FilmeRepository
from filmes_e_cubos.domain.entities.filme import Filme


class CadastrarFilme:
    """Adiciona um filme ao catálogo, disponível para ser indicado por qualquer clube."""

    def __init__(self, filme_repository: FilmeRepository) -> None:
        self._filmes = filme_repository

    def executar(
        self,
        *,
        titulo: str,
        ano_lancamento: int | None = None,
        diretor: str | None = None,
        identificador_externo: str | None = None,
        duracao_minutos: int | None = None,
    ) -> Filme:
        filme = Filme.criar(
            titulo=titulo,
            ano_lancamento=ano_lancamento,
            diretor=diretor,
            identificador_externo=identificador_externo,
            duracao_minutos=duracao_minutos,
        )
        self._filmes.salvar(filme)
        return filme
