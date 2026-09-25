"""Composition root: monta repositórios, serviços e casos de uso.

Este é o único módulo do projeto que conhece, ao mesmo tempo, todos os
ports e todas as suas implementações concretas. É aqui — e somente aqui —
que a escolha "SQLite" e a escolha "relógio do sistema" são feitas. As
interfaces (CLI, API HTTP e web) pedem um `Contexto` já montado e
enxergam apenas casos de uso e contratos.

As anotações de tipo dos repositórios usam os *ports* (`ClubeRepository`
e companhia), não as classes concretas: assim o `mypy` verifica, neste
ponto de montagem, que cada adapter realmente satisfaz o contrato que diz
implementar.

O critério de apuração do Óscar é a exceção deliberada: ele não é
escolhido aqui, e sim por cada interface. O mecanismo de apuração
continua em aberto no produto, e cada interface o delega a quem opera de
um jeito diferente — a CLI pergunta no terminal; a API e a web recebem a
escolha na própria requisição. Por isso `ApurarCategoriaOscar` é montado
sob demanda, com o critério que a interface fornecer
(`Contexto.apurar_categoria_oscar`).
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine

from filmes_e_cubos.adapters.persistence.sqlite.avaliacao_repository_sqlite import (
    AvaliacaoRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.categoria_oscar_repository_sqlite import (
    CategoriaOscarRepositorioSqlite,
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
from filmes_e_cubos.adapters.persistence.sqlite.nomeacao_oscar_repository_sqlite import (
    NomeacaoOscarRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.rodada_repository_sqlite import (
    RodadaRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.sessao_repository_sqlite import (
    SessaoRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.sorteio_repository_sqlite import (
    SorteioRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.temporada_oscar_repository_sqlite import (
    TemporadaOscarRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.trofeu_repository_sqlite import (
    TrofeuRepositorioSqlite,
)
from filmes_e_cubos.adapters.servicos.relogio_sistema import RelogioSistema
from filmes_e_cubos.adapters.servicos.sorteador_aleatorio import SorteadorAleatorio
from filmes_e_cubos.application.ports.avaliacao_repository import AvaliacaoRepository
from filmes_e_cubos.application.ports.categoria_oscar_repository import CategoriaOscarRepository
from filmes_e_cubos.application.ports.clube_repository import ClubeRepository
from filmes_e_cubos.application.ports.criterio_apuracao_oscar import CriterioApuracaoOscar
from filmes_e_cubos.application.ports.filme_repository import FilmeRepository
from filmes_e_cubos.application.ports.indicacao_repository import IndicacaoRepository
from filmes_e_cubos.application.ports.membro_repository import MembroRepository
from filmes_e_cubos.application.ports.nomeacao_oscar_repository import NomeacaoOscarRepository
from filmes_e_cubos.application.ports.relogio_service import RelogioService
from filmes_e_cubos.application.ports.rodada_repository import RodadaRepository
from filmes_e_cubos.application.ports.sessao_repository import SessaoRepository
from filmes_e_cubos.application.ports.sorteador_service import SorteadorService
from filmes_e_cubos.application.ports.sorteio_repository import SorteioRepository
from filmes_e_cubos.application.ports.temporada_oscar_repository import TemporadaOscarRepository
from filmes_e_cubos.application.ports.trofeu_repository import TrofeuRepository
from filmes_e_cubos.application.use_cases.abrir_nova_rodada import AbrirNovaRodada
from filmes_e_cubos.application.use_cases.abrir_temporada_oscar import AbrirTemporadaOscar
from filmes_e_cubos.application.use_cases.adicionar_filme_democracia import AdicionarFilmeDemocracia
from filmes_e_cubos.application.use_cases.apurar_categoria_oscar import ApurarCategoriaOscar
from filmes_e_cubos.application.use_cases.avaliar_filme import AvaliarFilme
from filmes_e_cubos.application.use_cases.cadastrar_filme import CadastrarFilme
from filmes_e_cubos.application.use_cases.cadastrar_membro import CadastrarMembro
from filmes_e_cubos.application.use_cases.criar_clube import CriarClube
from filmes_e_cubos.application.use_cases.definir_categoria_oscar import DefinirCategoriaOscar
from filmes_e_cubos.application.use_cases.definir_data_evento_oscar import DefinirDataEventoOscar
from filmes_e_cubos.application.use_cases.definir_duracao_filme import DefinirDuracaoFilme
from filmes_e_cubos.application.use_cases.desativar_membro import DesativarMembro
from filmes_e_cubos.application.use_cases.encerrar_rodada import EncerrarRodada
from filmes_e_cubos.application.use_cases.indicar_filme import IndicarFilme
from filmes_e_cubos.application.use_cases.indicar_filme_para_categoria import (
    IndicarFilmeParaCategoria,
)
from filmes_e_cubos.application.use_cases.realizar_sorteio import RealizarSorteio
from filmes_e_cubos.application.use_cases.reativar_membro import ReativarMembro
from filmes_e_cubos.application.use_cases.registrar_sessao_exibicao import RegistrarSessaoExibicao

CAMINHO_BANCO_PADRAO = Path("filmes_e_cubos.db")
"""Onde os dados ficam quando nada diferente é configurado: no diretório atual."""

VARIAVEL_DE_AMBIENTE_BANCO = "FILMES_E_CUBOS_DB"
"""Variável de ambiente que aponta o arquivo SQLite, respeitada por todas as interfaces."""


class Contexto:
    """Grafo de dependências já montado que uma interface consome.

    Expõe os casos de uso (para executar ações) e os repositórios (para as
    listagens de leitura, que não têm caso de uso próprio — ver a ADR 7 em
    docs/ARQUITETURA.md).

    `relogio` e `sorteador` são opcionais para que testes e embarcadores
    possam trocar as implementações reais por outras (um relógio fixo, um
    sorteio determinístico) sem mexer em nenhuma interface.
    """

    def __init__(
        self,
        engine: Engine,
        *,
        relogio: RelogioService | None = None,
        sorteador: SorteadorService | None = None,
    ) -> None:
        self.relogio: RelogioService = relogio or RelogioSistema()
        sorteador = sorteador or SorteadorAleatorio()

        self.clubes: ClubeRepository = ClubeRepositorioSqlite(engine)
        self.membros: MembroRepository = MembroRepositorioSqlite(engine)
        self.filmes: FilmeRepository = FilmeRepositorioSqlite(engine)
        self.rodadas: RodadaRepository = RodadaRepositorioSqlite(engine)
        self.indicacoes: IndicacaoRepository = IndicacaoRepositorioSqlite(engine)
        self.sorteios: SorteioRepository = SorteioRepositorioSqlite(engine)
        self.sessoes: SessaoRepository = SessaoRepositorioSqlite(engine)
        self.avaliacoes: AvaliacaoRepository = AvaliacaoRepositorioSqlite(engine)
        self.temporadas: TemporadaOscarRepository = TemporadaOscarRepositorioSqlite(engine)
        self.categorias: CategoriaOscarRepository = CategoriaOscarRepositorioSqlite(engine)
        self.nomeacoes: NomeacaoOscarRepository = NomeacaoOscarRepositorioSqlite(engine)
        self.trofeus: TrofeuRepository = TrofeuRepositorioSqlite(engine)

        self.criar_clube = CriarClube(clube_repository=self.clubes)
        self.cadastrar_membro = CadastrarMembro(
            membro_repository=self.membros,
            clube_repository=self.clubes,
            relogio=self.relogio,
        )
        self.desativar_membro = DesativarMembro(membro_repository=self.membros)
        self.reativar_membro = ReativarMembro(membro_repository=self.membros)
        self.cadastrar_filme = CadastrarFilme(filme_repository=self.filmes)
        self.definir_duracao_filme = DefinirDuracaoFilme(filme_repository=self.filmes)
        self.abrir_nova_rodada = AbrirNovaRodada(
            rodada_repository=self.rodadas,
            clube_repository=self.clubes,
            relogio=self.relogio,
        )
        self.indicar_filme = IndicarFilme(
            indicacao_repository=self.indicacoes,
            rodada_repository=self.rodadas,
            membro_repository=self.membros,
            filme_repository=self.filmes,
            clube_repository=self.clubes,
            relogio=self.relogio,
        )
        self.adicionar_filme_democracia = AdicionarFilmeDemocracia(
            indicacao_repository=self.indicacoes,
            rodada_repository=self.rodadas,
            filme_repository=self.filmes,
            relogio=self.relogio,
        )
        self.realizar_sorteio = RealizarSorteio(
            indicacao_repository=self.indicacoes,
            rodada_repository=self.rodadas,
            sorteio_repository=self.sorteios,
            sorteador=sorteador,
            relogio=self.relogio,
        )
        self.encerrar_rodada = EncerrarRodada(
            rodada_repository=self.rodadas,
            indicacao_repository=self.indicacoes,
            relogio=self.relogio,
        )
        self.registrar_sessao_exibicao = RegistrarSessaoExibicao(
            sessao_repository=self.sessoes,
            indicacao_repository=self.indicacoes,
            relogio=self.relogio,
        )
        self.avaliar_filme = AvaliarFilme(
            avaliacao_repository=self.avaliacoes,
            sessao_repository=self.sessoes,
            membro_repository=self.membros,
            indicacao_repository=self.indicacoes,
            rodada_repository=self.rodadas,
            clube_repository=self.clubes,
        )
        self.abrir_temporada_oscar = AbrirTemporadaOscar(
            temporada_repository=self.temporadas,
            clube_repository=self.clubes,
        )
        self.definir_data_evento_oscar = DefinirDataEventoOscar(
            temporada_repository=self.temporadas
        )
        self.definir_categoria_oscar = DefinirCategoriaOscar(
            categoria_repository=self.categorias,
            temporada_repository=self.temporadas,
        )
        self.indicar_filme_para_categoria = IndicarFilmeParaCategoria(
            nomeacao_repository=self.nomeacoes,
            categoria_repository=self.categorias,
            temporada_repository=self.temporadas,
            indicacao_repository=self.indicacoes,
            sessao_repository=self.sessoes,
        )

    def apurar_categoria_oscar(self, criterio: CriterioApuracaoOscar) -> ApurarCategoriaOscar:
        """Monta a apuração com o critério que a interface escolheu.

        É o único caso de uso montado sob demanda — ver a explicação no
        topo deste módulo.
        """
        return ApurarCategoriaOscar(
            trofeu_repository=self.trofeus,
            nomeacao_repository=self.nomeacoes,
            categoria_repository=self.categorias,
            criterio=criterio,
            relogio=self.relogio,
        )
