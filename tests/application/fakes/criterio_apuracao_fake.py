"""Implementação fake e determinística de `CriterioApuracaoOscar`.

Sempre escolhe a nomeação pré-definida (por padrão, a primeira da lista),
tornando os testes de `ApurarCategoriaOscar` determinísticos sem depender
do mecanismo real de apuração (ainda não decidido para o produto).
"""

from __future__ import annotations

from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar
from filmes_e_cubos.domain.value_objects.identificadores import NomeacaoOscarId


class CriterioApuracaoFake:
    def __init__(self, vencedora_id: NomeacaoOscarId | None = None) -> None:
        self._vencedora_id = vencedora_id

    def escolher_vencedora(self, nomeacoes: list[NomeacaoOscar]) -> NomeacaoOscar:
        if self._vencedora_id is not None:
            return next(nomeacao for nomeacao in nomeacoes if nomeacao.id == self._vencedora_id)
        return nomeacoes[0]
