"""Migrações do esquema do banco SQLite, com Alembic.

O esquema evolui (colunas e tabelas novas a cada fase), mas o banco de um
clube é um arquivo que precisa sobreviver às atualizações do programa.
Por isso toda mudança de esquema vira uma revisão do Alembic em
`migracoes/versions/`, e `migrar` leva qualquer banco até a revisão mais
recente sempre que o programa o abre.

Bancos criados antes de as migrações existirem (as Fases 2 e 3 criavam
as tabelas direto com `metadata.create_all`) não têm a tabela de
controle do Alembic. Eles são reconhecidos e marcados como estando na
revisão inicial — que reproduz exatamente aquele esquema — antes de
subir para as seguintes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, inspect

DIRETORIO_DE_MIGRACOES: Final = Path(__file__).parent / "migracoes"

REVISAO_INICIAL: Final = "0001"
"""Revisão que reproduz o esquema criado pelas Fases 2 e 3, antes das migrações."""

_TABELA_DE_CONTROLE: Final = "alembic_version"


def configuracao_alembic(url_do_banco: str | None = None) -> Config:
    """Configuração do Alembic apontando para os scripts deste pacote.

    Não depende de um `alembic.ini`: o programa instalado precisa migrar o
    banco sozinho, de qualquer diretório.
    """
    configuracao = Config()
    # O ConfigParser interpreta `%` como interpolação; caminhos precisam escapá-lo.
    configuracao.set_main_option("script_location", str(DIRETORIO_DE_MIGRACOES).replace("%", "%%"))
    configuracao.set_main_option("file_template", "revisao_%%(rev)s_%%(slug)s")
    if url_do_banco is not None:
        configuracao.set_main_option("sqlalchemy.url", url_do_banco.replace("%", "%%"))
    return configuracao


def migrar(engine: Engine) -> None:
    """Leva o banco do `engine` até a revisão mais recente do esquema."""
    configuracao = configuracao_alembic()
    with engine.begin() as conexao:
        configuracao.attributes["connection"] = conexao
        tabelas = set(inspect(conexao).get_table_names())
        if tabelas and _TABELA_DE_CONTROLE not in tabelas:
            command.stamp(configuracao, REVISAO_INICIAL)
        command.upgrade(configuracao, "head")
