"""Entidade que representa um clube de cinema."""

from __future__ import annotations

from uuid import uuid4

from filmes_e_cubos.domain.exceptions.clube import NomeClubeObrigatorioError
from filmes_e_cubos.domain.value_objects.configuracao_clube import ConfiguracaoClube
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId


class Clube:
    """Um clube de cinema, com sua configuração de rodadas e avaliações.

    Membros, rodadas e temporadas do Óscar não são compostos dentro desta
    classe: cada um guarda seu próprio `clube_id` e é acessado por
    repositório dedicado. Isso mantém o clube independente do tamanho do
    histórico associado e já prepara o terreno para suportar múltiplos
    clubes (ver docs/ROADMAP.md, Fase 5).
    """

    def __init__(self, *, id: ClubeId, nome: str, configuracao: ConfiguracaoClube) -> None:
        if not nome or not nome.strip():
            raise NomeClubeObrigatorioError("O nome do clube é obrigatório.")
        self._id = id
        self._nome = nome
        self._configuracao = configuracao

    @classmethod
    def criar(cls, *, nome: str, configuracao: ConfiguracaoClube | None = None) -> Clube:
        return cls(
            id=ClubeId(uuid4()),
            nome=nome,
            configuracao=configuracao or ConfiguracaoClube.padrao(),
        )

    @property
    def id(self) -> ClubeId:
        return self._id

    @property
    def nome(self) -> str:
        return self._nome

    @property
    def configuracao(self) -> ConfiguracaoClube:
        return self._configuracao

    def atualizar_configuracao(self, configuracao: ConfiguracaoClube) -> None:
        """Substitui a configuração do clube (ex.: novo tamanho de rodada ou escala de notas)."""
        self._configuracao = configuracao
