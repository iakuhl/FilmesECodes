"""Fixtures compartilhadas pela suíte de testes."""

from __future__ import annotations

import pytest

from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.value_objects.configuracao_clube import ConfiguracaoClube


@pytest.fixture
def configuracao_padrao() -> ConfiguracaoClube:
    return ConfiguracaoClube.padrao()


@pytest.fixture
def clube(configuracao_padrao: ConfiguracaoClube) -> Clube:
    return Clube.criar(nome="Filmes e Cubos", configuracao=configuracao_padrao)
