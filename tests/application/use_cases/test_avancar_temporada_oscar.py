"""Testes do caso de uso AvancarTemporadaOscar."""

from datetime import date, datetime
from uuid import uuid4

import pytest

from filmes_e_cubos.application.use_cases.avancar_temporada_oscar import AvancarTemporadaOscar
from filmes_e_cubos.domain.entities.categoria_oscar import CategoriaOscar
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.entities.trofeu import Trofeu
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.oscar import (
    TemporadaIncompletaError,
    TemporadaOscarInvalidaError,
)
from filmes_e_cubos.domain.value_objects.identificadores import (
    ClubeId,
    FilmeId,
    MembroId,
    TemporadaOscarId,
)
from filmes_e_cubos.domain.value_objects.status import (
    ModoDeVotacao,
    StatusTemporadaOscar,
    TipoCategoriaOscar,
)
from tests.application.fakes.categoria_oscar_repositorio_fake import CategoriaOscarRepositorioFake
from tests.application.fakes.membro_repositorio_fake import MembroRepositorioFake
from tests.application.fakes.nomeacao_oscar_repositorio_fake import NomeacaoOscarRepositorioFake
from tests.application.fakes.relogio_fake import RelogioFake
from tests.application.fakes.temporada_oscar_repositorio_fake import (
    TemporadaOscarRepositorioFake,
)
from tests.application.fakes.trofeu_repositorio_fake import TrofeuRepositorioFake
from tests.application.fakes.turno_de_votacao_repositorio_fake import (
    TurnoDeVotacaoRepositorioFake,
)
from tests.application.fakes.votacao_oscar_repositorio_fake import VotacaoOscarRepositorioFake

AGORA = datetime(2024, 12, 1, 20, 0)


class Cenario:
    """Uma edição com 2 nomeações por categoria, na fase pedida, num clube com um membro."""

    def __init__(self, status: StatusTemporadaOscar) -> None:
        self.temporadas = TemporadaOscarRepositorioFake()
        self.categorias = CategoriaOscarRepositorioFake()
        self.nomeacoes = NomeacaoOscarRepositorioFake()
        self.trofeus = TrofeuRepositorioFake()
        self.membros = MembroRepositorioFake()
        self.votacoes = VotacaoOscarRepositorioFake()
        self.turnos = TurnoDeVotacaoRepositorioFake()
        self.temporada = TemporadaOscar(
            id=TemporadaOscarId(uuid4()),
            clube_id=ClubeId(uuid4()),
            ano=2024,
            nome="Óscar 2024",
            status=status,
            nomeacoes_por_categoria=2,
        )
        self.temporadas.salvar(self.temporada)
        self.iano = self.membro("Iano")
        self.caso_de_uso = AvancarTemporadaOscar(
            self.temporadas,
            self.categorias,
            self.nomeacoes,
            self.trofeus,
            self.membros,
            self.votacoes,
            self.turnos,
            RelogioFake(AGORA),
        )

    def membro(self, nome: str) -> Membro:
        membro = Membro.criar(
            clube_id=self.temporada.clube_id, nome=nome, data_ingresso=date(2024, 1, 1)
        )
        self.membros.salvar(membro)
        return membro

    def categoria(self, nome: str, *, nomeacoes: int) -> CategoriaOscar:
        categoria = CategoriaOscar.criar(
            temporada_id=self.temporada.id, nome=nome, tipo=TipoCategoriaOscar.VARIAVEL
        )
        self.categorias.salvar(categoria)
        for _ in range(nomeacoes):
            self.nomeacoes.salvar(
                NomeacaoOscar.criar(
                    categoria_id=categoria.id,
                    filme_id=FilmeId(uuid4()),
                    indicado_por_membro_id=MembroId(uuid4()),
                )
            )
        return categoria

    def premiar(self, categoria: CategoriaOscar) -> None:
        nomeacao = self.nomeacoes.listar_por_categoria(categoria.id)[0]
        self.trofeus.salvar(
            Trofeu.emitir(
                categoria_id=categoria.id,
                nomeacao_vencedora_id=nomeacao.id,
                membro_vencedor_id=MembroId(uuid4()),
                data_apuracao=date(2024, 12, 20),
            )
        )

    def avancar(self) -> StatusTemporadaOscar:
        return self.caso_de_uso.executar(temporada_id=self.temporada.id).status


def test_preparacao_abre_para_indicacoes_mesmo_sem_categorias() -> None:
    cenario = Cenario(StatusTemporadaOscar.EM_PREPARACAO)

    assert cenario.avancar() is StatusTemporadaOscar.ABERTA_PARA_INDICACOES
    salva = cenario.temporadas.buscar_por_id(cenario.temporada.id)
    assert salva is not None
    assert salva.status is StatusTemporadaOscar.ABERTA_PARA_INDICACOES


def test_votacao_exige_ao_menos_uma_categoria() -> None:
    cenario = Cenario(StatusTemporadaOscar.ABERTA_PARA_INDICACOES)

    with pytest.raises(TemporadaIncompletaError, match="nenhuma categoria"):
        cenario.avancar()


def test_votacao_exige_todas_as_nomeacoes_em_cada_categoria() -> None:
    cenario = Cenario(StatusTemporadaOscar.ABERTA_PARA_INDICACOES)
    cenario.categoria("Melhor veículo", nomeacoes=2)
    cenario.categoria("Pior criança", nomeacoes=1)

    with pytest.raises(TemporadaIncompletaError, match=r"Pior criança \(1/2\)"):
        cenario.avancar()
    assert cenario.temporada.status is StatusTemporadaOscar.ABERTA_PARA_INDICACOES


def test_com_as_nomeacoes_completas_a_votacao_comeca() -> None:
    cenario = Cenario(StatusTemporadaOscar.ABERTA_PARA_INDICACOES)
    cenario.categoria("Melhor veículo", nomeacoes=2)

    assert cenario.avancar() is StatusTemporadaOscar.EM_VOTACAO


def test_a_votacao_comeca_com_os_membros_ativos_como_eleitores() -> None:
    """Decisão 23: quem estava desativado quando a votação começou não vota."""
    cenario = Cenario(StatusTemporadaOscar.ABERTA_PARA_INDICACOES)
    bia = cenario.membro("Bia")
    caio = cenario.membro("Caio")
    caio.desativar()
    cenario.categoria("Melhor veículo", nomeacoes=2)

    cenario.avancar()

    votacao = cenario.votacoes.buscar_por_temporada(cenario.temporada.id)
    assert votacao is not None
    assert votacao.eleitores == {cenario.iano.id, bia.id}
    assert votacao.turno_atual == 1
    assert votacao.iniciada_em == AGORA
    assert not votacao.encerrada


def test_cada_categoria_abre_o_1o_turno_com_as_nomeacoes_na_ordem() -> None:
    cenario = Cenario(StatusTemporadaOscar.ABERTA_PARA_INDICACOES)
    categorias = [cenario.categoria(nome, nomeacoes=2) for nome in ("Melhor veículo", "Pior")]

    cenario.avancar()

    for categoria in categorias:
        [turno] = cenario.turnos.listar_por_categoria(categoria.id)
        assert turno.numero == 1
        assert turno.modo is ModoDeVotacao.DUPLA
        assert turno.aberto
        assert turno.candidatas == tuple(
            nomeacao.id for nomeacao in cenario.nomeacoes.listar_por_categoria(categoria.id)
        )


def test_votacao_exige_ao_menos_um_membro_ativo() -> None:
    cenario = Cenario(StatusTemporadaOscar.ABERTA_PARA_INDICACOES)
    cenario.iano.desativar()
    categoria = cenario.categoria("Melhor veículo", nomeacoes=2)

    with pytest.raises(TemporadaIncompletaError, match="nenhum membro ativo"):
        cenario.avancar()

    assert cenario.temporada.status is StatusTemporadaOscar.ABERTA_PARA_INDICACOES
    assert cenario.votacoes.buscar_por_temporada(cenario.temporada.id) is None
    assert cenario.turnos.listar_por_categoria(categoria.id) == []


def test_apuracao_exige_resultado_em_toda_categoria() -> None:
    cenario = Cenario(StatusTemporadaOscar.EM_VOTACAO)
    apurada = cenario.categoria("Melhor veículo", nomeacoes=2)
    cenario.categoria("Pior criança", nomeacoes=2)
    cenario.premiar(apurada)

    with pytest.raises(TemporadaIncompletaError, match="Pior criança"):
        cenario.avancar()


def test_com_todas_as_categorias_apuradas_a_edicao_fica_apurada_e_depois_encerra() -> None:
    cenario = Cenario(StatusTemporadaOscar.EM_VOTACAO)
    cenario.premiar(cenario.categoria("Melhor veículo", nomeacoes=2))

    assert cenario.avancar() is StatusTemporadaOscar.APURADA
    assert cenario.avancar() is StatusTemporadaOscar.ENCERRADA


def test_edicao_encerrada_nao_avanca() -> None:
    cenario = Cenario(StatusTemporadaOscar.ENCERRADA)

    with pytest.raises(TemporadaOscarInvalidaError):
        cenario.avancar()


def test_temporada_inexistente_levanta_erro() -> None:
    cenario = Cenario(StatusTemporadaOscar.EM_PREPARACAO)

    with pytest.raises(EntidadeNaoEncontradaError):
        cenario.caso_de_uso.executar(temporada_id=TemporadaOscarId(uuid4()))
