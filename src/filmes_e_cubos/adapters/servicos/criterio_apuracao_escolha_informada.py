"""Implementação de `CriterioApuracaoOscar` em que a vencedora já vem escolhida.

O mecanismo de apuração de uma categoria do Óscar continua em aberto no
produto (ver docs/ROADMAP.md). Assim como a CLI, que pergunta no terminal
qual nomeação venceu, as interfaces HTTP delegam essa decisão a quem
opera — só que a escolha chega pronta, dentro da própria requisição.

Este critério não decide nada: apenas confere que a nomeação escolhida
concorre de fato na categoria apurada, e a devolve.
"""

from __future__ import annotations

from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar
from filmes_e_cubos.domain.exceptions.oscar import NomeacaoInvalidaError
from filmes_e_cubos.domain.value_objects.identificadores import NomeacaoOscarId


class CriterioEscolhaInformada:
    """Declara vencedora a nomeação indicada por quem pediu a apuração."""

    def __init__(self, nomeacao_vencedora_id: NomeacaoOscarId) -> None:
        self._nomeacao_vencedora_id = nomeacao_vencedora_id

    def escolher_vencedora(self, nomeacoes: list[NomeacaoOscar]) -> NomeacaoOscar:
        for nomeacao in nomeacoes:
            if nomeacao.id == self._nomeacao_vencedora_id:
                return nomeacao
        raise NomeacaoInvalidaError(
            f"Nomeação {self._nomeacao_vencedora_id} não concorre nesta categoria."
        )
