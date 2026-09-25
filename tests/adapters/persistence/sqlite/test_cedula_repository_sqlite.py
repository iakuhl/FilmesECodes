"""Testes de integração de `CedulaRepositorioSqlite` contra um SQLite real."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Engine

from filmes_e_cubos.adapters.persistence.sqlite.cedula_repository_sqlite import (
    CedulaRepositorioSqlite,
)
from filmes_e_cubos.domain.entities.cedula import Cedula
from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    MembroId,
    NomeacaoOscarId,
    VotacaoOscarId,
)

CONFIRMACAO = datetime(2024, 12, 8, 21, 0)
VEICULO, CRIANCA = CategoriaOscarId(uuid4()), CategoriaOscarId(uuid4())


def _classificacao() -> list[NomeacaoOscarId]:
    return [NomeacaoOscarId(uuid4()) for _ in range(4)]


def test_salvar_e_buscar_com_as_escolhas_em_ordem(engine: Engine) -> None:
    repositorio = CedulaRepositorioSqlite(engine)
    cedula = Cedula.criar(votacao_id=VotacaoOscarId(uuid4()), turno=2, membro_id=MembroId(uuid4()))
    ordem = _classificacao()
    dupla = [NomeacaoOscarId(uuid4()), NomeacaoOscarId(uuid4())]
    cedula.votar(VEICULO, ordem)
    cedula.votar(CRIANCA, dupla)

    repositorio.salvar(cedula)
    encontrada = repositorio.buscar(cedula.votacao_id, 2, cedula.membro_id)

    assert encontrada is not None
    assert encontrada.id == cedula.id
    assert encontrada.escolhas == {VEICULO: tuple(ordem), CRIANCA: tuple(dupla)}
    assert not encontrada.confirmada


def test_troca_de_voto_e_confirmacao_sao_gravadas(engine: Engine) -> None:
    repositorio = CedulaRepositorioSqlite(engine)
    cedula = Cedula.criar(votacao_id=VotacaoOscarId(uuid4()), turno=1, membro_id=MembroId(uuid4()))
    cedula.votar(VEICULO, _classificacao())
    repositorio.salvar(cedula)

    nova = _classificacao()
    cedula.votar(VEICULO, nova)
    cedula.confirmar([VEICULO], momento=CONFIRMACAO)
    repositorio.salvar(cedula)

    encontrada = repositorio.buscar(cedula.votacao_id, 1, cedula.membro_id)
    assert encontrada is not None
    assert encontrada.escolhas == {VEICULO: tuple(nova)}
    assert encontrada.confirmada_em == CONFIRMACAO


def test_listar_por_turno_separa_os_turnos(engine: Engine) -> None:
    repositorio = CedulaRepositorioSqlite(engine)
    votacao_id = VotacaoOscarId(uuid4())
    iano, bia = MembroId(uuid4()), MembroId(uuid4())
    for membro_id, turno in ((iano, 1), (bia, 1), (iano, 2)):
        repositorio.salvar(Cedula.criar(votacao_id=votacao_id, turno=turno, membro_id=membro_id))

    assert {c.membro_id for c in repositorio.listar_por_turno(votacao_id, 1)} == {iano, bia}
    assert [c.membro_id for c in repositorio.listar_por_turno(votacao_id, 2)] == [iano]
    assert repositorio.buscar(votacao_id, 2, bia) is None
