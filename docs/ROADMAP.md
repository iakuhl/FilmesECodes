# Roadmap

Fases sugeridas de desenvolvimento, do núcleo de domínio até uma eventual
versão comercial. Cada fase só começa depois da anterior estar
razoavelmente sólida e testada — a arquitetura hexagonal existe justamente
para que essa progressão não exija retrabalho nas fases já prontas.

## Fase 1 — Núcleo de domínio e casos de uso

- Implementar as entidades e value objects descritos em
  [DOMINIO.md](DOMINIO.md), com seus invariantes garantidos por código
  (não apenas por documentação).
- Implementar os ports (`Protocol`) descritos em
  [ARQUITETURA.md](ARQUITETURA.md) e os casos de uso de
  [CASOS_DE_USO.md](CASOS_DE_USO.md), usando implementações de teste
  (fakes/in-memory) dos ports para validar as regras de negócio.
- Cobertura de testes de domínio e de aplicação como critério de saída
  desta fase — nenhum adapter real é necessário para isso.
- **Decisões ainda em aberto ao final desta fase**: nenhuma decisão de
  persistência ou interface é necessária aqui.

## Fase 2 — Primeiro adapter de persistência ✅ concluída

Decisão tomada: **SQLite via SQLAlchemy Core** (não o ORM declarativo — as
entidades de domínio continuam sendo classes ricas e independentes de
persistência; cada repositório converte manualmente entre entidade e
linha de tabela). Implementado em
`src/filmes_e_cubos/adapters/persistence/sqlite/`:

- `esquema.py`: todas as tabelas (`Table`/`MetaData` do SQLAlchemy Core).
  Ids como texto (`str(UUID)`), decimais (notas, escala) como texto
  (`str(Decimal)`, para preservar precisão exata), enums pelo nome
  (`"ABERTA"`, `"DEMOCRACIA"` etc.).
- `fabrica_engine.py`: `criar_engine(caminho_banco)` cria o engine e as
  tabelas.
- `_upsert.py`: utilitário interno de insert-or-update (via
  `INSERT ... ON CONFLICT DO UPDATE`), compartilhado pelos 12
  repositórios para evitar duplicar esse SQL.
- Um arquivo por repositório (`clube_repository_sqlite.py`,
  `membro_repository_sqlite.py`, ... até `trofeu_repository_sqlite.py`),
  implementando exatamente os ports já definidos em
  `application/ports/`.
- `src/filmes_e_cubos/adapters/servicos/`: implementações reais de
  `RelogioService` (`RelogioSistema`, usa `datetime`/`date` do sistema) e
  `SorteadorService` (`SorteadorAleatorio`, usa `random.choice`).
- Testes de integração em `tests/adapters/persistence/sqlite/` (um
  arquivo por repositório, contra um SQLite real em arquivo temporário
  via `tmp_path`), validando round-trip de cada entidade, incluindo
  campos opcionais, enums e precisão decimal.

Durante a Fase 2 também foram preenchidas duas lacunas que faltavam desde
a Fase 1 (nenhum caso de uso criava um `Clube` ou cadastrava um `Filme`,
o que impediria a CLI de funcionar de ponta a ponta): novos casos de uso
`CriarClube` e `CadastrarFilme`, e os ports `ClubeRepository`,
`FilmeRepository`, `MembroRepository` e `TemporadaOscarRepository`
ganharam métodos de listagem (`listar_todos`/`listar_por_clube`) usados
para exibição pela futura interface.

## Fase 3 — Primeira interface de usuário ✅ concluída

Decisão tomada e implementada: **CLI com [Typer](https://typer.tiangolo.com/)**,
em `src/filmes_e_cubos/adapters/interfaces/cli/`, com o entry point
`filmes-e-cubos` registrado em `pyproject.toml`. A referência completa dos
comandos está em [CLI.md](CLI.md).

A interface apenas traduz entrada e saída para chamadas aos casos de uso
já existentes — nenhuma regra de negócio nasceu aqui. O que a camada
acrescenta, e por quê:

- `main.py`: monta o app raiz a partir de oito grupos de comando
  (`clube`, `membro`, `filme`, `rodada`, `indicacao`, `sessao`,
  `avaliacao`, `oscar`), um módulo por grupo em `comandos/`.
- `contexto.py`: o **composition root** (promovido a
  `adapters/composicao.py` no início da Fase 4, quando uma segunda
  interface passou a precisar dele). Monta os 12 repositórios SQLite,
  os serviços de infraestrutura e os 15 casos de uso. Anota cada
  repositório com o tipo do *port*, não da classe concreta, de modo que o
  `mypy` verifica neste ponto que cada adapter satisfaz o contrato que
  diz implementar. A montagem é adiada por uma `FabricaDeContexto` para
  que consultar a ajuda (`--help`) não crie um banco vazio no diretório
  do usuário.
- `erros.py`: concentra o contrato de erro da interface — qualquer
  `DomainError` ou `CliError` vira mensagem em `stderr` com código de
  saída 1, traduzida em um único ponto (um `TyperGroup` customizado na
  raiz), de modo que um comando novo já nasce com o comportamento certo.
- `resolucao.py`: deduz clube, rodada aberta e temporada do ano quando o
  usuário omite o id — conveniência de interface, nunca decisão de
  negócio.
- `conversores.py`: fronteira entre o texto do terminal e os tipos do
  domínio (`Decimal`, `Nota`, enumerações).
- `criterio_apuracao_interativo.py`: implementação de
  `CriterioApuracaoOscar` que lista as nomeações e pergunta ao usuário
  quem venceu (ver a seção de pontos em aberto abaixo).
- `apresentacao.py`: tabelas e mensagens. A tabela é montada à mão, sem
  biblioteca de terminal: `rich` só existe como dependência transitiva do
  `typer` (que publica a variante `typer-slim`, sem ela), e depender dele
  sem declará-lo deixaria a CLI refém de um detalhe de empacotamento de
  terceiros.

Testes em `tests/adapters/interfaces/cli/` (107 testes): um arquivo por
grupo de comandos, mais testes de unidade da apresentação, dos
conversores, da resolução automática e do contrato de erro, e um teste de
ponta a ponta que percorre uma temporada inteira do clube. Todos rodam a
CLI de verdade, com `typer.testing.CliRunner`, contra um banco SQLite
real em `tmp_path`.

## Fase 4 — API / Web

- Caso haja interesse em uma interface mais rica (web) ou em uso remoto
  pelos membros do clube, adicionar um adapter de API (ex.: FastAPI) e,
  posteriormente, um frontend web.
- Reaproveita integralmente os casos de uso das fases anteriores.

## Fase 5 — Evolução comercial

- Suporte a múltiplos clubes (a entidade `Clube` já foi desenhada para
  isso desde a Fase 1).
- Autenticação/autorização de membros.
- Eventuais integrações externas (ex.: base de dados de filmes para
  autocompletar título/ano/diretor).
- Empacotamento e distribuição como produto.

## Pontos explicitamente em aberto

| Decisão | Status | Onde foi/será resolvida |
|---|---|---|
| Implementação concreta de persistência | ✅ Resolvida: SQLite via SQLAlchemy Core | Fase 2 |
| Primeira interface de usuário | ✅ Resolvida: CLI com Typer | Fase 3 |
| Mecanismo de apuração de categorias do Óscar (votação vs. critério fixo) | Continua em aberto no domínio — port `CriterioApuracaoOscar` plugável | A CLI usa `CriterioApuracaoInterativo`, que delega a escolha a quem opera. Quando o clube decidir um mecanismo automático, basta escrever outro adapter e trocá-lo no composition root. |
