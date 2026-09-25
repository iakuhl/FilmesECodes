"""Testes do caso de uso IndicarFilme."""

from datetime import date, datetime
from uuid import uuid4

import pytest

from filmes_e_cubos.application.use_cases.indicar_filme import IndicarFilme
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.filme import Filme
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.indicacao import (
    FilmeRepetidoNoClubeError,
    IndicacaoDuplicadaError,
)
from filmes_e_cubos.domain.exceptions.membro import MembroInativoError
from filmes_e_cubos.domain.exceptions.rodada import RodadaJaEncerradaError, RodadaLotadaError
from filmes_e_cubos.domain.value_objects.configuracao_clube import ConfiguracaoClube
from filmes_e_cubos.domain.value_objects.identificadores import FilmeId
from tests.application.fakes.clube_repositorio_fake import ClubeRepositorioFake
from tests.application.fakes.filme_repositorio_fake import FilmeRepositorioFake
from tests.application.fakes.indicacao_repositorio_fake import IndicacaoRepositorioFake
from tests.application.fakes.membro_repositorio_fake import MembroRepositorioFake
from tests.application.fakes.relogio_fake import RelogioFake
from tests.application.fakes.rodada_repositorio_fake import RodadaRepositorioFake


def _montar_caso_de_uso() -> tuple[
    IndicarFilme,
    ClubeRepositorioFake,
    MembroRepositorioFake,
    FilmeRepositorioFake,
    RodadaRepositorioFake,
    IndicacaoRepositorioFake,
]:
    clubes = ClubeRepositorioFake()
    membros = MembroRepositorioFake()
    filmes = FilmeRepositorioFake()
    rodadas = RodadaRepositorioFake()
    indicacoes = IndicacaoRepositorioFake()
    caso_de_uso = IndicarFilme(
        indicacoes, rodadas, membros, filmes, clubes, RelogioFake(datetime(2024, 1, 7))
    )
    return caso_de_uso, clubes, membros, filmes, rodadas, indicacoes


def test_indicar_filme_com_sucesso(clube: Clube) -> None:
    caso_de_uso, clubes, membros, filmes, rodadas, _indicacoes = _montar_caso_de_uso()
    clubes.salvar(clube)
    membro = Membro.criar(clube_id=clube.id, nome="Ana", data_ingresso=date(2024, 1, 1))
    membros.salvar(membro)
    filme = Filme.criar(titulo="Duna")
    filmes.salvar(filme)
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    rodadas.salvar(rodada)

    indicacao = caso_de_uso.executar(rodada_id=rodada.id, membro_id=membro.id, filme_id=filme.id)

    assert indicacao.membro_id == membro.id
    assert indicacao.filme_id == filme.id


def test_indicar_filme_em_rodada_encerrada_levanta_erro(clube: Clube) -> None:
    caso_de_uso, clubes, membros, filmes, rodadas, _indicacoes = _montar_caso_de_uso()
    clubes.salvar(clube)
    membro = Membro.criar(clube_id=clube.id, nome="Ana", data_ingresso=date(2024, 1, 1))
    membros.salvar(membro)
    filme = Filme.criar(titulo="Duna")
    filmes.salvar(filme)
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    rodada.encerrar(data_encerramento=date(2024, 1, 8))
    rodadas.salvar(rodada)

    with pytest.raises(RodadaJaEncerradaError):
        caso_de_uso.executar(rodada_id=rodada.id, membro_id=membro.id, filme_id=filme.id)


def test_indicar_filme_com_membro_inativo_levanta_erro(clube: Clube) -> None:
    caso_de_uso, clubes, membros, filmes, rodadas, _indicacoes = _montar_caso_de_uso()
    clubes.salvar(clube)
    membro = Membro.criar(clube_id=clube.id, nome="Ana", data_ingresso=date(2024, 1, 1))
    membro.desativar()
    membros.salvar(membro)
    filme = Filme.criar(titulo="Duna")
    filmes.salvar(filme)
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    rodadas.salvar(rodada)

    with pytest.raises(MembroInativoError):
        caso_de_uso.executar(rodada_id=rodada.id, membro_id=membro.id, filme_id=filme.id)


def test_indicar_filme_inexistente_levanta_erro(clube: Clube) -> None:
    caso_de_uso, clubes, membros, filmes, rodadas, _indicacoes = _montar_caso_de_uso()
    clubes.salvar(clube)
    membro = Membro.criar(clube_id=clube.id, nome="Ana", data_ingresso=date(2024, 1, 1))
    membros.salvar(membro)
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    rodadas.salvar(rodada)

    with pytest.raises(EntidadeNaoEncontradaError):
        caso_de_uso.executar(rodada_id=rodada.id, membro_id=membro.id, filme_id=FilmeId(uuid4()))


def test_mesmo_membro_indicar_duas_vezes_na_mesma_rodada_levanta_erro(clube: Clube) -> None:
    caso_de_uso, clubes, membros, filmes, rodadas, _indicacoes = _montar_caso_de_uso()
    clubes.salvar(clube)
    membro = Membro.criar(clube_id=clube.id, nome="Ana", data_ingresso=date(2024, 1, 1))
    membros.salvar(membro)
    filme_1 = Filme.criar(titulo="Duna")
    filme_2 = Filme.criar(titulo="Arrival")
    filmes.salvar(filme_1)
    filmes.salvar(filme_2)
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    rodadas.salvar(rodada)
    caso_de_uso.executar(rodada_id=rodada.id, membro_id=membro.id, filme_id=filme_1.id)

    with pytest.raises(IndicacaoDuplicadaError):
        caso_de_uso.executar(rodada_id=rodada.id, membro_id=membro.id, filme_id=filme_2.id)


def test_indicar_filme_alem_do_tamanho_da_rodada_levanta_erro() -> None:
    caso_de_uso, clubes, membros, filmes, rodadas, _indicacoes = _montar_caso_de_uso()
    clube = Clube.criar(
        nome="Clube pequeno",
        configuracao=ConfiguracaoClube(
            tamanho_rodada=1, escala_avaliacao=ConfiguracaoClube.padrao().escala_avaliacao
        ),
    )
    clubes.salvar(clube)
    membro_1 = Membro.criar(clube_id=clube.id, nome="Ana", data_ingresso=date(2024, 1, 1))
    membro_2 = Membro.criar(clube_id=clube.id, nome="Bia", data_ingresso=date(2024, 1, 1))
    membros.salvar(membro_1)
    membros.salvar(membro_2)
    filme_1 = Filme.criar(titulo="Duna")
    filme_2 = Filme.criar(titulo="Arrival")
    filmes.salvar(filme_1)
    filmes.salvar(filme_2)
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    rodadas.salvar(rodada)
    caso_de_uso.executar(rodada_id=rodada.id, membro_id=membro_1.id, filme_id=filme_1.id)

    with pytest.raises(RodadaLotadaError):
        caso_de_uso.executar(rodada_id=rodada.id, membro_id=membro_2.id, filme_id=filme_2.id)


def test_indicacao_democracia_nao_conta_na_cota_nem_bloqueia_membro(clube: Clube) -> None:
    """Uma indicação DEMOCRACIA é extra: não ocupa a cota nem impede que o
    mesmo membro indique normalmente na mesma rodada."""
    caso_de_uso, clubes, membros, filmes, rodadas, indicacoes = _montar_caso_de_uso()
    clube_pequeno = Clube.criar(
        nome="Clube pequeno",
        configuracao=ConfiguracaoClube(
            tamanho_rodada=1, escala_avaliacao=ConfiguracaoClube.padrao().escala_avaliacao
        ),
    )
    clubes.salvar(clube_pequeno)
    membro = Membro.criar(clube_id=clube_pequeno.id, nome="Ana", data_ingresso=date(2024, 1, 1))
    membros.salvar(membro)
    filme_normal = Filme.criar(titulo="Duna")
    filme_democracia = Filme.criar(titulo="Arrival")
    filmes.salvar(filme_normal)
    filmes.salvar(filme_democracia)
    rodada = Rodada.abrir(clube_id=clube_pequeno.id, numero=1, data_inicio=date(2024, 1, 1))
    rodadas.salvar(rodada)
    indicacao_democracia = Indicacao.criar_democracia(
        rodada_id=rodada.id, filme_id=filme_democracia.id, data_indicacao=date(2024, 1, 2)
    )
    indicacoes.salvar(indicacao_democracia)

    indicacao = caso_de_uso.executar(
        rodada_id=rodada.id, membro_id=membro.id, filme_id=filme_normal.id
    )

    assert indicacao.membro_id == membro.id


def _clube_com_rodada(
    clube: Clube,
) -> tuple[IndicarFilme, IndicacaoRepositorioFake, Rodada, list[Membro], Filme]:
    caso_de_uso, clubes, membros, filmes, rodadas, indicacoes = _montar_caso_de_uso()
    clubes.salvar(clube)
    ana = Membro.criar(clube_id=clube.id, nome="Ana", data_ingresso=date(2024, 1, 1))
    bia = Membro.criar(clube_id=clube.id, nome="Bia", data_ingresso=date(2024, 1, 1))
    membros.salvar(ana)
    membros.salvar(bia)
    filme = Filme.criar(titulo="Duna")
    filmes.salvar(filme)
    rodada = Rodada.abrir(clube_id=clube.id, numero=2, data_inicio=date(2024, 2, 1))
    rodadas.salvar(rodada)
    return caso_de_uso, indicacoes, rodada, [ana, bia], filme


def test_filme_ja_indicado_e_nao_assistido_nao_e_indicado_de_novo(clube: Clube) -> None:
    caso_de_uso, _, rodada, (ana, bia), filme = _clube_com_rodada(clube)
    caso_de_uso.executar(rodada_id=rodada.id, membro_id=ana.id, filme_id=filme.id)

    with pytest.raises(FilmeRepetidoNoClubeError, match="já está indicado"):
        caso_de_uso.executar(rodada_id=rodada.id, membro_id=bia.id, filme_id=filme.id)


def test_filme_ja_assistido_pelo_clube_nao_e_indicado_de_novo(clube: Clube) -> None:
    caso_de_uso, indicacoes, rodada, (ana, _), filme = _clube_com_rodada(clube)
    antiga = Indicacao.criar_democracia(
        rodada_id=rodada.id, filme_id=filme.id, data_indicacao=date(2024, 2, 2)
    )
    antiga.marcar_assistida()
    indicacoes.salvar(antiga)

    with pytest.raises(FilmeRepetidoNoClubeError, match="já foi assistido"):
        caso_de_uso.executar(rodada_id=rodada.id, membro_id=ana.id, filme_id=filme.id)


def test_filme_que_passou_por_outro_clube_pode_ser_indicado(clube: Clube) -> None:
    caso_de_uso, indicacoes, rodada, (ana, _), filme = _clube_com_rodada(clube)
    de_outro_clube = Indicacao.criar_democracia(
        rodada_id=Rodada.abrir(
            clube_id=Clube.criar(nome="Outro").id, numero=1, data_inicio=date(2024, 1, 1)
        ).id,
        filme_id=filme.id,
        data_indicacao=date(2024, 1, 2),
    )
    indicacoes.salvar(de_outro_clube)

    indicacao = caso_de_uso.executar(rodada_id=rodada.id, membro_id=ana.id, filme_id=filme.id)

    assert indicacao.filme_id == filme.id
