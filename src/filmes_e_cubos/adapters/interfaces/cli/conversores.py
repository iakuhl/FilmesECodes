"""Conversão entre o texto que chega pela linha de comando e o domínio.

A CLI recebe tudo como texto; o domínio trabalha com `Decimal`, `Nota` e
enumerações. Manter essa fronteira em um módulo só evita que cada comando
invente sua própria forma de converter (e de errar).

Enumerações de domínio ganham aqui um espelho em minúsculas
(`TipoCategoriaCli`): os membros do domínio usam `auto()`, cujo valor é
um inteiro sem sentido para quem digita um comando. O espelho existe para
o Typer oferecer `[fixa|variavel]` na ajuda e no autocompletar, sem que o
domínio precise saber que existe uma CLI.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from enum import StrEnum

from filmes_e_cubos.adapters.interfaces.cli.erros import CliError
from filmes_e_cubos.domain.value_objects.nota import Nota
from filmes_e_cubos.domain.value_objects.status import TipoCategoriaOscar


class TipoCategoriaCli(StrEnum):
    """Representação textual de `TipoCategoriaOscar` para a linha de comando."""

    FIXA = "fixa"
    VARIAVEL = "variavel"

    def para_dominio(self) -> TipoCategoriaOscar:
        return _TIPOS_DE_CATEGORIA[self]


_TIPOS_DE_CATEGORIA: dict[TipoCategoriaCli, TipoCategoriaOscar] = {
    TipoCategoriaCli.FIXA: TipoCategoriaOscar.FIXA,
    TipoCategoriaCli.VARIAVEL: TipoCategoriaOscar.VARIAVEL,
}


def converter_decimal(texto: str, *, opcao: str) -> Decimal:
    """Converte o texto de uma opção numérica, aceitando vírgula decimal."""
    try:
        return Decimal(texto.replace(",", "."))
    except InvalidOperation as erro:
        raise CliError(f"Valor inválido para {opcao}: {texto!r}.") from erro


def converter_nota(texto: str | None) -> Nota | None:
    """Converte o texto de `--nota`; `None` significa membro dorminhoco.

    A faixa e o passo aceitáveis não são checados aqui: quem valida é a
    `EscalaAvaliacao` do clube, dentro do caso de uso `AvaliarFilme`.
    """
    if texto is None:
        return None
    return Nota.criar(converter_decimal(texto, opcao="--nota"))
