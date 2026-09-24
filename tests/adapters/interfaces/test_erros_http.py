"""Testes da classificação dos erros de domínio em status HTTP."""

from __future__ import annotations

import importlib
import pkgutil

import pytest

import filmes_e_cubos.domain.exceptions as pacote_de_excecoes
from filmes_e_cubos.adapters.interfaces.erros_http import (
    STATUS_HTTP_POR_ERRO,
    codigo_do_erro,
    status_http_do_erro,
)
from filmes_e_cubos.domain.exceptions.base import DomainError, EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.rodada import RodadaJaAbertaError


def _todas_as_excecoes_de_dominio() -> set[type[DomainError]]:
    """Toda subclasse de `DomainError` definida no pacote de exceções do domínio.

    Filtra pelo módulo para ignorar subclasses criadas por outros testes.
    """
    for modulo in pkgutil.iter_modules(pacote_de_excecoes.__path__):
        importlib.import_module(f"{pacote_de_excecoes.__name__}.{modulo.name}")
    encontradas: set[type[DomainError]] = set()
    pendentes: list[type[DomainError]] = [DomainError]
    while pendentes:
        for subclasse in pendentes.pop().__subclasses__():
            if subclasse.__module__.startswith(pacote_de_excecoes.__name__):
                encontradas.add(subclasse)
            pendentes.append(subclasse)
    return encontradas


def test_todo_erro_de_dominio_tem_status_http_decidido() -> None:
    """Um erro novo no domínio não pode cair no 422 genérico por esquecimento."""
    sem_classificacao = _todas_as_excecoes_de_dominio() - set(STATUS_HTTP_POR_ERRO)

    assert not sem_classificacao, "Classifique em adapters/interfaces/erros_http.py: " + ", ".join(
        sorted(e.__name__ for e in sem_classificacao)
    )


def test_erro_nao_classificado_cai_em_422() -> None:
    class DesconhecidoDaApiError(DomainError):
        pass

    assert status_http_do_erro(DesconhecidoDaApiError("?")) == 422


def test_subclasse_herda_o_status_da_classificada() -> None:
    class RodadaAindaMaisAbertaError(RodadaJaAbertaError):
        pass

    assert status_http_do_erro(RodadaAindaMaisAbertaError("?")) == 409


@pytest.mark.parametrize(
    ("tipo", "codigo"),
    [
        (RodadaJaAbertaError, "rodada_ja_aberta"),
        (EntidadeNaoEncontradaError, "entidade_nao_encontrada"),
        (DomainError, "domain"),
    ],
)
def test_codigo_do_erro_deriva_do_nome_da_excecao(tipo: type[Exception], codigo: str) -> None:
    assert codigo_do_erro(tipo) == codigo
