"""Testes das migrações de esquema (Alembic)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from uuid import UUID

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

from filmes_e_cubos.adapters.persistence.sqlite.clube_repository_sqlite import (
    ClubeRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.esquema import metadata
from filmes_e_cubos.adapters.persistence.sqlite.fabrica_engine import criar_engine
from filmes_e_cubos.adapters.persistence.sqlite.migracao import (
    REVISAO_INICIAL,
    configuracao_alembic,
)
from filmes_e_cubos.adapters.persistence.sqlite.sessao_repository_sqlite import (
    SessaoRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.turno_de_votacao_repository_sqlite import (
    TurnoDeVotacaoRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.votacao_oscar_repository_sqlite import (
    VotacaoOscarRepositorioSqlite,
)
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    MembroId,
    NomeacaoOscarId,
    SessaoExibicaoId,
    TemporadaOscarId,
)
from filmes_e_cubos.domain.value_objects.media_das_notas import MediaDasNotas


def _revisao_mais_recente() -> str | None:
    return ScriptDirectory.from_config(configuracao_alembic()).get_current_head()


def test_banco_novo_chega_na_revisao_mais_recente(tmp_path: Path) -> None:
    engine = criar_engine(tmp_path / "novo.db")

    with engine.connect() as conexao:
        assert MigrationContext.configure(conexao).get_current_revision() == (
            _revisao_mais_recente()
        )


def test_migracoes_produzem_exatamente_o_esquema_declarado(tmp_path: Path) -> None:
    """Se `esquema.py` mudar sem uma revisão nova, este teste acusa a diferença."""
    engine = criar_engine(tmp_path / "comparado.db")

    with engine.connect() as conexao:
        diferencas = compare_metadata(MigrationContext.configure(conexao), metadata)

    assert diferencas == []


def test_banco_anterior_as_migracoes_e_reconhecido_sem_perder_dados(tmp_path: Path) -> None:
    caminho = tmp_path / "legado.db"
    # Simula um banco criado pelas Fases 2 e 3: o esquema da revisão inicial,
    # sem a tabela de controle do Alembic.
    legado = create_engine(f"sqlite:///{caminho}")
    configuracao = configuracao_alembic()
    with legado.begin() as conexao:
        configuracao.attributes["connection"] = conexao
        command.upgrade(configuracao, REVISAO_INICIAL)
        conexao.execute(text("DROP TABLE alembic_version"))
    ClubeRepositorioSqlite(legado).salvar(Clube.criar(nome="Filmes e Cubos"))

    engine = criar_engine(caminho)

    assert [clube.nome for clube in ClubeRepositorioSqlite(engine).listar_todos()] == [
        "Filmes e Cubos"
    ]
    with engine.connect() as conexao:
        assert MigrationContext.configure(conexao).get_current_revision() == (
            _revisao_mais_recente()
        )


def test_abrir_o_mesmo_banco_de_novo_nao_muda_nada(tmp_path: Path) -> None:
    caminho = tmp_path / "reaberto.db"
    ClubeRepositorioSqlite(criar_engine(caminho)).salvar(Clube.criar(nome="Filmes e Cubos"))

    assert len(ClubeRepositorioSqlite(criar_engine(caminho)).listar_todos()) == 1


_ANTES_DA_MEDIA = "0002"
"""Última revisão em que a sessão ainda não guardava a média das notas."""

_SESSAO_AVALIADA = "00000000-0000-0000-0000-00000000000a"
_SESSAO_SO_DE_DORMINHOCOS = "00000000-0000-0000-0000-00000000000b"
_INDICACAO_I = "00000000-0000-0000-0000-000000000001"
_INDICACAO_J = "00000000-0000-0000-0000-000000000002"


def test_migracao_calcula_a_media_das_sessoes_ja_avaliadas(tmp_path: Path) -> None:
    """A revisão 0003 preenche a média de quem já tinha notas, sem contar dorminhocos.

    O banco "antigo" é montado com SQL puro, na revisão anterior: os
    repositórios atuais já gravam as colunas novas e não serviriam aqui.
    """
    caminho = tmp_path / "com_avaliacoes.db"
    antigo = create_engine(f"sqlite:///{caminho}")
    configuracao = configuracao_alembic()
    with antigo.begin() as conexao:
        configuracao.attributes["connection"] = conexao
        command.upgrade(configuracao, _ANTES_DA_MEDIA)
        for sql in (
            "INSERT INTO clubes VALUES ('c', 'Clube', 5, '0.5', '5.0', '0.5')",
            "INSERT INTO rodadas VALUES ('r', 'c', 1, 'ABERTA', '2024-01-01', NULL)",
            "INSERT INTO filmes VALUES ('f', 'Duna', NULL, NULL, NULL, NULL)",
            "INSERT INTO filmes VALUES ('g', 'Tár', NULL, NULL, NULL, NULL)",
            f"INSERT INTO indicacoes VALUES ('{_INDICACAO_I}', 'r', NULL, 'f', 'DEMOCRACIA',"
            " 'ASSISTIDA', '2024-01-02')",
            f"INSERT INTO indicacoes VALUES ('{_INDICACAO_J}', 'r', NULL, 'g', 'DEMOCRACIA',"
            " 'ASSISTIDA', '2024-01-02')",
            f"INSERT INTO sessoes_exibicao VALUES ('{_SESSAO_AVALIADA}', '{_INDICACAO_I}',"
            " '2024-01-07')",
            f"INSERT INTO sessoes_exibicao VALUES ('{_SESSAO_SO_DE_DORMINHOCOS}',"
            f" '{_INDICACAO_J}', '2024-01-14')",
            f"INSERT INTO avaliacoes VALUES ('a1', '{_SESSAO_AVALIADA}', 'm1', 'NOTA_REGISTRADA',"
            " '4.0', NULL)",
            f"INSERT INTO avaliacoes VALUES ('a2', '{_SESSAO_AVALIADA}', 'm2', 'NOTA_REGISTRADA',"
            " '3.5', NULL)",
            f"INSERT INTO avaliacoes VALUES ('a3', '{_SESSAO_AVALIADA}', 'm3', 'NOTA_REGISTRADA',"
            " '3.5', NULL)",
            f"INSERT INTO avaliacoes VALUES ('a4', '{_SESSAO_AVALIADA}', 'm4', 'DORMINHOCO',"
            " NULL, NULL)",
            f"INSERT INTO avaliacoes VALUES ('a5', '{_SESSAO_SO_DE_DORMINHOCOS}', 'm1',"
            " 'DORMINHOCO', NULL, NULL)",
        ):
            conexao.execute(text(sql))

    sessoes = SessaoRepositorioSqlite(criar_engine(caminho))

    avaliada = sessoes.buscar_por_id(SessaoExibicaoId(UUID(_SESSAO_AVALIADA)))
    so_de_dorminhocos = sessoes.buscar_por_id(SessaoExibicaoId(UUID(_SESSAO_SO_DE_DORMINHOCOS)))
    assert avaliada is not None
    assert so_de_dorminhocos is not None
    assert avaliada.media_das_notas == MediaDasNotas(soma=Decimal("11.0"), quantidade=3)
    assert so_de_dorminhocos.media_das_notas is None


_ANTES_DA_VOTACAO = "0004"
"""Última revisão em que a edição em votação não tinha votação registrada."""


def _id(numero: int) -> str:
    return f"00000000-0000-0000-0000-{numero:012d}"


def test_migracao_inicia_a_votacao_das_edicoes_que_ja_estavam_em_votacao(tmp_path: Path) -> None:
    """A revisão 0005 dá votação às edições em votação: eleitores são os ativos de agora,
    e só as categorias sem troféu (e com ao menos duas nomeações) abrem o 1º turno.
    """
    caminho = tmp_path / "em_votacao.db"
    antigo = create_engine(f"sqlite:///{caminho}")
    configuracao = configuracao_alembic()
    clube, iano, bia, caio = _id(1), _id(2), _id(3), _id(4)
    em_votacao, aberta = _id(10), _id(11)
    disputada, premiada, esvaziada = _id(20), _id(21), _id(22)
    primeira, segunda, vencedora, outra, sozinha = _id(30), _id(31), _id(32), _id(33), _id(34)
    with antigo.begin() as conexao:
        configuracao.attributes["connection"] = conexao
        command.upgrade(configuracao, _ANTES_DA_VOTACAO)
        for sql in (
            f"INSERT INTO clubes VALUES ('{clube}', 'Clube', 5, '0.5', '5.0', '0.5')",
            f"INSERT INTO membros VALUES ('{iano}', '{clube}', 'Iano', NULL, '2024-01-01', 1)",
            f"INSERT INTO membros VALUES ('{bia}', '{clube}', 'Bia', NULL, '2024-01-01', 1)",
            f"INSERT INTO membros VALUES ('{caio}', '{clube}', 'Caio', NULL, '2024-01-01', 0)",
            f"INSERT INTO temporadas_oscar VALUES ('{em_votacao}', '{clube}', 2024, 'Óscar',"
            " 'EM_VOTACAO', NULL, 2)",
            f"INSERT INTO temporadas_oscar VALUES ('{aberta}', '{clube}', 2025, 'Óscar',"
            " 'ABERTA_PARA_INDICACOES', NULL, 2)",
            f"INSERT INTO categorias_oscar VALUES ('{disputada}', '{em_votacao}', 'Veículo',"
            " 'VARIAVEL', NULL)",
            f"INSERT INTO categorias_oscar VALUES ('{premiada}', '{em_votacao}', 'Criança',"
            " 'VARIAVEL', NULL)",
            f"INSERT INTO categorias_oscar VALUES ('{esvaziada}', '{em_votacao}', 'Sono',"
            " 'VARIAVEL', NULL)",
            f"INSERT INTO nomeacoes_oscar VALUES ('{segunda}', '{disputada}', 'f', '{iano}')",
            f"INSERT INTO nomeacoes_oscar VALUES ('{primeira}', '{disputada}', 'g', NULL)",
            f"INSERT INTO nomeacoes_oscar VALUES ('{vencedora}', '{premiada}', 'f', '{iano}')",
            f"INSERT INTO nomeacoes_oscar VALUES ('{outra}', '{premiada}', 'g', NULL)",
            f"INSERT INTO nomeacoes_oscar VALUES ('{sozinha}', '{esvaziada}', 'f', '{bia}')",
            f"INSERT INTO trofeus VALUES ('t', '{premiada}', '{vencedora}', '{iano}',"
            " '2024-12-20')",
        ):
            conexao.execute(text(sql))

    engine = criar_engine(caminho)
    votacoes = VotacaoOscarRepositorioSqlite(engine)
    turnos = TurnoDeVotacaoRepositorioSqlite(engine)

    votacao = votacoes.buscar_por_temporada(TemporadaOscarId(UUID(em_votacao)))
    assert votacao is not None
    assert votacao.eleitores == {MembroId(UUID(iano)), MembroId(UUID(bia))}
    assert votacao.turno_atual == 1
    assert not votacao.encerrada
    [turno] = turnos.listar_por_categoria(CategoriaOscarId(UUID(disputada)))
    assert turno.candidatas == (NomeacaoOscarId(UUID(segunda)), NomeacaoOscarId(UUID(primeira)))
    assert turno.aberto
    assert turnos.listar_por_categoria(CategoriaOscarId(UUID(premiada))) == []
    assert turnos.listar_por_categoria(CategoriaOscarId(UUID(esvaziada))) == []
    assert votacoes.buscar_por_temporada(TemporadaOscarId(UUID(aberta))) is None
