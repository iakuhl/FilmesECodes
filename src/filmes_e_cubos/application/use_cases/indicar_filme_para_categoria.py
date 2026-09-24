"""Caso de uso: nomear, para uma categoria do Óscar, um filme já assistido pelo clube."""

from __future__ import annotations

from filmes_e_cubos.application.ports.categoria_oscar_repository import CategoriaOscarRepository
from filmes_e_cubos.application.ports.indicacao_repository import IndicacaoRepository
from filmes_e_cubos.application.ports.nomeacao_oscar_repository import NomeacaoOscarRepository
from filmes_e_cubos.application.ports.sessao_repository import SessaoRepository
from filmes_e_cubos.application.ports.temporada_oscar_repository import TemporadaOscarRepository
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.oscar import (
    FilmeNaoAssistidoError,
    FilmeNaoAssistidoNoAnoDaTemporadaError,
)
from filmes_e_cubos.domain.value_objects.identificadores import CategoriaOscarId, FilmeId


class IndicarFilmeParaCategoria:
    """Nomeia, para uma categoria, um filme assistido pelo clube dentro do
    ano da temporada dessa categoria (sessões DEMOCRACIA contam
    normalmente, pois também geram uma sessão de exibição de verdade).

    A nomeação herda `indicado_por_membro_id` da `Indicacao` semanal
    original assistida (pode ser `None`, se a indicação for DEMOCRACIA) —
    é essa rastreabilidade que permite ao caso de uso
    `ApurarCategoriaOscar` entregar o troféu a quem indicou o filme.
    """

    def __init__(
        self,
        nomeacao_repository: NomeacaoOscarRepository,
        categoria_repository: CategoriaOscarRepository,
        temporada_repository: TemporadaOscarRepository,
        indicacao_repository: IndicacaoRepository,
        sessao_repository: SessaoRepository,
    ) -> None:
        self._nomeacoes = nomeacao_repository
        self._categorias = categoria_repository
        self._temporadas = temporada_repository
        self._indicacoes = indicacao_repository
        self._sessoes = sessao_repository

    def executar(self, *, categoria_id: CategoriaOscarId, filme_id: FilmeId) -> NomeacaoOscar:
        categoria = self._categorias.buscar_por_id(categoria_id)
        if categoria is None:
            raise EntidadeNaoEncontradaError(f"Categoria {categoria_id} não encontrada.")

        temporada = self._temporadas.buscar_por_id(categoria.temporada_id)
        if temporada is None:
            raise EntidadeNaoEncontradaError(f"Temporada {categoria.temporada_id} não encontrada.")

        indicacoes_assistidas = self._indicacoes.listar_assistidas_por_filme(filme_id)
        if not indicacoes_assistidas:
            raise FilmeNaoAssistidoError(f"Filme {filme_id} ainda não foi assistido pelo clube.")

        indicacao_do_ano = self._buscar_indicacao_no_ano(indicacoes_assistidas, temporada.ano)
        if indicacao_do_ano is None:
            raise FilmeNaoAssistidoNoAnoDaTemporadaError(
                f"Filme {filme_id} não foi assistido no ano {temporada.ano} desta temporada."
            )

        nomeacao = NomeacaoOscar.criar(
            categoria_id=categoria_id,
            filme_id=filme_id,
            indicado_por_membro_id=indicacao_do_ano.membro_id,
        )
        self._nomeacoes.salvar(nomeacao)
        return nomeacao

    def _buscar_indicacao_no_ano(
        self, indicacoes_assistidas: list[Indicacao], ano: int
    ) -> Indicacao | None:
        for indicacao in indicacoes_assistidas:
            sessao = self._sessoes.buscar_por_indicacao(indicacao.id)
            if sessao is not None and sessao.data_sessao.year == ano:
                return indicacao
        return None
