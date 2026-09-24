# Estrutura do Projeto

Este documento descreve a estrutura de pastas do projeto, alinhada com a
arquitetura definida em [ARQUITETURA.md](ARQUITETURA.md). A partir da
Fase 1 do roadmap (ver [ROADMAP.md](ROADMAP.md)), `domain/` e
`application/` (com suas subpastas e os testes correspondentes) já
existem e estão implementados; `adapters/` continua reservada e vazia,
pois persistência e interface concretas ainda são decisões em aberto.

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
│       │   ├── use_cases/             # um módulo por caso de uso
│       │   └── ports/                 # Protocols: repositórios, SorteadorService,
│       │                              # RelogioService, CriterioApuracaoOscar
│       └── adapters/                  # reservado; ainda vazio (Fase 2/3)
│           ├── persistence/           # futuro: sqlite, json, memory...
│           └── interfaces/            # futuro: cli, api, web...
└── tests/
    ├── conftest.py
    ├── domain/
    │   ├── value_objects/
    │   └── entities/
    └── application/
        ├── fakes/                     # implementações in-memory dos ports
        └── use_cases/
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
- **`src/filmes_e_cubos/adapters/`**: reservado para as implementações
  concretas (persistência e interface) que serão decididas e escritas em
  fases futuras (ver [ROADMAP.md](ROADMAP.md)). Fica vazio (ou nem é
  criado) até essa decisão.
- **`tests/`**: espelha a estrutura de `src/`, com testes de domínio
  (regras de negócio isoladas) e de aplicação (casos de uso com
  implementações de teste/fake dos ports).

## Ferramentas e convenções previstas

| Ferramenta | Uso |
|---|---|
| [`uv`](https://docs.astral.sh/uv/) | Gerenciamento de ambiente virtual e dependências, substituindo pip/venv/poetry. |
| `pytest` | Framework de testes. |
| `ruff` | Lint e formatação (substitui flake8/black/isort). |
| `mypy` | Verificação estática de tipos — importante para validar os contratos (`Protocol`) entre camadas. |

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

- Escolha e implementação do primeiro adapter de persistência.
- Escolha e implementação da primeira interface (provavelmente CLI, por
  simplicidade — ver [ROADMAP.md](ROADMAP.md)).
