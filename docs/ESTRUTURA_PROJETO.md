# Estrutura do Projeto

Este documento descreve a estrutura de pastas do projeto, alinhada com a
arquitetura definida em [ARQUITETURA.md](ARQUITETURA.md).
`domain/`, `application/` (Fase 1) e `adapters/persistence/` +
`adapters/servicos/` (Fase 2, persistência SQLite) já existem e estão
implementados e testados. `adapters/interfaces/` (Fase 3, CLI) **ainda
não existe** — ver [ROADMAP.md](ROADMAP.md) e a seção "Como continuar a
Fase 3" do [README.md](../README.md).

## Árvore de diretórios

```
FilmesECodes/
├── README.md
├── docs/
│   ├── ARQUITETURA.md
│   ├── DOMINIO.md
│   ├── CASOS_DE_USO.md
│   ├── ESTRUTURA_PROJETO.md
│   ├── ROADMAP.md
│   └── GLOSSARIO.md
├── pyproject.toml                     # gerenciado via uv
├── src/
│   └── filmes_e_cubos/
│       ├── __init__.py
│       ├── domain/
│       │   ├── entities/              # Clube, Membro, Filme, Rodada, ...
│       │   ├── value_objects/         # ex.: Nota, ConfiguracaoClube
│       │   └── exceptions/            # erros de invariante de domínio
│       ├── application/
│       │   ├── use_cases/             # um módulo por caso de uso (15, após Fase 2)
│       │   └── ports/                 # Protocols: repositórios, SorteadorService,
│       │                              # RelogioService, CriterioApuracaoOscar
│       └── adapters/
│           ├── persistence/
│           │   └── sqlite/            # ✅ Fase 2: esquema, engine, 12 repositórios
│           ├── servicos/              # ✅ Fase 2: RelogioSistema, SorteadorAleatorio
│           └── interfaces/            # ⏳ Fase 3: CLI — AINDA NÃO EXISTE
│               └── cli/               # (a criar: main.py, comandos_*.py, ...)
└── tests/
    ├── conftest.py
    ├── domain/
    │   ├── value_objects/
    │   └── entities/
    ├── application/
    │   ├── fakes/                     # implementações in-memory dos ports
    │   └── use_cases/
    └── adapters/
        └── persistence/
            └── sqlite/                # testes de integração, um arquivo por repositório
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
  que os casos de uso declaram precisar — sem nenhuma implementação
  concreta nesta fase.
- **`src/filmes_e_cubos/adapters/persistence/sqlite/`**: implementações
  concretas dos ports de repositório usando SQLAlchemy Core + SQLite (ver
  [ARQUITETURA.md](ARQUITETURA.md) para o racional de Core vs. ORM).
- **`src/filmes_e_cubos/adapters/servicos/`**: implementações concretas
  de `RelogioService` e `SorteadorService` usando o relógio e o gerador
  aleatório reais do sistema.
- **`src/filmes_e_cubos/adapters/interfaces/`**: reservado para a
  interface de usuário (CLI na Fase 3). Ainda não existe.
- **`tests/`**: espelha a estrutura de `src/`, com testes de domínio
  (regras de negócio isoladas), de aplicação (casos de uso com
  implementações de teste/fake dos ports) e de adapters (persistência
  testada de ponta a ponta contra um SQLite real, não fakes).

## Ferramentas e convenções previstas

| Ferramenta | Uso |
|---|---|
| [`uv`](https://docs.astral.sh/uv/) | Gerenciamento de ambiente virtual e dependências, substituindo pip/venv/poetry. |
| `pytest` | Framework de testes. |
| `ruff` | Lint e formatação (substitui flake8/black/isort). |
| `mypy` | Verificação estática de tipos — importante para validar os contratos (`Protocol`) entre camadas. |
| `sqlalchemy` (Core) | Persistência SQLite na Fase 2 — tabelas explícitas, sem ORM declarativo. |
| `typer` | Framework de CLI para a Fase 3 (dependência já adicionada; uso ainda pendente). |

### Convenções de nomenclatura

- Conceitos de domínio (entidades, casos de uso, campos de negócio) são
  nomeados em **português**, fiéis à linguagem que o clube já usa
  (`Membro`, `Rodada`, `Sorteio`, `Trofeu`) — mantém o código próximo da
  linguagem ubíqua do domínio.
- Termos puramente técnicos e genéricos (nomes de módulos padrão,
  utilitários de infraestrutura) podem seguir convenções em inglês quando
  isso for mais natural no ecossistema Python (ex.: nomes de exceções
  base, utilitários internos). Esta convivência será refinada quando o
  código começar a ser escrito.
- Um caso de uso = um verbo no infinitivo + objeto (`IndicarFilme`,
  `RealizarSorteio`), espelhando a lista em
  [CASOS_DE_USO.md](CASOS_DE_USO.md).

## O que fica para depois

- Implementação da CLI (Fase 3) — ver "Como continuar a Fase 3" no
  [README.md](../README.md).
