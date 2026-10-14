"""Testes do caso de uso RegistrarVencedorOscar (decisão 29 de docs/PENDENCIAS.md)."""

from __future__ import annotations

from datetime import date, datetime
from uuid import uuid4

import pytest

from filmes_e_cubos.application.use_cases.registrar_vencedor_oscar import RegistrarVencedorOscar
from filmes_e_cubos.domain.entities.categoria_oscar import CategoriaOscar
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.entities.votacao_oscar import VotacaoOscar
from filmes_e_cubos.domain.exceptions.oscar import (
    AcaoForaDaFaseError,
    CategoriaJaApuradaError,
    EscolhaDoGrupoNecessariaError,
    MembroDeOutroClubeError,
    NomeacaoInvalidaError,
    VotacaoEmAndamentoError,
)
from filmes_e_cubos.domain.value_objects.identificadores import (
    ClubeId,
    FilmeId,
    MembroId,
    TemporadaOscarId,
)
from filmes_e_cubos.domain.value_objects.status import StatusTemporadaOscar, TipoCategoriaOscar
from tests.application.fakes.categoria_oscar_repositorio_fake import CategoriaOscarRepositorioFake
from tests.application.fakes.membro_repositorio_fake import MembroRepositorioFake
from tests.application.fakes.nomeacao_oscar_repositorio_fake import NomeacaoOscarRepositorioFake
from tests.application.fakes.relogio_fake import RelogioFake
from tests.application.fakes.temporada_oscar_repositorio_fake import (
    TemporadaOscarRepositorioFake,
)
from tests.application.fakes.trofeu_repositorio_fake import TrofeuRepositorioFake
from tests.application.fakes.votacao_oscar_repositorio_fake import VotacaoOscarRepositorioFake

AGORA = datetime(2024, 12, 20, 22, 0)


class Cenario:
    """Edição em votação, já terminada; a categoria tem uma nomeação de Iano e uma de
    filme democracia. Bia é do clube; Duda, de outro.
    """

    def __init__(self) -> None:
        self.temporadas = TemporadaOscarRepositorioFake()
        self.categorias = CategoriaOscarRepositorioFake()
        self.nomeacoes = NomeacaoOscarRepositorioFake()
        self.votacoes = VotacaoOscarRepositorioFake()
        self.membros = MembroRepositorioFake()
        self.trofeus = TrofeuRepositorioFake()
        clube = ClubeId(uuid4())
        self.temporada = TemporadaOscar(
            id=TemporadaOscarId(uuid4()),
            clube_id=clube,
            ano=2024,
            nome="Óscar 2024",
            status=StatusTemporadaOscar.EM_VOTACAO,
            nomeacoes_por_categoria=2,
        )
        self.temporadas.salvar(self.temporada)
        self.iano, self.bia = (self._membro(nome, clube) for nome in ("Iano", "Bia"))
        self.duda = self._membro("Duda", ClubeId(uuid4()))
        self.votacao = VotacaoOscar.iniciar(
            temporada_id=self.temporada.id, eleitores=[self.iano.id], momento=AGORA
        )
        self.votacao.encerrar(AGORA)
        self.votacoes.salvar(self.votacao)
        self.categoria = CategoriaOscar.criar(
            temporada_id=self.temporada.id, nome="Melhor veículo", tipo=TipoCategoriaOscar.VARIAVEL
        )
        self.categorias.salvar(self.categoria)
        self.do_iano, self.democracia = (
            NomeacaoOscar.criar(
                categoria_id=self.categoria.id, filme_id=FilmeId(uuid4()), indicado_por_membro_id=m
            )
            for m in (self.iano.id, None)
        )
        for nomeacao in (self.do_iano, self.democracia):
            self.nomeacoes.salvar(nomeacao)
        self.caso_de_uso = RegistrarVencedorOscar(
            self.trofeus,
            self.categorias,
            self.nomeacoes,
            self.temporadas,
            self.votacoes,
            self.membros,
            RelogioFake(AGORA),
        )

    def _membro(self, nome: str, clube: ClubeId) -> Membro:
        membro = Membro.criar(clube_id=clube, nome=nome, data_ingresso=date(2024, 1, 1))
        self.membros.salvar(membro)
        return membro


def test_trofeu_vai_para_quem_indicou_a_vencedora() -> None:
    cenario = Cenario()

    trofeu = cenario.caso_de_uso.executar(
        categoria_id=cenario.categoria.id, nomeacao_id=cenario.do_iano.id
    )

    assert trofeu.membro_vencedor_id == cenario.iano.id
    assert trofeu.nomeacao_vencedora_id == cenario.do_iano.id
    assert trofeu.data_apuracao == AGORA.date()
    assert cenario.trofeus.buscar_por_categoria(cenario.categoria.id) is trofeu


def test_escolha_do_grupo_e_ignorada_quando_ha_quem_indicou() -> None:
    cenario = Cenario()

    trofeu = cenario.caso_de_uso.executar(
        categoria_id=cenario.categoria.id,
        nomeacao_id=cenario.do_iano.id,
        membro_escolhido_id=cenario.bia.id,
    )

    assert trofeu.membro_vencedor_id == cenario.iano.id


def test_filme_democracia_exige_a_escolha_do_grupo() -> None:
    cenario = Cenario()

    with pytest.raises(EscolhaDoGrupoNecessariaError, match="democracia"):
        cenario.caso_de_uso.executar(
            categoria_id=cenario.categoria.id, nomeacao_id=cenario.democracia.id
        )
    trofeu = cenario.caso_de_uso.executar(
        categoria_id=cenario.categoria.id,
        nomeacao_id=cenario.democracia.id,
        membro_escolhido_id=cenario.bia.id,
    )

    assert trofeu.membro_vencedor_id == cenario.bia.id


def test_empate_absoluto_vai_para_quem_o_grupo_escolheu() -> None:
    cenario = Cenario()

    with pytest.raises(EscolhaDoGrupoNecessariaError, match="empate absoluto"):
        cenario.caso_de_uso.executar(categoria_id=cenario.categoria.id)
    trofeu = cenario.caso_de_uso.executar(
        categoria_id=cenario.categoria.id, membro_escolhido_id=cenario.bia.id
    )

    assert trofeu.nomeacao_vencedora_id is None
    assert trofeu.membro_vencedor_id == cenario.bia.id


def test_escolhido_precisa_ser_do_clube() -> None:
    """Interpretação 3."""
    cenario = Cenario()

    with pytest.raises(MembroDeOutroClubeError):
        cenario.caso_de_uso.executar(
            categoria_id=cenario.categoria.id, membro_escolhido_id=cenario.duda.id
        )


def test_nomeacao_de_outra_categoria_e_recusada() -> None:
    cenario = Cenario()
    outra = NomeacaoOscar.criar(
        categoria_id=CategoriaOscar.criar(
            temporada_id=cenario.temporada.id, nome="Outra", tipo=TipoCategoriaOscar.FIXA
        ).id,
        filme_id=FilmeId(uuid4()),
        indicado_por_membro_id=MembroId(cenario.iano.id),
    )
    cenario.nomeacoes.salvar(outra)

    with pytest.raises(NomeacaoInvalidaError):
        cenario.caso_de_uso.executar(categoria_id=cenario.categoria.id, nomeacao_id=outra.id)


def test_vencedor_so_depois_da_votacao() -> None:
    cenario = Cenario()
    cenario.votacoes.salvar(
        VotacaoOscar.iniciar(
            temporada_id=cenario.temporada.id, eleitores=[cenario.iano.id], momento=AGORA
        )
    )

    with pytest.raises(VotacaoEmAndamentoError):
        cenario.caso_de_uso.executar(
            categoria_id=cenario.categoria.id, nomeacao_id=cenario.do_iano.id
        )


def test_so_com_a_edicao_em_votacao() -> None:
    cenario = Cenario()
    cenario.temporada.avancar_para(StatusTemporadaOscar.APURADA)

    with pytest.raises(AcaoForaDaFaseError):
        cenario.caso_de_uso.executar(
            categoria_id=cenario.categoria.id, nomeacao_id=cenario.do_iano.id
        )


def test_vencedor_nao_muda_depois_de_registrado() -> None:
    """Interpretação 14."""
    cenario = Cenario()
    cenario.caso_de_uso.executar(categoria_id=cenario.categoria.id, nomeacao_id=cenario.do_iano.id)

    with pytest.raises(CategoriaJaApuradaError):
        cenario.caso_de_uso.executar(
            categoria_id=cenario.categoria.id, nomeacao_id=cenario.democracia.id
        )
