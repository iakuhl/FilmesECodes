"""Caso de uso: adicionar uma indicação extra DEMOCRACIA à rodada corrente."""

from __future__ import annotations

from filmes_e_cubos.application.ports.filme_repository import FilmeRepository
from filmes_e_cubos.application.ports.indicacao_repository import IndicacaoRepository
from filmes_e_cubos.application.ports.relogio_service import RelogioService
from filmes_e_cubos.application.ports.rodada_repository import RodadaRepository
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.rodada import RodadaJaEncerradaError
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId, FilmeId


class AdicionarFilmeDemocracia:
    """Registra uma sessão extra DEMOCRACIA na rodada aberta do clube.

    Não é uma substituição de nenhuma indicação normal, por isso não
    passa pelas checagens de cota nem de duplicidade por membro que
    `IndicarFilme` aplica — o filme é escolhido pelo grupo, não por um
    membro específico.
    """

    def __init__(
        self,
        indicacao_repository: IndicacaoRepository,
        rodada_repository: RodadaRepository,
        filme_repository: FilmeRepository,
        relogio: RelogioService,
    ) -> None:
        self._indicacoes = indicacao_repository
        self._rodadas = rodada_repository
        self._filmes = filme_repository
        self._relogio = relogio

    def executar(self, *, clube_id: ClubeId, filme_id: FilmeId) -> Indicacao:
        rodada = self._rodadas.buscar_aberta_por_clube(clube_id)
        if rodada is None:
            raise EntidadeNaoEncontradaError(f"Clube {clube_id} não tem rodada aberta.")
        if not rodada.esta_aberta:
            raise RodadaJaEncerradaError(f"Rodada {rodada.id} não está aberta.")

        if self._filmes.buscar_por_id(filme_id) is None:
            raise EntidadeNaoEncontradaError(f"Filme {filme_id} não encontrado.")

        indicacao = Indicacao.criar_democracia(
            rodada_id=rodada.id,
            filme_id=filme_id,
            data_indicacao=self._relogio.hoje(),
        )
        self._indicacoes.salvar(indicacao)
        return indicacao
