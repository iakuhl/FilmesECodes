"""Identificadores tipados de cada entidade do domínio.

Centralizar todos os ids aqui como `NewType` sobre `UUID` isola o impacto
de uma eventual troca de esquema de identificador (ex.: UUID -> inteiro
autoincrementado) a este único módulo, sem tocar nas entidades.
"""

from typing import NewType
from uuid import UUID

ClubeId = NewType("ClubeId", UUID)
MembroId = NewType("MembroId", UUID)
FilmeId = NewType("FilmeId", UUID)
RodadaId = NewType("RodadaId", UUID)
IndicacaoId = NewType("IndicacaoId", UUID)
SorteioId = NewType("SorteioId", UUID)
SessaoExibicaoId = NewType("SessaoExibicaoId", UUID)
AvaliacaoId = NewType("AvaliacaoId", UUID)
TemporadaOscarId = NewType("TemporadaOscarId", UUID)
CategoriaOscarId = NewType("CategoriaOscarId", UUID)
NomeacaoOscarId = NewType("NomeacaoOscarId", UUID)
TrofeuId = NewType("TrofeuId", UUID)
