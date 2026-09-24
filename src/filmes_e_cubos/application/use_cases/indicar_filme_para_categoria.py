"""Caso de uso: nomear, para uma categoria do Óscar, um filme já assistido pelo clube."""

from __future__ import annotations

from filmes_e_cubos.application.ports.categoria_oscar_repository import CategoriaOscarRepository
from filmes_e_cubos.application.ports.indicacao_repository import IndicacaoRepository
from filmes_e_cubos.application.ports.nomeacao_oscar_repository import NomeacaoOscarRepository
from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.oscar import FilmeNaoAssistidoError
from filmes_e_cubos.domain.value_objects.identificadores import CategoriaOscarId, FilmeId


class IndicarFilmeParaCategoria:
    """Nomeia um filme já assistido pelo clube para concorrer em uma categoria.

    A nomeação herda `indicado_por_membro_id` da `Indicacao` semanal
    original assistida — é essa rastreabilidade que permite ao caso de uso
    `ApurarCategoriaOscar` entregar o troféu a quem indicou o filme.
    """

    def __init__(
        self,
        nomeacao_repository: NomeacaoOscarRepository,
        categoria_repository: CategoriaOscarRepository,
        indicacao_repository: IndicacaoRepository,
    ) -> None:
        self._nomeacoes = nomeacao_repository
        self._categorias = categoria_repository
        self._indicacoes = indicacao_repository

    def executar(self, *, categoria_id: CategoriaOscarId, filme_id: FilmeId) -> NomeacaoOscar:
        if self._categorias.buscar_por_id(categoria_id) is None:
            raise EntidadeNaoEncontradaError(f"Categoria {categoria_id} não encontrada.")

        indicacao_assistida = self._indicacoes.buscar_assistida_por_filme(filme_id)
        if indicacao_assistida is None:
            raise FilmeNaoAssistidoError(f"Filme {filme_id} ainda não foi assistido pelo clube.")

        nomeacao = NomeacaoOscar.criar(
            categoria_id=categoria_id,
            filme_id=filme_id,
            indicado_por_membro_id=indicacao_assistida.membro_id,
        )
        self._nomeacoes.salvar(nomeacao)
        return nomeacao
