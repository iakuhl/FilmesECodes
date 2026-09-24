# Arquitetura

## Estilo arquitetural

O projeto adota **Arquitetura Hexagonal (Ports & Adapters)**, também
descrita como uma variante de Clean Architecture. A motivação é direta a
partir das decisões já tomadas para esta fase:

- A **interface** do sistema (CLI, API, web) ainda não foi decidida.
- A **persistência** concreta (SQLite, arquivos, outro banco) ainda não
  foi decidida.

Para que essas duas decisões possam continuar em aberto sem bloquear o
desenvolvimento do domínio, o núcleo do sistema (entidades e regras de
negócio) precisa ser completamente independente de ambas. Isso só é
possível isolando o núcleo detrás de contratos (**ports**) e empurrando
toda decisão concreta para implementações plugáveis (**adapters**) que
são escritas depois, sem tocar no núcleo.

## Camadas

```
┌─────────────────────────────────────────────────────────┐
│  Adapters (futuro)                                       │
│  - Interfaces: CLI / API / Web                            │
│  - Persistência: SQLite / JSON / outro                    │
│  - Serviços externos: provedor de dados de filmes, etc.   │
└───────────────────────┬───────────────────────────────────┘
                         │ implementam
┌───────────────────────▼───────────────────────────────────┐
│  Application                                              │
│  - Casos de uso (orquestram o domínio)                    │
│  - Ports: contratos que os casos de uso precisam          │
│    (repositórios, sorteador, relógio)                     │
└───────────────────────┬───────────────────────────────────┘
                         │ usa
┌───────────────────────▼───────────────────────────────────┐
│  Domain                                                    │
│  - Entidades e Value Objects                               │
│  - Regras de negócio e invariantes                         │
│  - Exceções de domínio                                     │
│  (nenhuma dependência de outras camadas)                   │
└─────────────────────────────────────────────────────────────┘
```

Regra de dependência: as camadas externas conhecem e dependem das
internas; o inverso nunca ocorre. `domain` não importa nada de
`application` ou `adapters`. `application` não importa nada de
`adapters`. Isso é o que permite que persistência e interface fiquem
indefinidas sem travar o desenvolvimento do núcleo.

### Domain

Contém as entidades (`Membro`, `Filme`, `Rodada`, `Indicacao`, `Sorteio`,
`SessaoExibicao`, `Avaliacao`, `TemporadaOscar`, `CategoriaOscar`,
`Trofeu`, entre outras — ver [DOMINIO.md](DOMINIO.md)) e as regras de
negócio que essas entidades garantem sobre si mesmas. Não conhece banco
de dados, não conhece interface, não conhece formato de I/O. É a camada
com maior valor de portfólio: é onde a modelagem orientada a objetos é
avaliada.

### Application

Contém os **casos de uso** (ver [CASOS_DE_USO.md](CASOS_DE_USO.md)), que
orquestram entidades de domínio para realizar uma ação completa (ex.:
"realizar sorteio da rodada"). Um caso de uso depende apenas de **ports**
— contratos abstratos — nunca de uma implementação concreta.

Também define os **ports** que a camada de domínio/aplicação precisa de
fora:

- Repositórios, um por entidade (`ClubeRepository`, `MembroRepository`,
  `FilmeRepository`, `RodadaRepository`, `IndicacaoRepository`,
  `SorteioRepository`, `SessaoRepository`, `AvaliacaoRepository`,
  `TemporadaOscarRepository`, `CategoriaOscarRepository`,
  `NomeacaoOscarRepository`, `TrofeuRepository`): contratos de
  persistência, sem implementação concreta nesta fase. `Clube` tem seu
  próprio repositório porque `Membro`, `Rodada` e `TemporadaOscar` se
  referenciam a ele por `clube_id`, não por composição direta (ver
  [DOMINIO.md](DOMINIO.md)).
- `SorteadorService`: contrato para o mecanismo de sorteio (permite, por
  exemplo, trocar um sorteio pseudoaleatório por um determinístico em
  testes).
- `RelogioService` (clock): contrato para obter a data/hora atual, para
  que casos de uso sejam testáveis sem depender do relógio do sistema.
- `CriterioApuracaoOscar`: contrato para o critério que decide o vencedor
  de uma categoria do Óscar — existe porque esse mecanismo (votação,
  média de notas, etc.) ainda não foi decidido para o produto; o caso de
  uso `ApurarCategoriaOscar` não fica acoplado a essa decisão em aberto.

### Adapters

Implementações concretas dos ports. Duas categorias já existem (Fase 2):

- **Persistência** (`adapters/persistence/sqlite/`): um repositório
  SQLite por entidade, implementado com **SQLAlchemy Core** (tabelas
  explícitas via `Table`/`MetaData`, não o ORM declarativo). A escolha
  por Core em vez do ORM é deliberada: as entidades de domínio já são
  classes ricas, com construtores que validam invariantes e métodos de
  mutação nomeados pela regra de negócio — moldá-las para um mapeamento
  ORM declarativo (que espera atributos simples e mutáveis) quebraria
  esse encapsulamento. Cada repositório converte manualmente entre
  entidade e linha de tabela (funções `_para_linha`/`_para_entidade`).
- **Serviços de infraestrutura** (`adapters/servicos/`):
  implementações reais de `RelogioService` e `SorteadorService`.

Uma terceira categoria ainda não existe: **interface** (ex.: um comando
de CLI que chama um caso de uso), planejada para a Fase 3 (ver
[ROADMAP.md](ROADMAP.md) e o README para o plano detalhado).

## Registro de decisões arquiteturais (ADR resumido)

| # | Decisão | Status | Justificativa |
|---|---------|--------|----------------|
| 1 | Arquitetura Hexagonal (Ports & Adapters) | Adotada | Permite deixar persistência e interface indefinidas sem bloquear o domínio. |
| 2 | Persistência via padrão Repository, concretizada com **SQLite + SQLAlchemy Core** | Adotada (Fase 2) | Banco leve, embutido em arquivo, sem servidor externo; Core (não ORM) preserva o encapsulamento das entidades. |
| 3 | Interface de usuário: **CLI com Typer** | Decidida, não implementada (Fase 3) | Simplicidade de implementação, sem infraestrutura extra; `typer` já está em `pyproject.toml`. |
| 4 | Contratos via `typing.Protocol` (ou `abc.ABC` quando fizer sentido) | Adotada | Contratos explícitos e verificáveis por type checking (`mypy`), sem herança forçada. |
| 5 | Injeção de dependência manual (sem framework de DI) | Adotada | Projeto pequeno; um container de DI seria complexidade prematura nesta fase. |
| 6 | `Clube` como entidade de primeira classe, com configurações | Adotada | Viabiliza evolução para suportar múltiplos clubes em uma versão comercial futura, sem redesenhar o domínio. |

## Princípios de orientação a objetos aplicados

- **Encapsulamento**: entidades expõem comportamento que protege seus
  próprios invariantes (ex.: uma `Avaliacao` só aceita ser criada com uma
  nota válida; ninguém de fora manipula seu estado interno diretamente
  para colocá-la em um estado inválido).
- **Contratos explícitos (interfaces/protocolos)**: toda dependência de
  uma camada interna sobre algo externo é expressa como um `Protocol`
  (ou ABC) definido na própria camada interna — quem implementa é quem
  se adapta ao contrato, não o contrário.
- **Inversão de dependência**: `application` define os ports que precisa;
  futuros `adapters` implementam esses ports. O núcleo nunca importa uma
  implementação concreta.
- **Composição sobre herança**: preferir compor entidades e serviços a
  criar hierarquias profundas de herança no domínio.
- **Coesão e responsabilidade única**: cada entidade e cada caso de uso
  tem uma razão de existir e mudar; regras de sorteio, por exemplo, vivem
  em um serviço de domínio dedicado, não espalhadas em `Rodada` ou em um
  caso de uso genérico.
