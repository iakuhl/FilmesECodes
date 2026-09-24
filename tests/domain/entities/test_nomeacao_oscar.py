"""Testes da entidade NomeacaoOscar."""

from uuid import uuid4

from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar
from filmes_e_cubos.domain.value_objects.identificadores import CategoriaOscarId, FilmeId, MembroId


def test_criar_nomeacao_guarda_membro_que_indicou_o_filme() -> None:
    membro_id = MembroId(uuid4())

    nomeacao = NomeacaoOscar.criar(
        categoria_id=CategoriaOscarId(uuid4()),
        filme_id=FilmeId(uuid4()),
        indicado_por_membro_id=membro_id,
    )

    assert nomeacao.indicado_por_membro_id == membro_id
