"""Implementação de `SorteadorService` usando escolha pseudoaleatória uniforme."""

from __future__ import annotations

import random

from filmes_e_cubos.domain.value_objects.identificadores import IndicacaoId


class SorteadorAleatorio:
    def sortear(self, candidatos: list[IndicacaoId]) -> IndicacaoId:
        return random.choice(candidatos)
