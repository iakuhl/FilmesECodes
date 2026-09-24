# Arquitetura

## Estilo arquitetural

O projeto adota **Arquitetura Hexagonal (Ports & Adapters)**, também
descrita como uma variante de Clean Architecture. A motivação original
foi poder construir o núcleo antes de duas decisões que ainda estavam em
aberto: qual seria a **interface** do sistema (CLI, API, web) e qual
seria a **persistência** concreta.

Para que essas decisões pudessem esperar sem bloquear o desenvolvimento
do domínio, o núcleo (entidades e regras de negócio) precisava ser
completamente independente de ambas — o que se consegue isolando-o detrás
de contratos (**ports**) e empurrando toda decisão concreta para
implementações plugáveis (**adapters**) escritas depois, sem tocar no
núcleo.

A aposta se confirmou: as duas decisões foram tomadas depois (SQLite na
Fase 2, CLI na Fase 3) e nenhuma delas exigiu uma única alteração em
`domain/` ou `application/`. Uma terceira continua em aberto — o critério
de apuração do Óscar — e segue viável exatamente pelo mesmo mecanismo.

## Camadas

```
┌─────────────────────────────────────────────────────────┐
│  Adapters                                                 │
│  - Interfaces: CLI (Typer) ✅ | API / Web (futuro)         │
│  - Persistência: SQLite + SQLAlchemy Core ✅               │
│  - Serviços: relógio ✅, sorteador ✅, critério do Óscar ✅ │
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
  persistência, implementados na Fase 2. `Clube` tem seu
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

Implementações concretas dos ports. Três categorias existem:

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
- **Interface** (`adapters/interfaces/cli/`): a CLI em Typer (Fase 3 —
  ver [CLI.md](CLI.md)). Traduz argumentos de terminal em chamadas aos
  casos de uso e formata o resultado. Inclui também uma implementação de
  `CriterioApuracaoOscar` (`CriterioApuracaoInterativo`), que pergunta ao
  usuário quem venceu a categoria: como o mecanismo de apuração continua
  em aberto no produto, a resposta mais honesta é delegá-la a quem opera,
  e o port existe exatamente para permitir isso sem contaminar o domínio.

#### Composition root

`adapters/composicao.py` é o **composition root** do sistema: o único
módulo que conhece, ao mesmo tempo, todos os ports e todas as suas
implementações concretas. É onde a decisão "SQLite" e a decisão "relógio
do sistema" são efetivamente tomadas. Todo o resto do código — domínio,
casos de uso e até as próprias interfaces — enxerga apenas contratos.

Nasceu dentro da CLI (`adapters/interfaces/cli/contexto.py`, Fase 3) e
foi promovido a módulo próprio no início da Fase 4, quando uma segunda
interface passou a precisar exatamente do mesmo grafo de dependências.
Cada interface continua dona apenas do que é dela: a CLI, por exemplo,
decide *quando* montar o grafo (só quando um comando toca dados) e qual
critério de apuração do Óscar usar.

Uma consequência prática e deliberada: os repositórios são anotados ali
com o tipo do *port*, não com o da classe concreta. Assim o `mypy` checa,
naquele ponto de montagem, que cada adapter realmente satisfaz o
`Protocol` que diz implementar — a verificação estrutural que justifica a
decisão nº 4 da tabela abaixo.

O critério de apuração do Óscar é a única dependência que o composition
root **não** escolhe: como o mecanismo continua em aberto no produto,
cada interface o delega a quem opera do seu jeito (a CLI pergunta no
terminal; interfaces HTTP recebem a escolha na requisição). Por isso
`ApurarCategoriaOscar` é montado sob demanda, por
`Contexto.apurar_categoria_oscar(criterio)`.

Conveniências que várias interfaces compartilham — o nome padrão de uma
edição do Óscar, a presença padrão de uma sessão, o clube a que uma
sessão pertence — ficam em `adapters/interfaces/convencoes.py`, para que
todas se comportem igual. Não são regras de negócio: os casos de uso
continuam recebendo tudo explicitamente.

## Registro de decisões arquiteturais (ADR resumido)

| # | Decisão | Status | Justificativa |
|---|---------|--------|----------------|
| 1 | Arquitetura Hexagonal (Ports & Adapters) | Adotada | Permite deixar persistência e interface indefinidas sem bloquear o domínio. |
| 2 | Persistência via padrão Repository, concretizada com **SQLite + SQLAlchemy Core** | Adotada (Fase 2) | Banco leve, embutido em arquivo, sem servidor externo; Core (não ORM) preserva o encapsulamento das entidades. |
| 3 | Interface de usuário: **CLI com Typer** | Adotada (Fase 3) | Simplicidade de implementação, sem infraestrutura extra. Ver [CLI.md](CLI.md). |
| 4 | Contratos via `typing.Protocol` (ou `abc.ABC` quando fizer sentido) | Adotada | Contratos explícitos e verificáveis por type checking (`mypy`), sem herança forçada. |
| 5 | Injeção de dependência manual (sem framework de DI) | Adotada | Projeto pequeno; um container de DI seria complexidade prematura nesta fase. |
| 6 | `Clube` como entidade de primeira classe, com configurações | Adotada | Viabiliza evolução para suportar múltiplos clubes em uma versão comercial futura, sem redesenhar o domínio. |
| 7 | Listagens de leitura da interface vão direto ao repositório, sem caso de uso | Adotada (Fase 3) | Um caso de uso que só repassa uma chamada de repositório não acrescenta regra nenhuma — seria indireção vazia. Ações que mudam estado, essas sim, passam obrigatoriamente por um caso de uso. |
| 8 | Composition root único, em `adapters/composicao.py` (na Fase 3, em `adapters/interfaces/cli/contexto.py`) | Adotada (Fase 3; movido na Fase 4) | Concentra em um lugar toda a amarração port↔implementação, e transforma a checagem de tipos nesse ponto em verificação de conformidade dos adapters. Compartilhado por todas as interfaces. |

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
