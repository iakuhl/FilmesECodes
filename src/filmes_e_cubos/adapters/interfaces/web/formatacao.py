"""Como os valores do domínio aparecem nas páginas: datas, números e rótulos.

A web fala com pessoas, então datas saem no formato brasileiro, decimais
com vírgula e enumerações com um rótulo legível ("Em preparação", e não
`EM_PREPARACAO`). Estas funções viram filtros do Jinja em
`renderizacao.py`.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Final

from filmes_e_cubos.domain.value_objects.escala_avaliacao import EscalaAvaliacao
from filmes_e_cubos.domain.value_objects.status import (
    StatusIndicacao,
    StatusRodada,
    StatusTemporadaOscar,
    TipoCategoriaOscar,
)
from filmes_e_cubos.domain.value_objects.status_avaliacao import StatusAvaliacao
from filmes_e_cubos.domain.value_objects.tipo_indicacao import TipoIndicacao

ROTULOS: Final[dict[Enum, str]] = {
    StatusRodada.ABERTA: "Aberta",
    StatusRodada.ENCERRADA: "Encerrada",
    StatusIndicacao.PENDENTE: "Pendente",
    StatusIndicacao.SORTEADA: "Sorteada",
    StatusIndicacao.ASSISTIDA: "Assistida",
    TipoIndicacao.NORMAL: "Normal",
    TipoIndicacao.DEMOCRACIA: "Democracia",
    StatusAvaliacao.NOTA_REGISTRADA: "Nota registrada",
    StatusAvaliacao.DORMINHOCO: "Dorminhoco",
    StatusTemporadaOscar.EM_PREPARACAO: "Em preparação",
    StatusTemporadaOscar.ABERTA_PARA_INDICACOES: "Aberta para indicações",
    StatusTemporadaOscar.EM_VOTACAO: "Em votação",
    StatusTemporadaOscar.APURADA: "Apurada",
    StatusTemporadaOscar.ENCERRADA: "Encerrada",
    TipoCategoriaOscar.FIXA: "Fixa",
    TipoCategoriaOscar.VARIAVEL: "Variável",
}
"""Rótulo de cada membro das enumerações do domínio exibidas na web."""


def rotulo(valor: Enum) -> str:
    """O rótulo legível de um membro de enumeração do domínio."""
    return ROTULOS[valor]


def formatar_data(valor: date | None) -> str:
    """`2026-09-24` -> `24/09/2026`; `None` vira travessão."""
    return valor.strftime("%d/%m/%Y") if valor is not None else "—"


def formatar_data_hora(valor: datetime) -> str:
    """`2026-09-24 21:30` -> `24/09/2026 21:30`."""
    return valor.strftime("%d/%m/%Y %H:%M")


def formatar_decimal(valor: Decimal) -> str:
    """Decimal em notação brasileira, sem zeros inúteis: `4.50` -> `4,5`; `5.0` -> `5`."""
    texto = format(valor, "f")  # notação fixa: nunca `1E+1`
    if "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto.replace(".", ",")


def notas_da_escala(escala: EscalaAvaliacao) -> list[Decimal]:
    """Todas as notas que a escala aceita, da maior para a menor (ordem de um `<select>`)."""
    notas: list[Decimal] = []
    nota = escala.nota_maxima
    while nota >= escala.nota_minima:
        notas.append(nota)
        nota -= escala.passo
    return notas
