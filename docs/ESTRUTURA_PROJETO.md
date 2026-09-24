# Estrutura do Projeto

Este documento descreve a estrutura de pastas do projeto, alinhada com a
arquitetura definida em [ARQUITETURA.md](ARQUITETURA.md).
Todas as camadas previstas até a Fase 3 existem e estão implementadas e
testadas: `domain/` e `application/` (Fase 1), `adapters/persistence/` e
`adapters/servicos/` (Fase 2) e `adapters/interfaces/cli/` (Fase 3).

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
│           ├── composicao.py          # composition root: engine -> repos -> casos de uso
│           ├── persistence/
│           │   └── sqlite/            # ✅ Fase 2: esquema, engine, 12 repositórios
│           ├── servicos/              # ✅ Fase 2: RelogioSistema, SorteadorAleatorio
│           └── interfaces/            # ✅ Fase 3: interface de usuário
│               ├── convencoes.py      # padrões deduzidos, iguais em todas as interfaces
│               └── cli/
│                   ├── main.py        # app Typer raiz; monta os grupos de comando
│                   ├── contexto.py    # quando montar o composition root; critério da CLI
│                   ├── erros.py       # CliError + tradução de erros para stderr/exit 1
│                   ├── resolucao.py   # clube/rodada/temporada "correntes" quando omitidos
│                   ├── conversores.py # texto da linha de comando -> tipos do domínio
│                   ├── apresentacao.py            # tabelas e mensagens
│                   ├── criterio_apuracao_interativo.py  # CriterioApuracaoOscar via prompt
│                   └── comandos/      # um módulo por grupo: clube, membro, filme,
│                                      # rodada, indicacao, sessao, avaliacao, oscar
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
        └── interfaces/
            └── cli/                   # CLI real contra SQLite temporário, um arquivo
                                       # por grupo de comandos + fluxo de ponta a ponta
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
  aleatório reais do sistema.
- **`src/filmes_e_cubos/adapters/interfaces/cli/`**: a interface de
  linha de comando (ver [CLI.md](CLI.md)). Traduz argumentos de terminal
  em chamadas aos casos de uso e formata o resultado — nenhuma regra de
  negócio mora aqui. `contexto.py` decide quando montar o composition
  root (`adapters/composicao.py`, o único ponto do projeto que conhece
  ports e implementações concretas ao mesmo tempo) e qual critério de
  apuração do Óscar a CLI usa.
- **`tests/`**: espelha a estrutura de `src/`, com testes de domínio
  (regras de negócio isoladas), de aplicação (casos de uso com
  implementações de teste/fake dos ports) e de adapters — estes sempre
  contra o componente real: a persistência contra um SQLite de verdade e
  a CLI contra o app Typer de verdade, nunca contra fakes.

## Ferramentas e convenções

| Ferramenta | Uso |
|---|---|
| [`uv`](https://docs.astral.sh/uv/) | Gerenciamento de ambiente virtual e dependências, substituindo pip/venv/poetry. |
| `pytest` | Framework de testes. |
| `ruff` | Lint e formatação (substitui flake8/black/isort). |
| `mypy` | Verificação estática de tipos — importante para validar os contratos (`Protocol`) entre camadas. |
| `sqlalchemy` (Core) | Persistência SQLite na Fase 2 — tabelas explícitas, sem ORM declarativo. |
| `typer` | Framework da CLI (Fase 3), com o entry point `filmes-e-cubos`. |

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
  `RodadaJaAbertaError`, `NotaForaDaEscalaError`.
- Um caso de uso = um verbo no infinitivo + objeto (`IndicarFilme`,
  `RealizarSorteio`), espelhando a lista em
  [CASOS_DE_USO.md](CASOS_DE_USO.md).

## O que fica para depois

- Adapter de API/web (Fase 4) entraria como
  `adapters/interfaces/api/`, ao lado de `cli/`, reaproveitando os mesmos
  casos de uso — ver [ROADMAP.md](ROADMAP.md).
