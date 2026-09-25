# Estrutura do Projeto

Este documento descreve a estrutura de pastas do projeto, alinhada com a
arquitetura definida em [ARQUITETURA.md](ARQUITETURA.md).
As camadas implementadas e testadas até aqui: `domain/` e `application/`
(Fase 1), `adapters/persistence/` e `adapters/servicos/` (Fase 2),
`adapters/interfaces/cli/` (Fase 3) e `adapters/interfaces/api/` (Fase 4).

## Árvore de diretórios

```
FilmesECodes/
├── README.md
├── docs/
│   ├── ARQUITETURA.md
│   ├── DOMINIO.md
│   ├── CASOS_DE_USO.md
│   ├── ESTRUTURA_PROJETO.md
│   ├── CLI.md
│   ├── API.md
│   ├── ROADMAP.md
│   └── GLOSSARIO.md
├── pyproject.toml                     # gerenciado via uv
├── src/
│   └── filmes_e_cubos/
│       ├── __init__.py                # __version__, lida dos metadados do pacote
│       ├── domain/
│       │   ├── entities/              # Clube, Membro, Filme, Rodada, ...
│       │   ├── value_objects/         # ex.: Nota, ConfiguracaoClube
│       │   └── exceptions/            # erros de invariante de domínio
│       ├── application/
│       │   ├── use_cases/             # um módulo por caso de uso (18)
│       │   └── ports/                 # Protocols: repositórios, SorteadorService,
│       │                              # RelogioService, CriterioApuracaoOscar
│       └── adapters/
│           ├── composicao.py          # composition root: engine -> repos -> casos de uso
│           ├── persistence/
│           │   └── sqlite/            # ✅ Fase 2: esquema, engine, 12 repositórios
│           │       ├── migracao.py    # Fase 4: leva o banco à revisão mais recente
│           │       └── migracoes/     # Fase 4: env.py do Alembic e versions/
│           ├── servicos/              # ✅ Fase 2: RelogioSistema, SorteadorAleatorio;
│           │                          # Fase 4: CriterioEscolhaInformada
│           └── interfaces/
│               ├── convencoes.py      # padrões deduzidos, iguais em todas as interfaces
│               ├── consultas.py       # buscas por id que precisam encontrar a entidade
│               ├── estrelas.py        # a média das notas em estrelas (★★★⅔)
│               ├── erros_http.py      # erro de domínio -> status HTTP (API e web)
│               ├── contexto_http.py   # injeção do Contexto nas rotas HTTP
│               ├── escritas_em_fila.py  # middleware: uma escrita HTTP por vez
│               ├── servidor.py        # app ASGI completo + entry point do servidor
│               ├── web/               # 🚧 Fase 4: por ora, formatacao, mensagens e
│               │                      # formularios (apoio das páginas)
│               ├── cli/               # ✅ Fase 3
│               │   ├── main.py        # app Typer raiz; monta os grupos de comando
│               │   ├── contexto.py    # quando montar o composition root; critério da CLI
│               │   ├── erros.py       # CliError + tradução de erros para stderr/exit 1
│               │   ├── resolucao.py   # clube/rodada/temporada "correntes" quando omitidos
│               │   ├── conversores.py # texto da linha de comando -> tipos do domínio
│               │   ├── apresentacao.py            # tabelas e mensagens
│               │   ├── criterio_apuracao_interativo.py  # CriterioApuracaoOscar via prompt
│               │   └── comandos/      # um módulo por grupo: clube, membro, filme,
│               │                      # rodada, indicacao, sessao, avaliacao, oscar
│               └── api/               # ✅ Fase 4
│                   ├── app.py         # criar_api(): sub-app FastAPI montado em /api/v1
│                   ├── esquemas.py    # formato JSON de entrada e saída (Pydantic)
│                   ├── erros.py       # erros -> application/problem+json (RFC 9457)
│                   └── rotas/         # um módulo por grupo: clubes, membros, filmes,
│                                      # rodadas, indicacoes, sessoes, avaliacoes, oscar
└── tests/
    ├── conftest.py
    ├── domain/
    │   ├── value_objects/
    │   └── entities/
    ├── application/
    │   ├── fakes/                     # implementações in-memory dos ports
    │   └── use_cases/
    └── adapters/
        ├── persistence/
        │   └── sqlite/                # testes de integração, um arquivo por repositório
        ├── servicos/
        └── interfaces/                # convenções, middleware e servidor
            ├── cli/                   # CLI real contra SQLite temporário, um arquivo
            │                          # por grupo de comandos + fluxo de ponta a ponta
            ├── api/                   # API real (app ASGI completo) contra SQLite
            │                          # temporário, idem
            └── web/                   # módulos de apoio da interface web
```

## Responsabilidade de cada pasta

- **`src/filmes_e_cubos/domain/`**: entidades, value objects e exceções de
  domínio. Não importa nada de `application` ou `adapters`. É a única
  camada que deve ser 100% testável sem nenhum tipo de mock de
  infraestrutura.
- **`src/filmes_e_cubos/application/use_cases/`**: um caso de uso por
  arquivo/módulo (ver [CASOS_DE_USO.md](CASOS_DE_USO.md)), recebendo os
  ports de que precisa via injeção de dependência manual (construtor).
- **`src/filmes_e_cubos/application/ports/`**: contratos (`Protocol`/ABC)
  que os casos de uso declaram precisar. Quem implementa cada um mora em
  `adapters/` — e o único ponto que amarra contrato a implementação é o
  composition root, `adapters/composicao.py`.
- **`src/filmes_e_cubos/adapters/persistence/sqlite/`**: implementações
  concretas dos ports de repositório usando SQLAlchemy Core + SQLite (ver
  [ARQUITETURA.md](ARQUITETURA.md) para o racional de Core vs. ORM).
- **`src/filmes_e_cubos/adapters/servicos/`**: implementações concretas
  de `RelogioService` e `SorteadorService` usando o relógio e o gerador
  aleatório reais do sistema, e o `CriterioEscolhaInformada` (critério de
  apuração do Óscar em que a vencedora chega escolhida).
- **`src/filmes_e_cubos/adapters/interfaces/`**: as interfaces com o
  usuário e o que elas compartilham (convenções, consultas por id, o
  middleware de escritas e o servidor HTTP). Nenhuma regra de negócio
  mora aqui.
  - **`cli/`**: a interface de linha de comando (ver [CLI.md](CLI.md)).
    `contexto.py` decide quando montar o composition root e qual critério
    de apuração do Óscar a CLI usa.
  - **`api/`**: a API HTTP (ver [API.md](API.md)). Traduz requisições em
    chamadas aos casos de uso e erros em `application/problem+json`.
- **`tests/`**: espelha a estrutura de `src/`, com testes de domínio
  (regras de negócio isoladas), de aplicação (casos de uso com
  implementações de teste/fake dos ports) e de adapters — estes sempre
  contra o componente real: a persistência contra um SQLite de verdade, a
  CLI contra o app Typer de verdade e a API contra o app ASGI de verdade,
  nunca contra fakes.

## Ferramentas e convenções

| Ferramenta | Uso |
|---|---|
| [`uv`](https://docs.astral.sh/uv/) | Gerenciamento de ambiente virtual e dependências, substituindo pip/venv/poetry. |
| `pytest` | Framework de testes. |
| `ruff` | Lint e formatação (substitui flake8/black/isort). |
| `mypy` | Verificação estática de tipos (modo estrito) — importante para validar os contratos (`Protocol`) entre camadas. |
| `sqlalchemy` (Core) | Persistência SQLite na Fase 2 — tabelas explícitas, sem ORM declarativo. |
| `typer` | Framework da CLI (Fase 3), com o entry point `filmes-e-cubos`. |
| `fastapi` + `uvicorn` | API HTTP (Fase 4), servida pelo entry point `filmes-e-cubos-servidor`. |
| `httpx2` | Cliente HTTP usado pelo `TestClient` do Starlette nos testes (dependência só de desenvolvimento). |

### Convenções de nomenclatura

- Conceitos de domínio (entidades, casos de uso, campos de negócio) são
  nomeados em **português**, fiéis à linguagem que o clube já usa
  (`Membro`, `Rodada`, `Sorteio`, `Trofeu`) — mantém o código próximo da
  linguagem ubíqua do domínio.
- Termos puramente técnicos e genéricos seguem convenções em inglês
  quando isso é mais natural no ecossistema Python: os ports levam o
  sufixo `Repository`/`Service`, e as exceções base são `DomainError` e
  `CliError` (o sufixo `Error` é exigido pela regra N818 do `ruff`, que o
  projeto adota). As exceções específicas, porém, continuam em português:
  `RodadaJaAbertaError`, `NotaForaDaEscalaError`. Os campos padronizados
  pela RFC 9457 nas respostas de erro da API (`type`, `title`, `status`,
  `detail`) também ficam em inglês, porque são exigidos pelo padrão.
- Um caso de uso = um verbo no infinitivo + objeto (`IndicarFilme`,
  `RealizarSorteio`), espelhando a lista em
  [CASOS_DE_USO.md](CASOS_DE_USO.md).
- Na API, os esquemas de saída levam o sufixo `Saida` (`ClubeSaida`), os
  corpos de criação começam por `Novo`/`Nova` (`NovoClube`,
  `NovaIndicacao`) e os espelhos de enumerações do domínio levam o
  sufixo `Api` (`StatusRodadaApi`), como o `TipoCategoriaCli` da CLI.

Na raiz do repositório, `alembic.ini` serve só ao desenvolvimento
(gerar revisões com `uv run alembic revision --autogenerate -m "..."`);
o programa migra o banco sozinho. `CLAUDE.md` resume, para quem continua
o trabalho, os comandos, as convenções e as armadilhas do ambiente.

## O que fica para depois

- As páginas da interface web (`adapters/interfaces/web/`), no mesmo
  servidor da API — ver "Como continuar" em [ROADMAP.md](ROADMAP.md).
