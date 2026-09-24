"""Implementação fake e determinística de `SorteadorService`.

Em vez de sortear aleatoriamente, sempre escolhe um candidato pré-definido
(por padrão, o primeiro), tornando os testes de `RealizarSorteio`
determinísticos.
"""

from __future__ import annotations

from filmes_e_cubos.domain.value_objects.identificadores import IndicacaoId


class SorteadorFake:
    def __init__(self, escolha: IndicacaoId | None = None) -> None:
        self._escolha = escolha

    def sortear(self, candidatos: list[IndicacaoId]) -> IndicacaoId:
        if self._escolha is not None:
            return self._escolha
        return candidatos[0]
