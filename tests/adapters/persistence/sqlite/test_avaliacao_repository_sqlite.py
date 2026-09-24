"""Testes de integração de `AvaliacaoRepositorioSqlite` contra um SQLite real."""

from datetime import date
from decimal import Decimal

from sqlalchemy import Engine

from filmes_e_cubos.adapters.persistence.sqlite.avaliacao_repository_sqlite import (
    AvaliacaoRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.clube_repository_sqlite import (
    ClubeRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.filme_repository_sqlite import (
    FilmeRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.indicacao_repository_sqlite import (
    IndicacaoRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.membro_repository_sqlite import (
    MembroRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.rodada_repository_sqlite import (
    RodadaRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.sessao_repository_sqlite import (
    SessaoRepositorioSqlite,
)
from filmes_e_cubos.domain.entities.avaliacao import Avaliacao
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.filme import Filme
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.entities.membro import Membro
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.entities.sessao_exibicao import SessaoExibicao
from filmes_e_cubos.domain.value_objects.escala_avaliacao import EscalaAvaliacao
from filmes_e_cubos.domain.value_objects.nota import Nota
from filmes_e_cubos.domain.value_objects.status_avaliacao import StatusAvaliacao


def _sessao_e_membro_salvos(engine: Engine) -> tuple[str, Membro]:
    clube = Clube.criar(nome="Filmes e Cubos")
    ClubeRepositorioSqlite(engine).salvar(clube)
    rodada = Rodada.abrir(clube_id=clube.id, numero=1, data_inicio=date(2024, 1, 1))
    RodadaRepositorioSqlite(engine).salvar(rodada)
    membro = Membro.criar(clube_id=clube.id, nome="Ana", data_ingresso=date(2024, 1, 1))
    MembroRepositorioSqlite(engine).salvar(membro)
    filme = Filme.criar(titulo="Duna")
    FilmeRepositorioSqlite(engine).salvar(filme)
    indicacao = Indicacao.criar(
        rodada_id=rodada.id, membro_id=membro.id, filme_id=filme.id, data_indicacao=date(2024, 1, 2)
    )
    IndicacaoRepositorioSqlite(engine).salvar(indicacao)
    sessao = SessaoExibicao.registrar(
        indicacao_id=indicacao.id, data_sessao=date(2024, 1, 7), membros_presentes=frozenset()
    )
    SessaoRepositorioSqlite(engine).salvar(sessao)
    return sessao.id, membro


def test_avaliacao_com_nota_preserva_precisao_decimal(engine: Engine) -> None:
    sessao_id, membro = _sessao_e_membro_salvos(engine)
    repositorio = AvaliacaoRepositorioSqlite(engine)
    avaliacao = Avaliacao.criar(
        sessao_id=sessao_id,
        membro_id=membro.id,
        nota=Nota.criar("4.5"),
        escala=EscalaAvaliacao.padrao(),
        comentario="Ótimo",
    )

    repositorio.salvar(avaliacao)
    recuperada = repositorio.buscar_por_sessao_e_membro(sessao_id, membro.id)

    assert recuperada is not None
    assert recuperada.status is StatusAvaliacao.NOTA_REGISTRADA
    assert recuperada.nota is not None
    assert recuperada.nota.valor == Decimal("4.5")
    assert recuperada.comentario == "Ótimo"


def test_avaliacao_dorminhoco_preserva_nota_nula(engine: Engine) -> None:
    sessao_id, membro = _sessao_e_membro_salvos(engine)
    repositorio = AvaliacaoRepositorioSqlite(engine)
    avaliacao = Avaliacao.criar(
        sessao_id=sessao_id, membro_id=membro.id, escala=EscalaAvaliacao.padrao()
    )

    repositorio.salvar(avaliacao)
    recuperada = repositorio.buscar_por_sessao_e_membro(sessao_id, membro.id)

    assert recuperada is not None
    assert recuperada.status is StatusAvaliacao.DORMINHOCO
    assert recuperada.nota is None


def test_listar_por_sessao(engine: Engine) -> None:
    sessao_id, membro = _sessao_e_membro_salvos(engine)
    repositorio = AvaliacaoRepositorioSqlite(engine)
    repositorio.salvar(
        Avaliacao.criar(
            sessao_id=sessao_id,
            membro_id=membro.id,
            nota=Nota.criar("3.0"),
            escala=EscalaAvaliacao.padrao(),
        )
    )

    assert len(repositorio.listar_por_sessao(sessao_id)) == 1
