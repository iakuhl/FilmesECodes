"""Contrato para o serviço responsável por sortear uma indicação elegível."""

from typing import Protocol

from filmes_e_cubos.domain.value_objects.identificadores import IndicacaoId


class SorteadorService(Protocol):
    def sortear(self, candidatos: list[IndicacaoId]) -> IndicacaoId: ...
