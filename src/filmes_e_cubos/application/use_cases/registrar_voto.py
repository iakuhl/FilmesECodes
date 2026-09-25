"""Caso de uso: registrar (ou trocar) o voto de um eleitor numa categoria do Óscar."""

from __future__ import annotations

from collections.abc import Sequence

from filmes_e_cubos.application.ports.categoria_oscar_repository import CategoriaOscarRepository
from filmes_e_cubos.application.ports.cedula_repository import CedulaRepository
from filmes_e_cubos.application.ports.temporada_oscar_repository import TemporadaOscarRepository
from filmes_e_cubos.application.ports.turno_de_votacao_repository import (
    TurnoDeVotacaoRepository,
)
from filmes_e_cubos.application.ports.votacao_oscar_repository import VotacaoOscarRepository
from filmes_e_cubos.application.use_cases._votacao import votacao_do_eleitor
from filmes_e_cubos.domain.entities.cedula import Cedula
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.oscar import CategoriaForaDoTurnoError
from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    MembroId,
    NomeacaoOscarId,
)


class RegistrarVoto:
    """Grava o voto de um eleitor numa categoria, na cédula dele do turno atual.

    Até confirmar a cédula, o eleitor troca os votos à vontade (decisão
    25 de docs/PENDENCIAS.md). Só votam os eleitores definidos no início
    da votação — inclusive os que foram desativados depois (decisão 23).
    """

    def __init__(
        self,
        temporada_repository: TemporadaOscarRepository,
        categoria_repository: CategoriaOscarRepository,
        votacao_repository: VotacaoOscarRepository,
        turno_repository: TurnoDeVotacaoRepository,
        cedula_repository: CedulaRepository,
    ) -> None:
        self._temporadas = temporada_repository
        self._categorias = categoria_repository
        self._votacoes = votacao_repository
        self._turnos = turno_repository
        self._cedulas = cedula_repository

    def executar(
        self,
        *,
        categoria_id: CategoriaOscarId,
        membro_id: MembroId,
        escolhas: Sequence[NomeacaoOscarId],
    ) -> Cedula:
        categoria = self._categorias.buscar_por_id(categoria_id)
        if categoria is None:
            raise EntidadeNaoEncontradaError(f"Categoria {categoria_id} não encontrada.")
        temporada = self._temporadas.buscar_por_id(categoria.temporada_id)
        if temporada is None:
            raise EntidadeNaoEncontradaError(f"Temporada {categoria.temporada_id} não encontrada.")
        votacao = votacao_do_eleitor(self._votacoes, temporada, membro_id)

        turno = next(
            (turno for turno in self._turnos.listar_por_categoria(categoria_id) if turno.aberto),
            None,
        )
        if turno is None:
            raise CategoriaForaDoTurnoError(
                f"A categoria {categoria.nome} não está em disputa no "
                f"{votacao.turno_atual}º turno da votação."
            )

        cedula = self._cedulas.buscar(votacao.id, votacao.turno_atual, membro_id)
        if cedula is None:
            cedula = Cedula.criar(
                votacao_id=votacao.id, turno=votacao.turno_atual, membro_id=membro_id
            )
        cedula.verificar_aberta()
        cedula.votar(categoria_id, turno.conferir_escolhas(escolhas))
        self._cedulas.salvar(cedula)
        return cedula
