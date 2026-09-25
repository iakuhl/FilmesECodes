"""Cenário compartilhado pelos testes dos casos de uso da votação do Óscar."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from filmes_e_cubos.application.use_cases.confirmar_cedula import (
    ConfirmarCedula,
    ResultadoDaConfirmacao,
)
from filmes_e_cubos.application.use_cases.registrar_voto import RegistrarVoto
from filmes_e_cubos.domain.entities.categoria_oscar import CategoriaOscar
from filmes_e_cubos.domain.entities.cedula import Cedula
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.entities.turno_de_votacao import TurnoDeVotacao
from filmes_e_cubos.domain.entities.votacao_oscar import VotacaoOscar
from filmes_e_cubos.domain.value_objects.identificadores import (
    ClubeId,
    MembroId,
    NomeacaoOscarId,
    TemporadaOscarId,
)
from filmes_e_cubos.domain.value_objects.status import StatusTemporadaOscar, TipoCategoriaOscar
from tests.application.fakes.categoria_oscar_repositorio_fake import CategoriaOscarRepositorioFake
from tests.application.fakes.cedula_repositorio_fake import CedulaRepositorioFake
from tests.application.fakes.relogio_fake import RelogioFake
from tests.application.fakes.temporada_oscar_repositorio_fake import (
    TemporadaOscarRepositorioFake,
)
from tests.application.fakes.turno_de_votacao_repositorio_fake import (
    TurnoDeVotacaoRepositorioFake,
)
from tests.application.fakes.votacao_oscar_repositorio_fake import VotacaoOscarRepositorioFake

AGORA = datetime(2024, 12, 8, 21, 0)


class CenarioDeVotacao:
    """Uma edição em votação, com Iano e Bia como eleitores e duas categorias em disputa.

    Cada categoria tem duas nomeações no 1º turno, acessíveis pelo turno
    (`veiculo.candidatas`, `crianca.candidatas`).
    """

    def __init__(self) -> None:
        self.temporadas = TemporadaOscarRepositorioFake()
        self.categorias = CategoriaOscarRepositorioFake()
        self.votacoes = VotacaoOscarRepositorioFake()
        self.turnos = TurnoDeVotacaoRepositorioFake()
        self.cedulas = CedulaRepositorioFake()
        self.temporada = TemporadaOscar(
            id=TemporadaOscarId(uuid4()),
            clube_id=ClubeId(uuid4()),
            ano=2024,
            nome="Óscar 2024",
            status=StatusTemporadaOscar.EM_VOTACAO,
            nomeacoes_por_categoria=2,
        )
        self.temporadas.salvar(self.temporada)
        self.iano, self.bia = MembroId(uuid4()), MembroId(uuid4())
        self.votacao = VotacaoOscar.iniciar(
            temporada_id=self.temporada.id, eleitores=[self.iano, self.bia], momento=AGORA
        )
        self.votacoes.salvar(self.votacao)
        self.veiculo = self._categoria_em_disputa("Melhor veículo")
        self.crianca = self._categoria_em_disputa("Pior criança")
        self.registrar_voto = RegistrarVoto(
            self.temporadas, self.categorias, self.votacoes, self.turnos, self.cedulas
        )
        self.confirmar_cedula = ConfirmarCedula(
            self.temporadas,
            self.categorias,
            self.votacoes,
            self.turnos,
            self.cedulas,
            RelogioFake(AGORA),
        )

    def _categoria_em_disputa(self, nome: str) -> TurnoDeVotacao:
        categoria = CategoriaOscar.criar(
            temporada_id=self.temporada.id, nome=nome, tipo=TipoCategoriaOscar.VARIAVEL
        )
        self.categorias.salvar(categoria)
        turno = TurnoDeVotacao.abrir_primeiro(
            categoria_id=categoria.id,
            candidatas=[NomeacaoOscarId(uuid4()), NomeacaoOscarId(uuid4())],
        )
        self.turnos.salvar(turno)
        return turno

    def votar(self, membro_id: MembroId, turno: TurnoDeVotacao, *escolhas: int) -> Cedula:
        """Vota pelas posições das candidatas no turno (0 é a primeira)."""
        return self.registrar_voto.executar(
            categoria_id=turno.categoria_id,
            membro_id=membro_id,
            escolhas=[turno.candidatas[posicao] for posicao in escolhas],
        )

    def confirmar(self, membro_id: MembroId) -> ResultadoDaConfirmacao:
        return self.confirmar_cedula.executar(temporada_id=self.temporada.id, membro_id=membro_id)

    def turno_aberto(self, turno: TurnoDeVotacao) -> TurnoDeVotacao | None:
        """O turno aberto da categoria desse turno, se houver."""
        return next(
            (
                outro
                for outro in self.turnos.listar_por_categoria(turno.categoria_id)
                if outro.aberto
            ),
            None,
        )
