"""Caso de uso: criar um novo clube."""

from __future__ import annotations

from filmes_e_cubos.application.ports.clube_repository import ClubeRepository
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.value_objects.configuracao_clube import ConfiguracaoClube


class CriarClube:
    """Cria um novo clube, com configuração padrão ou customizada."""

    def __init__(self, clube_repository: ClubeRepository) -> None:
        self._clubes = clube_repository

    def executar(self, *, nome: str, configuracao: ConfiguracaoClube | None = None) -> Clube:
        clube = Clube.criar(nome=nome, configuracao=configuracao)
        self._clubes.salvar(clube)
        return clube
