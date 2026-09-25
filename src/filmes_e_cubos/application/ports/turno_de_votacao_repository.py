"""Contrato de persistência para a entidade TurnoDeVotacao."""

from typing import Protocol

from filmes_e_cubos.domain.entities.turno_de_votacao import TurnoDeVotacao
from filmes_e_cubos.domain.value_objects.identificadores import CategoriaOscarId


class TurnoDeVotacaoRepository(Protocol):
    def salvar(self, turno: TurnoDeVotacao) -> None: ...

    def listar_por_categoria(self, categoria_id: CategoriaOscarId) -> list[TurnoDeVotacao]:
        """Os turnos da categoria, do 1º ao mais recente."""
        ...
