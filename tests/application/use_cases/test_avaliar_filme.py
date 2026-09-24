"""Testes do caso de uso AvaliarFilme."""

from datetime import date
from uuid import uuid4

import pytest

from filmes_e_cubos.application.use_cases.avaliar_filme import AvaliarFilme
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.entities.sessao_exibicao import SessaoExibicao
from filmes_e_cubos.domain.exceptions.avaliacao import (
    AvaliacaoDuplicadaError,
    NotaForaDaEscalaError,
)
from filmes_e_cubos.domain.value_objects.identificadores import IndicacaoId
from filmes_e_cubos.domain.value_objects.nota import Nota
from filmes_e_cubos.domain.value_objects.status_avaliacao import StatusAvaliacao
from tests.application.fakes.avaliacao_repositorio_fake import AvaliacaoRepositorioFake
from tests.application.fakes.clube_repositorio_fake import ClubeRepositorioFake
from tests.application.fakes.membro_repositorio_fake import MembroRepositorioFake
from tests.application.fakes.sessao_repositorio_fake import SessaoRepositorioFake


def _preparar(
    clube: Clube,
) -> tuple[
    AvaliarFilme,
    ClubeRepositorioFake,
    MembroRepositorioFake,
    SessaoRepositorioFake,
    AvaliacaoRepositorioFake,
    Membro,
    SessaoExibicao,
]:
    clubes = ClubeRepositorioFake()
    clubes.salvar(clube)
    membros = MembroRepositorioFake()
    membro = Membro.criar(clube_id=clube.id, nome="Ana", data_ingresso=date(2024, 1, 1))
    membros.salvar(membro)
    sessoes = SessaoRepositorioFake()
    sessao = SessaoExibicao.registrar(
        indicacao_id=IndicacaoId(uuid4()),
        data_sessao=date(2024, 1, 7),
        membros_presentes=frozenset(),
    )
    sessoes.salvar(sessao)
    avaliacoes = AvaliacaoRepositorioFake()
    caso_de_uso = AvaliarFilme(avaliacoes, sessoes, membros, clubes)
    return caso_de_uso, clubes, membros, sessoes, avaliacoes, membro, sessao


def test_avaliar_filme_com_nota_valida(clube: Clube) -> None:
    caso_de_uso, _, _, _, avaliacoes, membro, sessao = _preparar(clube)

    avaliacao = caso_de_uso.executar(
        sessao_id=sessao.id, membro_id=membro.id, clube_id=clube.id, nota=Nota.criar("4.5")
    )

    assert avaliacoes.buscar_por_sessao_e_membro(sessao.id, membro.id) is avaliacao


def test_avaliar_filme_com_nota_fora_da_escala_levanta_erro(clube: Clube) -> None:
    caso_de_uso, _, _, _, _, membro, sessao = _preparar(clube)

    with pytest.raises(NotaForaDaEscalaError):
        caso_de_uso.executar(
            sessao_id=sessao.id, membro_id=membro.id, clube_id=clube.id, nota=Nota.criar("5.3")
        )


def test_avaliar_filme_sem_nota_registra_dorminhoco(clube: Clube) -> None:
    caso_de_uso, _, _, _, _, membro, sessao = _preparar(clube)

    avaliacao = caso_de_uso.executar(sessao_id=sessao.id, membro_id=membro.id, clube_id=clube.id)

    assert avaliacao.status is StatusAvaliacao.DORMINHOCO
    assert avaliacao.nota is None


def test_mesmo_membro_avaliar_a_mesma_sessao_duas_vezes_levanta_erro(clube: Clube) -> None:
    caso_de_uso, _, _, _, _, membro, sessao = _preparar(clube)
    caso_de_uso.executar(
        sessao_id=sessao.id, membro_id=membro.id, clube_id=clube.id, nota=Nota.criar("4.0")
    )

    with pytest.raises(AvaliacaoDuplicadaError):
        caso_de_uso.executar(
            sessao_id=sessao.id, membro_id=membro.id, clube_id=clube.id, nota=Nota.criar("3.0")
        )
