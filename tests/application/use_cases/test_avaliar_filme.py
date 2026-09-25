"""Testes do caso de uso AvaliarFilme."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from fractions import Fraction
from uuid import uuid4

import pytest

from filmes_e_cubos.application.use_cases.avaliar_filme import AvaliarFilme
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.filme import Filme
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.entities.sessao_exibicao import SessaoExibicao
from filmes_e_cubos.domain.exceptions.avaliacao import (
    AvaliacaoDuplicadaError,
    MembroAusenteNaSessaoError,
    NotaForaDaEscalaError,
)
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.configuracao_clube import ConfiguracaoClube
from filmes_e_cubos.domain.value_objects.escala_avaliacao import EscalaAvaliacao
from filmes_e_cubos.domain.value_objects.identificadores import MembroId, SessaoExibicaoId
from filmes_e_cubos.domain.value_objects.nota import Nota
from filmes_e_cubos.domain.value_objects.status_avaliacao import StatusAvaliacao
from tests.application.fakes.avaliacao_repositorio_fake import AvaliacaoRepositorioFake
from tests.application.fakes.clube_repositorio_fake import ClubeRepositorioFake
from tests.application.fakes.indicacao_repositorio_fake import IndicacaoRepositorioFake
from tests.application.fakes.membro_repositorio_fake import MembroRepositorioFake
from tests.application.fakes.rodada_repositorio_fake import RodadaRepositorioFake
from tests.application.fakes.sessao_repositorio_fake import SessaoRepositorioFake


@dataclass
class Cenario:
    caso_de_uso: AvaliarFilme
    avaliacoes: AvaliacaoRepositorioFake
    sessoes: SessaoRepositorioFake
    membros: MembroRepositorioFake
    presente: Membro
    ausente: Membro
    sessao: SessaoExibicao


def _preparar(clube: Clube) -> Cenario:
    """Uma sessão do clube com um membro presente e outro ausente."""
    clubes = ClubeRepositorioFake()
    clubes.salvar(clube)
    membros = MembroRepositorioFake()
    presente = Membro.criar(clube_id=clube.id, nome="Ana", data_ingresso=date(2024, 1, 1))
    ausente = Membro.criar(clube_id=clube.id, nome="Bia", data_ingresso=date(2024, 1, 1))
    membros.salvar(presente)
    membros.salvar(ausente)
    rodadas = RodadaRepositorioFake()
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    rodadas.salvar(rodada)
    indicacoes = IndicacaoRepositorioFake()
    indicacao = Indicacao.criar(
        rodada_id=rodada.id,
        membro_id=presente.id,
        filme_id=Filme.criar(titulo="Duna").id,
        data_indicacao=date(2024, 1, 2),
    )
    indicacoes.salvar(indicacao)
    sessoes = SessaoRepositorioFake()
    sessao = SessaoExibicao.registrar(
        indicacao_id=indicacao.id,
        data_sessao=date(2024, 1, 7),
        membros_presentes=frozenset({presente.id}),
    )
    sessoes.salvar(sessao)
    avaliacoes = AvaliacaoRepositorioFake()
    caso_de_uso = AvaliarFilme(avaliacoes, sessoes, membros, indicacoes, rodadas, clubes)
    return Cenario(caso_de_uso, avaliacoes, sessoes, membros, presente, ausente, sessao)


def _com_mais_presentes(cenario: Cenario, clube: Clube, quantos: int) -> list[Membro]:
    """Acrescenta membros presentes à sessão do cenário."""
    novos = [
        Membro.criar(clube_id=clube.id, nome=f"Membro {i}", data_ingresso=date(2024, 1, 1))
        for i in range(quantos)
    ]
    for membro in novos:
        cenario.membros.salvar(membro)
    sessao = SessaoExibicao(
        id=cenario.sessao.id,
        indicacao_id=cenario.sessao.indicacao_id,
        data_sessao=cenario.sessao.data_sessao,
        membros_presentes=cenario.sessao.membros_presentes | {m.id for m in novos},
    )
    cenario.sessoes.salvar(sessao)
    return novos


def _sessao_gravada(cenario: Cenario) -> SessaoExibicao:
    sessao = cenario.sessoes.buscar_por_id(cenario.sessao.id)
    assert sessao is not None
    return sessao


def test_avaliar_filme_com_nota_valida(clube: Clube) -> None:
    cenario = _preparar(clube)

    avaliacao = cenario.caso_de_uso.executar(
        sessao_id=cenario.sessao.id, membro_id=cenario.presente.id, nota=Nota.criar("4.5")
    )

    assert cenario.avaliacoes.buscar_por_sessao_e_membro(
        cenario.sessao.id, cenario.presente.id
    ) is (avaliacao)


def test_quem_nao_esteve_na_sessao_nao_avalia(clube: Clube) -> None:
    cenario = _preparar(clube)

    with pytest.raises(MembroAusenteNaSessaoError):
        cenario.caso_de_uso.executar(
            sessao_id=cenario.sessao.id, membro_id=cenario.ausente.id, nota=Nota.criar("4")
        )
    assert cenario.avaliacoes.listar_por_sessao(cenario.sessao.id) == []


def test_escala_vem_do_clube_dono_da_sessao() -> None:
    escala_de_dez = EscalaAvaliacao(
        nota_minima=Decimal("1"), nota_maxima=Decimal("10"), passo=Decimal("1")
    )
    cenario = _preparar(
        Clube.criar(
            nome="Clube de Dez",
            configuracao=ConfiguracaoClube(tamanho_rodada=5, escala_avaliacao=escala_de_dez),
        )
    )

    avaliacao = cenario.caso_de_uso.executar(
        sessao_id=cenario.sessao.id, membro_id=cenario.presente.id, nota=Nota.criar("9")
    )

    assert avaliacao.nota == Nota.criar("9")


def test_avaliar_filme_com_nota_fora_da_escala_levanta_erro(clube: Clube) -> None:
    cenario = _preparar(clube)

    with pytest.raises(NotaForaDaEscalaError):
        cenario.caso_de_uso.executar(
            sessao_id=cenario.sessao.id, membro_id=cenario.presente.id, nota=Nota.criar("7")
        )


def test_avaliar_filme_sem_nota_registra_dorminhoco(clube: Clube) -> None:
    cenario = _preparar(clube)

    avaliacao = cenario.caso_de_uso.executar(
        sessao_id=cenario.sessao.id, membro_id=cenario.presente.id
    )

    assert avaliacao.status is StatusAvaliacao.DORMINHOCO
    assert avaliacao.nota is None
    assert _sessao_gravada(cenario).media_das_notas is None


def test_mesmo_membro_avaliar_a_mesma_sessao_duas_vezes_levanta_erro(clube: Clube) -> None:
    cenario = _preparar(clube)
    cenario.caso_de_uso.executar(
        sessao_id=cenario.sessao.id, membro_id=cenario.presente.id, nota=Nota.criar("4")
    )

    with pytest.raises(AvaliacaoDuplicadaError):
        cenario.caso_de_uso.executar(
            sessao_id=cenario.sessao.id, membro_id=cenario.presente.id, nota=Nota.criar("5")
        )


def test_cada_avaliacao_refaz_a_media_da_sessao_sem_contar_dorminhocos(clube: Clube) -> None:
    cenario = _preparar(clube)
    outro, dorminhoco, mais_um = _com_mais_presentes(cenario, clube, 3)

    cenario.caso_de_uso.executar(
        sessao_id=cenario.sessao.id, membro_id=cenario.presente.id, nota=Nota.criar("4")
    )
    cenario.caso_de_uso.executar(sessao_id=cenario.sessao.id, membro_id=dorminhoco.id)
    cenario.caso_de_uso.executar(
        sessao_id=cenario.sessao.id, membro_id=outro.id, nota=Nota.criar("3.5")
    )
    cenario.caso_de_uso.executar(
        sessao_id=cenario.sessao.id, membro_id=mais_um.id, nota=Nota.criar("3.5")
    )

    media = _sessao_gravada(cenario).media_das_notas
    assert media is not None
    assert (media.soma, media.quantidade) == (Decimal("11.0"), 3)
    assert media.valor == Fraction(11, 3)


@pytest.mark.parametrize("qual", ["sessao", "membro"])
def test_sessao_ou_membro_inexistente_levanta_erro(clube: Clube, qual: str) -> None:
    cenario = _preparar(clube)
    sessao_id = SessaoExibicaoId(uuid4()) if qual == "sessao" else cenario.sessao.id
    membro_id = MembroId(uuid4()) if qual == "membro" else cenario.presente.id

    with pytest.raises(EntidadeNaoEncontradaError):
        cenario.caso_de_uso.executar(sessao_id=sessao_id, membro_id=membro_id)
