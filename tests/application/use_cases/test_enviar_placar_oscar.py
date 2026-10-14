"""Testes do caso de uso EnviarPlacarOscar."""

from __future__ import annotations

from datetime import date, datetime
from uuid import uuid4

import pytest

from filmes_e_cubos.application.use_cases.enviar_placar_oscar import EnviarPlacarOscar
from filmes_e_cubos.domain.entities.categoria_oscar import CategoriaOscar
from filmes_e_cubos.domain.entities.filme import Filme
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.entities.turno_de_votacao import TurnoDeVotacao
from filmes_e_cubos.domain.entities.votacao_oscar import VotacaoOscar
from filmes_e_cubos.domain.exceptions.email import EnderecoDeEmailInvalidoError
from filmes_e_cubos.domain.exceptions.oscar import AcaoForaDaFaseError, VotacaoEmAndamentoError
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId, TemporadaOscarId
from filmes_e_cubos.domain.value_objects.status import StatusTemporadaOscar, TipoCategoriaOscar
from tests.application.fakes.categoria_oscar_repositorio_fake import CategoriaOscarRepositorioFake
from tests.application.fakes.enviador_de_email_fake import EnviadorDeEmailFake
from tests.application.fakes.filme_repositorio_fake import FilmeRepositorioFake
from tests.application.fakes.membro_repositorio_fake import MembroRepositorioFake
from tests.application.fakes.nomeacao_oscar_repositorio_fake import NomeacaoOscarRepositorioFake
from tests.application.fakes.temporada_oscar_repositorio_fake import (
    TemporadaOscarRepositorioFake,
)
from tests.application.fakes.turno_de_votacao_repositorio_fake import (
    TurnoDeVotacaoRepositorioFake,
)
from tests.application.fakes.votacao_oscar_repositorio_fake import VotacaoOscarRepositorioFake

FIM = datetime(2024, 12, 8, 22, 0)


class Cenario:
    """Uma edição com a votação de Iano e Bia já terminada.

    "Melhor veículo" se decidiu no 1º turno (Parasita, de Iano); "Pior
    criança" empatou e foi decidida por classificação (Duna, democracia).
    """

    def __init__(self) -> None:
        self.temporadas = TemporadaOscarRepositorioFake()
        self.categorias = CategoriaOscarRepositorioFake()
        self.nomeacoes = NomeacaoOscarRepositorioFake()
        self.filmes = FilmeRepositorioFake()
        self.membros = MembroRepositorioFake()
        self.votacoes = VotacaoOscarRepositorioFake()
        self.turnos = TurnoDeVotacaoRepositorioFake()
        self.enviador = EnviadorDeEmailFake()
        self.temporada = TemporadaOscar(
            id=TemporadaOscarId(uuid4()),
            clube_id=ClubeId(uuid4()),
            ano=2024,
            nome="Óscar 2024",
            status=StatusTemporadaOscar.EM_VOTACAO,
            nomeacoes_por_categoria=2,
        )
        self.temporadas.salvar(self.temporada)
        self.iano, self.bia = (self._membro(nome) for nome in ("Iano", "Bia"))
        self.votacao = VotacaoOscar.iniciar(
            temporada_id=self.temporada.id, eleitores=[self.iano.id, self.bia.id], momento=FIM
        )
        self.votacoes.salvar(self.votacao)

        parasita, tar = self._nomeacoes(
            "Melhor veículo", ("Parasita", self.iano), ("Tár", self.bia)
        )
        primeiro = TurnoDeVotacao.abrir_primeiro(
            categoria_id=parasita.categoria_id, candidatas=[tar.id, parasita.id]
        )
        assert primeiro.apurar([(parasita.id, tar.id), (parasita.id, tar.id)], momento=FIM) is None
        self.turnos.salvar(primeiro)

        duna, coco = self._nomeacoes("Pior criança", ("Duna", None), ("Coco", self.iano))
        empate = TurnoDeVotacao.abrir_primeiro(
            categoria_id=duna.categoria_id, candidatas=[duna.id, coco.id]
        )
        desempate = empate.apurar([(duna.id, coco.id), (coco.id, duna.id)], momento=FIM)
        assert desempate is not None
        assert desempate.apurar([(duna.id, coco.id), (duna.id, coco.id)], momento=FIM) is None
        self.turnos.salvar(empate)
        self.turnos.salvar(desempate)
        self.votacao.encerrar(FIM)

        self.caso_de_uso = EnviarPlacarOscar(
            self.temporadas,
            self.categorias,
            self.nomeacoes,
            self.filmes,
            self.membros,
            self.votacoes,
            self.turnos,
            self.enviador,
        )

    def _membro(self, nome: str) -> Membro:
        membro = Membro.criar(
            clube_id=self.temporada.clube_id, nome=nome, data_ingresso=date(2024, 1, 1)
        )
        self.membros.salvar(membro)
        return membro

    def _nomeacoes(self, categoria: str, *filmes: tuple[str, Membro | None]) -> list[NomeacaoOscar]:
        nova = CategoriaOscar.criar(
            temporada_id=self.temporada.id, nome=categoria, tipo=TipoCategoriaOscar.VARIAVEL
        )
        self.categorias.salvar(nova)
        nomeacoes = []
        for titulo, indicador in filmes:
            filme = Filme.criar(titulo=titulo)
            self.filmes.salvar(filme)
            nomeacao = NomeacaoOscar.criar(
                categoria_id=nova.id,
                filme_id=filme.id,
                indicado_por_membro_id=indicador.id if indicador else None,
            )
            self.nomeacoes.salvar(nomeacao)
            nomeacoes.append(nomeacao)
        return nomeacoes

    def enviar(self, destinatario: str = "cerimonia@clube.com") -> str:
        self.caso_de_uso.executar(temporada_id=self.temporada.id, destinatario=destinatario)
        return self.enviador.enviadas[-1].corpo


def test_placar_vai_para_o_endereco_informado() -> None:
    cenario = Cenario()

    endereco = cenario.caso_de_uso.executar(
        temporada_id=cenario.temporada.id, destinatario=" cerimonia@clube.com "
    )

    [mensagem] = cenario.enviador.enviadas
    assert str(endereco) == str(mensagem.destinatario) == "cerimonia@clube.com"
    assert mensagem.assunto == "Placar do Óscar 2024"


def test_placar_traz_os_pontos_de_cada_turno_em_ordem() -> None:
    corpo = Cenario().enviar()

    assert "Eleitores (2): Bia, Iano." in corpo
    veiculo = corpo[corpo.index("MELHOR VEÍCULO") : corpo.index("PIOR CRIANÇA")]
    assert veiculo.index("4 pontos  Parasita — indicado por Iano") < veiculo.index(
        "2 pontos  Tár — indicado por Bia"
    )
    crianca = corpo[corpo.index("PIOR CRIANÇA") :]
    assert "1º turno — 1ª opção vale 2 pontos; 2ª opção, 1" in crianca
    assert "Empate no topo: as empatadas foram ao 2º turno." in crianca
    assert "2º turno — classificação: o 1º lugar vale 2 pontos; o último, 1" in crianca
    assert "4 pontos  Duna — sessão democracia" in crianca
    assert "o grupo escolhe quem leva o troféu" in crianca


def test_placar_pode_ser_reenviado() -> None:
    cenario = Cenario()

    cenario.enviar("errado@clube.com")
    cenario.enviar("certo@clube.com")

    assert [str(m.destinatario) for m in cenario.enviador.enviadas] == [
        "errado@clube.com",
        "certo@clube.com",
    ]


def test_sem_votacao_terminada_nao_ha_placar() -> None:
    cenario = Cenario()
    cenario.votacoes.salvar(
        VotacaoOscar.iniciar(
            temporada_id=cenario.temporada.id, eleitores=[cenario.iano.id], momento=FIM
        )
    )

    with pytest.raises(VotacaoEmAndamentoError):
        cenario.enviar()
    assert cenario.enviador.enviadas == []


def test_edicao_encerrada_nao_envia_mais() -> None:
    cenario = Cenario()
    cenario.temporada.avancar_para(StatusTemporadaOscar.APURADA)
    cenario.temporada.avancar_para(StatusTemporadaOscar.ENCERRADA)

    with pytest.raises(AcaoForaDaFaseError, match="encerrada"):
        cenario.enviar()


def test_edicao_que_nao_foi_a_votacao() -> None:
    cenario = Cenario()
    outra = TemporadaOscar.abrir(clube_id=cenario.temporada.clube_id, ano=2025, nome="Óscar 2025")
    cenario.temporadas.salvar(outra)

    with pytest.raises(AcaoForaDaFaseError, match="ainda não foi à votação"):
        cenario.caso_de_uso.executar(temporada_id=outra.id, destinatario="a@b.com")


def test_endereco_invalido_e_recusado() -> None:
    cenario = Cenario()

    with pytest.raises(EnderecoDeEmailInvalidoError):
        cenario.enviar("cerimonia")
    assert cenario.enviador.enviadas == []
