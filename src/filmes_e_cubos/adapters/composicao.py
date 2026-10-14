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
from filmes_e_cubos.adapters.persistence.sqlite.cedula_repository_sqlite import (
    CedulaRepositorioSqlite,
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
from filmes_e_cubos.adapters.persistence.sqlite.turno_de_votacao_repository_sqlite import (
    TurnoDeVotacaoRepositorioSqlite,
)
from filmes_e_cubos.adapters.persistence.sqlite.votacao_oscar_repository_sqlite import (
    VotacaoOscarRepositorioSqlite,
)
from filmes_e_cubos.adapters.servicos.enviador_smtp import enviador_do_ambiente
from filmes_e_cubos.adapters.servicos.relogio_sistema import RelogioSistema
from filmes_e_cubos.adapters.servicos.sorteador_aleatorio import SorteadorAleatorio
from filmes_e_cubos.application.ports.avaliacao_repository import AvaliacaoRepository
from filmes_e_cubos.application.ports.categoria_oscar_repository import CategoriaOscarRepository
from filmes_e_cubos.application.ports.cedula_repository import CedulaRepository
from filmes_e_cubos.application.ports.clube_repository import ClubeRepository
from filmes_e_cubos.application.ports.enviador_de_email import EnviadorDeEmail
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
from filmes_e_cubos.application.ports.turno_de_votacao_repository import (
    TurnoDeVotacaoRepository,
)
from filmes_e_cubos.application.ports.votacao_oscar_repository import VotacaoOscarRepository
from filmes_e_cubos.application.use_cases.abrir_nova_rodada import AbrirNovaRodada
from filmes_e_cubos.application.use_cases.abrir_temporada_oscar import AbrirTemporadaOscar
from filmes_e_cubos.application.use_cases.adicionar_filme_democracia import AdicionarFilmeDemocracia
from filmes_e_cubos.application.use_cases.avaliar_filme import AvaliarFilme
from filmes_e_cubos.application.use_cases.avancar_temporada_oscar import (
    AvancarTemporadaOscar,
)
from filmes_e_cubos.application.use_cases.cadastrar_filme import CadastrarFilme
from filmes_e_cubos.application.use_cases.cadastrar_membro import CadastrarMembro
from filmes_e_cubos.application.use_cases.confirmar_cedula import ConfirmarCedula
from filmes_e_cubos.application.use_cases.criar_clube import CriarClube
from filmes_e_cubos.application.use_cases.definir_categoria_oscar import DefinirCategoriaOscar
from filmes_e_cubos.application.use_cases.definir_data_evento_oscar import DefinirDataEventoOscar
from filmes_e_cubos.application.use_cases.definir_duracao_filme import DefinirDuracaoFilme
from filmes_e_cubos.application.use_cases.desativar_membro import DesativarMembro
from filmes_e_cubos.application.use_cases.encerrar_rodada import EncerrarRodada
from filmes_e_cubos.application.use_cases.enviar_placar_oscar import EnviarPlacarOscar
from filmes_e_cubos.application.use_cases.indicar_filme import IndicarFilme
from filmes_e_cubos.application.use_cases.indicar_filme_para_categoria import (
    IndicarFilmeParaCategoria,
)
from filmes_e_cubos.application.use_cases.realizar_sorteio import RealizarSorteio
from filmes_e_cubos.application.use_cases.reativar_membro import ReativarMembro
from filmes_e_cubos.application.use_cases.registrar_sessao_exibicao import RegistrarSessaoExibicao
from filmes_e_cubos.application.use_cases.registrar_vencedor_oscar import (
    RegistrarVencedorOscar,
)
from filmes_e_cubos.application.use_cases.registrar_voto import RegistrarVoto

CAMINHO_BANCO_PADRAO = Path("filmes_e_cubos.db")
"""Onde os dados ficam quando nada diferente é configurado: no diretório atual."""

VARIAVEL_DE_AMBIENTE_BANCO = "FILMES_E_CUBOS_DB"
"""Variável de ambiente que aponta o arquivo SQLite, respeitada por todas as interfaces."""

VARIAVEL_DE_AMBIENTE_URL_DO_BANCO = "DATABASE_URL"
"""URL de um banco de dados — em produção, o Postgres que a Neon injeta na Vercel.

Quando definida, vale no lugar do arquivo SQLite (o nome é o que a
integração da Neon com a Vercel usa).
"""


class Contexto:
    """Grafo de dependências já montado que uma interface consome.

    Expõe os casos de uso (para executar ações) e os repositórios (para as
    listagens de leitura, que não têm caso de uso próprio — ver a ADR 7 em
    docs/ARQUITETURA.md).

    `relogio`, `sorteador` e `enviador` são opcionais para que testes e
    embarcadores possam trocar as implementações reais por outras (um
    relógio fixo, um sorteio determinístico, um e-mail que não sai da
    máquina) sem mexer em nenhuma interface. O enviador padrão é o SMTP
    configurado pelo ambiente — desligado, se não houver servidor.
    """

    def __init__(
        self,
        engine: Engine,
        *,
        relogio: RelogioService | None = None,
        sorteador: SorteadorService | None = None,
        enviador: EnviadorDeEmail | None = None,
    ) -> None:
        self.relogio: RelogioService = relogio or RelogioSistema()
        self.enviador: EnviadorDeEmail = enviador or enviador_do_ambiente()
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
        self.votacoes: VotacaoOscarRepository = VotacaoOscarRepositorioSqlite(engine)
        self.turnos: TurnoDeVotacaoRepository = TurnoDeVotacaoRepositorioSqlite(engine)
        self.cedulas: CedulaRepository = CedulaRepositorioSqlite(engine)

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
        self.avancar_temporada_oscar = AvancarTemporadaOscar(
            temporada_repository=self.temporadas,
            categoria_repository=self.categorias,
            nomeacao_repository=self.nomeacoes,
            trofeu_repository=self.trofeus,
            membro_repository=self.membros,
            votacao_repository=self.votacoes,
            turno_repository=self.turnos,
            relogio=self.relogio,
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
            rodada_repository=self.rodadas,
        )
        self.registrar_voto = RegistrarVoto(
            temporada_repository=self.temporadas,
            categoria_repository=self.categorias,
            votacao_repository=self.votacoes,
            turno_repository=self.turnos,
            cedula_repository=self.cedulas,
        )
        self.enviar_placar_oscar = EnviarPlacarOscar(
            temporada_repository=self.temporadas,
            categoria_repository=self.categorias,
            nomeacao_repository=self.nomeacoes,
            filme_repository=self.filmes,
            membro_repository=self.membros,
            votacao_repository=self.votacoes,
            turno_repository=self.turnos,
            enviador=self.enviador,
        )
        self.confirmar_cedula = ConfirmarCedula(
            temporada_repository=self.temporadas,
            categoria_repository=self.categorias,
            votacao_repository=self.votacoes,
            turno_repository=self.turnos,
            cedula_repository=self.cedulas,
            relogio=self.relogio,
        )
        self.registrar_vencedor_oscar = RegistrarVencedorOscar(
            trofeu_repository=self.trofeus,
            categoria_repository=self.categorias,
            nomeacao_repository=self.nomeacoes,
            temporada_repository=self.temporadas,
            votacao_repository=self.votacoes,
            membro_repository=self.membros,
            relogio=self.relogio,
        )
