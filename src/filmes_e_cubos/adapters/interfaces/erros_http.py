"""Classificação dos erros de domínio em status HTTP, compartilhada pela API e pela web.

O domínio não classifica seus erros em "dado inválido" e "conflito com o
estado atual" — essa distinção só existe no HTTP. Por isso a
classificação mora na camada de interface, em `STATUS_HTTP_POR_ERRO`, e é
explícita para cada erro: um teste garante que nenhuma exceção de domínio
nova fique de fora sem que alguém decida qual status ela merece.
"""

from __future__ import annotations

import re
from http import HTTPStatus
from typing import Final

from filmes_e_cubos.domain.exceptions.avaliacao import (
    AvaliacaoDuplicadaError,
    EscalaAvaliacaoInvalidaError,
    MembroAusenteNaSessaoError,
    NotaForaDaEscalaError,
    NotaInvalidaError,
)
from filmes_e_cubos.domain.exceptions.base import DomainError, EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.clube import (
    NomeClubeObrigatorioError,
    TamanhoRodadaInvalidoError,
)
from filmes_e_cubos.domain.exceptions.filme import (
    DuracaoFilmeInvalidaError,
    TituloFilmeObrigatorioError,
)
from filmes_e_cubos.domain.exceptions.indicacao import (
    IndicacaoDuplicadaError,
    TransicaoDeStatusInvalidaError,
)
from filmes_e_cubos.domain.exceptions.membro import MembroInativoError, NomeMembroObrigatorioError
from filmes_e_cubos.domain.exceptions.oscar import (
    AcaoForaDaFaseError,
    CategoriaJaApuradaError,
    FilmeNaoAssistidoError,
    FilmeNaoAssistidoNoAnoDaTemporadaError,
    NomeacaoInvalidaError,
    NomeCategoriaObrigatorioError,
    TemporadaOscarInvalidaError,
    VencedorDemocraciaNaoInformadoError,
)
from filmes_e_cubos.domain.exceptions.rodada import (
    RodadaJaAbertaError,
    RodadaJaEncerradaError,
    RodadaLotadaError,
    RodadaNaoEncerravelError,
)
from filmes_e_cubos.domain.exceptions.sorteio import (
    IndicacaoNaoElegivelParaSorteioError,
    NenhumaIndicacaoElegivelError,
)

_NAO_ENCONTRADO: Final[tuple[type[DomainError], ...]] = (EntidadeNaoEncontradaError,)

# A requisição é válida, mas colide com o estado atual (tentar de novo não
# adianta até que o estado mude).
_CONFLITO: Final[tuple[type[DomainError], ...]] = (
    AcaoForaDaFaseError,
    AvaliacaoDuplicadaError,
    CategoriaJaApuradaError,
    IndicacaoDuplicadaError,
    MembroAusenteNaSessaoError,
    MembroInativoError,
    NenhumaIndicacaoElegivelError,
    RodadaJaAbertaError,
    RodadaJaEncerradaError,
    RodadaLotadaError,
    RodadaNaoEncerravelError,
    TemporadaOscarInvalidaError,
    TransicaoDeStatusInvalidaError,
)

# Os dados enviados violam uma regra de negócio, independentemente do estado.
_ENTRADA_INVALIDA: Final[tuple[type[DomainError], ...]] = (
    DuracaoFilmeInvalidaError,
    EscalaAvaliacaoInvalidaError,
    FilmeNaoAssistidoError,
    FilmeNaoAssistidoNoAnoDaTemporadaError,
    NomeacaoInvalidaError,
    NomeCategoriaObrigatorioError,
    NomeClubeObrigatorioError,
    NomeMembroObrigatorioError,
    NotaForaDaEscalaError,
    NotaInvalidaError,
    TamanhoRodadaInvalidoError,
    TituloFilmeObrigatorioError,
    VencedorDemocraciaNaoInformadoError,
)

# Defeito do próprio servidor: o sorteador devolveu um candidato inexistente.
# O cliente não fez nada de errado.
_FALHA_INTERNA: Final[tuple[type[DomainError], ...]] = (IndicacaoNaoElegivelParaSorteioError,)

STATUS_HTTP_POR_ERRO: Final[dict[type[DomainError], int]] = {
    **dict.fromkeys(_NAO_ENCONTRADO, HTTPStatus.NOT_FOUND),
    **dict.fromkeys(_CONFLITO, HTTPStatus.CONFLICT),
    **dict.fromkeys(_ENTRADA_INVALIDA, HTTPStatus.UNPROCESSABLE_ENTITY),
    **dict.fromkeys(_FALHA_INTERNA, HTTPStatus.INTERNAL_SERVER_ERROR),
}
"""Status HTTP de cada erro de domínio. Um erro não listado cai em 422."""


def status_http_do_erro(erro: DomainError) -> int:
    """O status mais específico classificado para o erro (ou 422, se nenhum)."""
    for tipo in type(erro).__mro__:
        if tipo in STATUS_HTTP_POR_ERRO:
            return int(STATUS_HTTP_POR_ERRO[tipo])
    return int(HTTPStatus.UNPROCESSABLE_ENTITY)


def codigo_do_erro(tipo: type[Exception]) -> str:
    """Identificador estável de um erro: `RodadaJaAbertaError` -> `"rodada_ja_aberta"`."""
    nome = tipo.__name__.removesuffix("Error")
    return re.sub(r"(?<!^)(?=[A-Z])", "_", nome).lower()
