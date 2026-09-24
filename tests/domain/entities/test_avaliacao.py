"""Testes da entidade Avaliacao."""

from uuid import uuid4

import pytest

from filmes_e_cubos.domain.entities.avaliacao import Avaliacao
from filmes_e_cubos.domain.exceptions.avaliacao import NotaForaDaEscalaError
from filmes_e_cubos.domain.value_objects.escala_avaliacao import EscalaAvaliacao
from filmes_e_cubos.domain.value_objects.identificadores import MembroId, SessaoExibicaoId
from filmes_e_cubos.domain.value_objects.nota import Nota


def test_criar_avaliacao_com_nota_dentro_da_escala() -> None:
    avaliacao = Avaliacao.criar(
        sessao_id=SessaoExibicaoId(uuid4()),
        membro_id=MembroId(uuid4()),
        nota=Nota.criar("4.5"),
        escala=EscalaAvaliacao.padrao(),
        comentario="Ótimo filme",
    )

    assert avaliacao.nota.valor == Nota.criar("4.5").valor
    assert avaliacao.comentario == "Ótimo filme"


def test_criar_avaliacao_com_nota_fora_da_escala_levanta_erro() -> None:
    with pytest.raises(NotaForaDaEscalaError):
        Avaliacao.criar(
            sessao_id=SessaoExibicaoId(uuid4()),
            membro_id=MembroId(uuid4()),
            nota=Nota.criar("5.5"),
            escala=EscalaAvaliacao.padrao(),
        )
