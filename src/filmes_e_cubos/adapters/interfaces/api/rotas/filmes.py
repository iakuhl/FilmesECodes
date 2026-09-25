"""Rotas do catálogo de filmes.

O catálogo é compartilhado entre clubes (um `Filme` não pertence a um
clube), por isso nenhuma rota aqui fica sob `/clubes/{clube_id}`.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from filmes_e_cubos.adapters.interfaces.api.esquemas import FilmeSaida, NovaDuracao, NovoFilme
from filmes_e_cubos.adapters.interfaces.consultas import obter_filme
from filmes_e_cubos.adapters.interfaces.contexto_http import ContextoDep
from filmes_e_cubos.domain.value_objects.identificadores import FilmeId

roteador = APIRouter(tags=["filmes"])


@roteador.get("/filmes", summary="Lista o catálogo de filmes")
def listar_filmes(contexto: ContextoDep) -> list[FilmeSaida]:
    return [FilmeSaida.de_dominio(filme) for filme in contexto.filmes.listar_todos()]


@roteador.post("/filmes", status_code=status.HTTP_201_CREATED, summary="Cadastra um filme")
def cadastrar_filme(novo: NovoFilme, contexto: ContextoDep) -> FilmeSaida:
    filme = contexto.cadastrar_filme.executar(
        titulo=novo.titulo,
        ano_lancamento=novo.ano_lancamento,
        diretor=novo.diretor,
        identificador_externo=novo.identificador_externo,
        duracao_minutos=novo.duracao_minutos,
    )
    return FilmeSaida.de_dominio(filme)


@roteador.get("/filmes/{filme_id}", summary="Consulta um filme")
def consultar_filme(filme_id: UUID, contexto: ContextoDep) -> FilmeSaida:
    return FilmeSaida.de_dominio(obter_filme(contexto.filmes, filme_id))


@roteador.put(
    "/filmes/{filme_id}/duracao",
    summary="Informa ou corrige a duração de um filme",
    description="Útil para os filmes cadastrados antes de a duração existir no catálogo.",
)
def definir_duracao(filme_id: UUID, nova: NovaDuracao, contexto: ContextoDep) -> FilmeSaida:
    filme = contexto.definir_duracao_filme.executar(
        filme_id=FilmeId(filme_id), duracao_minutos=nova.duracao_minutos
    )
    return FilmeSaida.de_dominio(filme)
