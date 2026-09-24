"""Contrato para o critério que decide o vencedor de uma categoria do Óscar.

O mecanismo concreto (votação entre membros, média de notas, etc.) ainda
não foi decidido para o produto (ver docs/ROADMAP.md). Este port existe
para que o caso de uso `ApurarCategoriaOscar` não fique acoplado a essa
decisão em aberto.
"""

from typing import Protocol

from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar


class CriterioApuracaoOscar(Protocol):
    def escolher_vencedora(self, nomeacoes: list[NomeacaoOscar]) -> NomeacaoOscar: ...
