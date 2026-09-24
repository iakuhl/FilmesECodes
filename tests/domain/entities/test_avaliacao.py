"""Testes da entidade Avaliacao."""

from uuid import uuid4

import pytest

from filmes_e_cubos.domain.entities.avaliacao import Avaliacao
from filmes_e_cubos.domain.exceptions.avaliacao import NotaForaDaEscalaError
from filmes_e_cubos.domain.value_objects.escala_avaliacao import EscalaAvaliacao
from filmes_e_cubos.domain.value_objects.identificadores import MembroId, SessaoExibicaoId
from filmes_e_cubos.domain.value_objects.nota import Nota
from filmes_e_cubos.domain.value_objects.status_avaliacao import StatusAvaliacao


def test_criar_avaliacao_com_nota_dentro_da_escala() -> None:
    avaliacao = Avaliacao.criar(
        sessao_id=SessaoExibicaoId(uuid4()),
        membro_id=MembroId(uuid4()),
        nota=Nota.criar("4.5"),
        escala=EscalaAvaliacao.padrao(),
        comentario="Ótimo filme",
    )

    assert avaliacao.status is StatusAvaliacao.NOTA_REGISTRADA
    assert avaliacao.nota == Nota.criar("4.5")
    assert avaliacao.comentario == "Ótimo filme"


def test_criar_avaliacao_com_nota_fora_da_escala_levanta_erro() -> None:
    with pytest.raises(NotaForaDaEscalaError):
        Avaliacao.criar(
            sessao_id=SessaoExibicaoId(uuid4()),
            membro_id=MembroId(uuid4()),
            nota=Nota.criar("5.5"),
            escala=EscalaAvaliacao.padrao(),
        )


def test_criar_avaliacao_sem_nota_vira_dorminhoco() -> None:
    avaliacao = Avaliacao.criar(
        sessao_id=SessaoExibicaoId(uuid4()),
        membro_id=MembroId(uuid4()),
        escala=EscalaAvaliacao.padrao(),
        comentario="Cochilei no início",
    )

    assert avaliacao.status is StatusAvaliacao.DORMINHOCO
    assert avaliacao.nota is None
    assert avaliacao.comentario == "Cochilei no início"
