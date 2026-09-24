"""Esquema SQLAlchemy Core do banco SQLite: tabelas e tipos, sem lógica de domínio.

Ids são armazenados como texto (`str(uuid.UUID)`), valores decimais (notas e
escala de avaliação) como texto (`str(Decimal)`, para preservar precisão
exata) e enums como o nome do membro (ex.: `"ABERTA"`).
"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
)

metadata = MetaData()

clubes = Table(
    "clubes",
    metadata,
    Column("id", String, primary_key=True),
    Column("nome", String, nullable=False),
    Column("tamanho_rodada", Integer, nullable=False),
    Column("nota_minima", String, nullable=False),
    Column("nota_maxima", String, nullable=False),
    Column("passo", String, nullable=False),
)

membros = Table(
    "membros",
    metadata,
    Column("id", String, primary_key=True),
    Column("clube_id", String, ForeignKey("clubes.id"), nullable=False),
    Column("nome", String, nullable=False),
    Column("apelido", String, nullable=True),
    Column("data_ingresso", Date, nullable=False),
    Column("ativo", Boolean, nullable=False),
)

filmes = Table(
    "filmes",
    metadata,
    Column("id", String, primary_key=True),
    Column("titulo", String, nullable=False),
    Column("ano_lancamento", Integer, nullable=True),
    Column("diretor", String, nullable=True),
    Column("identificador_externo", String, nullable=True),
)

rodadas = Table(
    "rodadas",
    metadata,
    Column("id", String, primary_key=True),
    Column("clube_id", String, ForeignKey("clubes.id"), nullable=False),
    Column("numero", Integer, nullable=False),
    Column("status", String, nullable=False),
    Column("data_inicio", Date, nullable=False),
    Column("data_encerramento", Date, nullable=True),
)

indicacoes = Table(
    "indicacoes",
    metadata,
    Column("id", String, primary_key=True),
    Column("rodada_id", String, ForeignKey("rodadas.id"), nullable=False),
    Column("membro_id", String, ForeignKey("membros.id"), nullable=True),
    Column("filme_id", String, ForeignKey("filmes.id"), nullable=False),
    Column("tipo", String, nullable=False),
    Column("status", String, nullable=False),
    Column("data_indicacao", Date, nullable=False),
)

sorteios = Table(
    "sorteios",
    metadata,
    Column("id", String, primary_key=True),
    Column("rodada_id", String, ForeignKey("rodadas.id"), nullable=False),
    Column("indicacao_sorteada_id", String, ForeignKey("indicacoes.id"), nullable=False),
    Column("data_sorteio", DateTime, nullable=False),
    Column("metodo", String, nullable=False),
)

sessoes_exibicao = Table(
    "sessoes_exibicao",
    metadata,
    Column("id", String, primary_key=True),
    Column("indicacao_id", String, ForeignKey("indicacoes.id"), nullable=False, unique=True),
    Column("data_sessao", Date, nullable=False),
)

sessao_membros_presentes = Table(
    "sessao_membros_presentes",
    metadata,
    Column("sessao_id", String, ForeignKey("sessoes_exibicao.id"), primary_key=True),
    Column("membro_id", String, ForeignKey("membros.id"), primary_key=True),
)

avaliacoes = Table(
    "avaliacoes",
    metadata,
    Column("id", String, primary_key=True),
    Column("sessao_id", String, ForeignKey("sessoes_exibicao.id"), nullable=False),
    Column("membro_id", String, ForeignKey("membros.id"), nullable=False),
    Column("status", String, nullable=False),
    Column("nota", String, nullable=True),
    Column("comentario", String, nullable=True),
)

temporadas_oscar = Table(
    "temporadas_oscar",
    metadata,
    Column("id", String, primary_key=True),
    Column("clube_id", String, ForeignKey("clubes.id"), nullable=False),
    Column("ano", Integer, nullable=False),
    Column("nome", String, nullable=False),
    Column("status", String, nullable=False),
    Column("data_evento", Date, nullable=True),
)

categorias_oscar = Table(
    "categorias_oscar",
    metadata,
    Column("id", String, primary_key=True),
    Column("temporada_id", String, ForeignKey("temporadas_oscar.id"), nullable=False),
    Column("nome", String, nullable=False),
    Column("tipo", String, nullable=False),
    Column("descricao", String, nullable=True),
)

nomeacoes_oscar = Table(
    "nomeacoes_oscar",
    metadata,
    Column("id", String, primary_key=True),
    Column("categoria_id", String, ForeignKey("categorias_oscar.id"), nullable=False),
    Column("filme_id", String, ForeignKey("filmes.id"), nullable=False),
    Column("indicado_por_membro_id", String, ForeignKey("membros.id"), nullable=True),
)

trofeus = Table(
    "trofeus",
    metadata,
    Column("id", String, primary_key=True),
    Column("categoria_id", String, ForeignKey("categorias_oscar.id"), nullable=False, unique=True),
    Column("nomeacao_vencedora_id", String, ForeignKey("nomeacoes_oscar.id"), nullable=False),
    Column("membro_vencedor_id", String, ForeignKey("membros.id"), nullable=False),
    Column("data_apuracao", Date, nullable=False),
)
