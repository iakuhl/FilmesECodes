"""Esquema SQLAlchemy Core do banco SQLite: tabelas e tipos, sem lógica de domínio.

Ids são armazenados como texto (`str(uuid.UUID)`), valores decimais (notas,
soma das notas e escala de avaliação) como texto (`str(Decimal)`, para
preservar precisão exata) e enums como o nome do membro (ex.: `"ABERTA"`).
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
    UniqueConstraint,
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
    Column("duracao_minutos", Integer, nullable=True),
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
    # Ordem de criação (ver revisão 0006): o Postgres não garante ordem sem ORDER BY.
    Column("ordem", Integer, nullable=False, server_default="0"),
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
    # A média das notas, como fração: soma ÷ quantidade. Sem notas, 0 e 0.
    Column("soma_das_notas", String, nullable=False, server_default="0"),
    Column("quantidade_de_notas", Integer, nullable=False, server_default="0"),
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
    # Ordem de criação (ver revisão 0006): o Postgres não garante ordem sem ORDER BY.
    Column("ordem", Integer, nullable=False, server_default="0"),
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
    Column("nomeacoes_por_categoria", Integer, nullable=False, server_default="5"),
)

categorias_oscar = Table(
    "categorias_oscar",
    metadata,
    Column("id", String, primary_key=True),
    Column("temporada_id", String, ForeignKey("temporadas_oscar.id"), nullable=False),
    Column("nome", String, nullable=False),
    Column("tipo", String, nullable=False),
    Column("descricao", String, nullable=True),
    # Ordem de criação (ver revisão 0006): o Postgres não garante ordem sem ORDER BY.
    Column("ordem", Integer, nullable=False, server_default="0"),
)

nomeacoes_oscar = Table(
    "nomeacoes_oscar",
    metadata,
    Column("id", String, primary_key=True),
    Column("categoria_id", String, ForeignKey("categorias_oscar.id"), nullable=False),
    Column("filme_id", String, ForeignKey("filmes.id"), nullable=False),
    Column("indicado_por_membro_id", String, ForeignKey("membros.id"), nullable=True),
    # Ordem de criação (ver revisão 0006): o Postgres não garante ordem sem ORDER BY.
    Column("ordem", Integer, nullable=False, server_default="0"),
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

votacoes_oscar = Table(
    "votacoes_oscar",
    metadata,
    Column("id", String, primary_key=True),
    Column("temporada_id", String, ForeignKey("temporadas_oscar.id"), nullable=False, unique=True),
    Column("iniciada_em", DateTime, nullable=False),
    Column("turno_atual", Integer, nullable=False),
    Column("encerrada_em", DateTime, nullable=True),
)

votacao_eleitores = Table(
    "votacao_eleitores",
    metadata,
    Column("votacao_id", String, ForeignKey("votacoes_oscar.id"), primary_key=True),
    Column("membro_id", String, ForeignKey("membros.id"), primary_key=True),
)

turnos_votacao = Table(
    "turnos_votacao",
    metadata,
    Column("id", String, primary_key=True),
    Column("categoria_id", String, ForeignKey("categorias_oscar.id"), nullable=False),
    Column("numero", Integer, nullable=False),
    Column("modo", String, nullable=False),
    Column("apurado_em", DateTime, nullable=True),
    UniqueConstraint("categoria_id", "numero"),
)

turno_candidatas = Table(
    "turno_candidatas",
    metadata,
    Column("turno_id", String, ForeignKey("turnos_votacao.id"), primary_key=True),
    Column("posicao", Integer, primary_key=True),
    Column("nomeacao_id", String, ForeignKey("nomeacoes_oscar.id"), nullable=False),
    # Os pontos da candidata, gravados quando o turno é apurado.
    Column("pontos", Integer, nullable=True),
)

cedulas = Table(
    "cedulas",
    metadata,
    Column("id", String, primary_key=True),
    Column("votacao_id", String, ForeignKey("votacoes_oscar.id"), nullable=False),
    Column("turno", Integer, nullable=False),
    Column("membro_id", String, ForeignKey("membros.id"), nullable=False),
    Column("confirmada_em", DateTime, nullable=True),
    UniqueConstraint("votacao_id", "turno", "membro_id"),
)

cedula_escolhas = Table(
    "cedula_escolhas",
    metadata,
    Column("cedula_id", String, ForeignKey("cedulas.id"), primary_key=True),
    Column("categoria_id", String, ForeignKey("categorias_oscar.id"), primary_key=True),
    # Ordem de preferência: 1 é a 1ª opção.
    Column("posicao", Integer, primary_key=True),
    Column("nomeacao_id", String, ForeignKey("nomeacoes_oscar.id"), nullable=False),
)
