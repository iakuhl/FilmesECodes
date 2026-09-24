# FilmesECodes

Software de gestão para o clube de cinema **Filmes e Cubos**.

## O clube

O "Filmes e Cubos" é um clube de cinema com 5 membros fixos que assistem a
um filme por semana. Toda semana cada membro indica um filme; um dos
filmes indicados é sorteado para a sessão daquela semana. O ciclo (uma
"rodada") só se encerra quando as 5 indicações da rodada tiverem sido
sorteadas e assistidas — aí uma nova rodada de indicações começa.

Depois de cada sessão, todos os membros dão uma nota ao filme assistido,
em uma escala de 0,5 a 5 estrelas. Essas notas são guardadas ao longo do
ano para alimentar o **"Óscar do Filmes e Cubos"**: um evento anual com
categorias de premiação, algumas fixas e outras variáveis de ano para
ano (e via de regra bem irreverentes — "Melhor veículo", "Pior criança",
"Personagem mais detestável" etc.). O troféu de cada categoria é entregue
ao membro que indicou o filme premiado, não a quem "atua" na categoria.

O nome do clube vem de uma brincadeira: durante a pandemia o grupo jogava
um jogo de blocos (cubos) online, até migrar para sessões de cinema — e
"Filmes e Cubos" pegou. Todas as redes sociais, grupos e nomes do clube
remetem a essa origem (por exemplo, este próprio projeto, "FilmesECodes").

## O que é este projeto

Este repositório é o software de apoio ao clube: cadastro de membros e
filmes, controle de rodadas e sorteios, registro de sessões e notas, e
apuração do Óscar anual. É um projeto pessoal, mas conduzido com rigor
profissional — serve como peça de portfólio e é desenhado para,
eventualmente, evoluir para uma versão comercializável (multi-clube).

**Status atual:** Fases 1 e 2 do roadmap **concluídas e testadas**; Fase 3
**não iniciada**. Ver [docs/ROADMAP.md](docs/ROADMAP.md) para o histórico
completo e a seção **"Como continuar a Fase 3"** abaixo para retomar o
trabalho em uma nova sessão.

- ✅ **Fase 1** — núcleo de domínio (12 entidades, 6 value objects) e
  casos de uso (agora 15, após a Fase 2) em `src/filmes_e_cubos/domain/`
  e `src/filmes_e_cubos/application/`.
- ✅ **Fase 2** — persistência SQLite via SQLAlchemy Core, em
  `src/filmes_e_cubos/adapters/persistence/sqlite/` (12 repositórios) e
  `src/filmes_e_cubos/adapters/servicos/` (relógio e sorteador reais).
- ⏳ **Fase 3** — CLI (Typer). Dependência já instalada e entry point já
  registrado em `pyproject.toml`, mas **o código da CLI ainda não
  existe**. Rodar `filmes-e-cubos` agora falha.

Toda a suíte de testes está verde: `uv run pytest` (139 testes),
`uv run mypy src` (limpo, 87 arquivos) e `uv run ruff check .` (limpo).

## Desenvolvimento

O projeto é gerenciado com [uv](https://docs.astral.sh/uv/).

```bash
uv sync --dev        # instala dependências (runtime + dev)
uv run pytest        # roda a suíte de testes
uv run mypy src      # checagem estática de tipos
uv run ruff check .  # lint
```

## Como continuar a Fase 3 (CLI)

Contexto para retomar em uma nova sessão: as Fases 1 e 2 estão prontas,
testadas e commitadas. Falta só a interface de linha de comando. Segue o
plano que estava em andamento quando a sessão anterior foi interrompida
(por limite de contexto) — nenhuma linha de código da CLI foi escrita
ainda, então não há nada para conferir/consertar, só para construir.

### O que já está pronto para a CLI consumir

- **15 casos de uso** em `src/filmes_e_cubos/application/use_cases/`,
  cada um com um método `executar(...)` e suas próprias exceções de
  domínio (ver [docs/CASOS_DE_USO.md](docs/CASOS_DE_USO.md) para a lista
  completa e as regras de cada um): `CriarClube`, `CadastrarMembro`,
  `DesativarMembro`, `CadastrarFilme`, `AbrirNovaRodada`, `IndicarFilme`,
  `AdicionarFilmeDemocracia`, `RealizarSorteio`, `EncerrarRodada`,
  `RegistrarSessaoExibicao`, `AvaliarFilme`, `AbrirTemporadaOscar`,
  `DefinirCategoriaOscar`, `IndicarFilmeParaCategoria`,
  `ApurarCategoriaOscar`.
- **12 repositórios SQLite** prontos em
  `src/filmes_e_cubos/adapters/persistence/sqlite/` (um arquivo por
  entidade) e `criar_engine(caminho_banco)` em `fabrica_engine.py` para
  obter um `Engine` do SQLAlchemy a partir de um caminho de arquivo.
- **Serviços reais** em `src/filmes_e_cubos/adapters/servicos/`:
  `RelogioSistema` (implementa `RelogioService`) e `SorteadorAleatorio`
  (implementa `SorteadorService`).
- **Falta implementar**: `CriterioApuracaoOscar` (port em
  `application/ports/criterio_apuracao_oscar.py`) não tem nenhuma
  implementação concreta ainda — nem os fakes de teste resolvem isso
  automaticamente para a CLI real.

### Estrutura sugerida (ainda não criada)

```
src/filmes_e_cubos/adapters/interfaces/
├── __init__.py
└── cli/
    ├── __init__.py
    ├── main.py                       # cria o Typer() `app`, monta os sub-apps
    ├── contexto.py                   # composition root: monta engine + repos + use cases
    ├── criterio_apuracao_interativo.py  # CriterioApuracaoOscar via prompt ao usuário
    ├── comandos_clube.py             # criar, listar
    ├── comandos_membro.py            # cadastrar, desativar, listar
    ├── comandos_filme.py             # cadastrar, listar
    ├── comandos_rodada.py            # abrir, encerrar, status
    ├── comandos_indicacao.py         # indicar, democracia, sortear, assistida
    ├── comandos_avaliacao.py         # registrar (nota opcional = dorminhoco)
    └── comandos_oscar.py             # temporada-abrir, categoria-definir, nomear, apurar
```

O `pyproject.toml` já aponta o entry point `filmes-e-cubos` para
`filmes_e_cubos.adapters.interfaces.cli.main:app` — depois de criar
`main.py` com um objeto `app` (Typer), `uv run filmes-e-cubos --help`
deve funcionar.

### Decisões de design recomendadas (dentro da liberdade já dada pelo usuário)

1. **Caminho do banco**: opção global `--db-path` (ou variável de
   ambiente `FILMES_E_CUBOS_DB`), com default tipo `filmes_e_cubos.db`
   no diretório atual. Construir o `Engine` a cada invocação de comando
   a partir desse caminho (SQLite é um arquivo, não precisa manter
   conexão viva entre comandos).
2. **Resolver o clube automaticamente**: como o uso real (Filmes e
   Cubos) é de um único clube, comandos que precisam de `clube_id`
   podem, se não informado via `--clube-id`, usar
   `ClubeRepository.listar_todos()` e escolher automaticamente quando
   houver exatamente um; senão, pedir para especificar. Mesma ideia para
   "rodada aberta do clube" via `RodadaRepository.buscar_aberta_por_clube`.
3. **`CriterioApuracaoOscar` interativo**: como o mecanismo de apuração
   continua em aberto no domínio (ver ROADMAP.md), a implementação mais
   honesta para uma CLI é perguntar ao usuário — listar as nomeações de
   `NomeacaoOscar` (com o filme de cada uma) e pedir para escolher a
   vencedora. Não é um hack: o port existe exatamente para isso.
4. **`RegistrarSessaoExibicao` / membros presentes**: aceitar
   `--presente <membro_id>` repetível; se nenhum for passado, um default
   razoável é assumir todos os membros ativos do clube como presentes
   (`MembroRepository.listar_ativos_por_clube`).
5. **`AvaliarFilme` sem nota = dorminhoco**: já é assim no caso de uso
   (`nota` é opcional); a CLI só precisa tornar `--nota` opcional
   também.

### Testes a escrever

- `tests/adapters/interfaces/cli/` — usar `typer.testing.CliRunner` (ou
  `click.testing.CliRunner`) contra um banco SQLite temporário
  (`tmp_path`), cobrindo pelo menos um fluxo de ponta a ponta completo:
  criar clube → cadastrar membros → cadastrar filme → abrir rodada →
  indicar → sortear ou marcar assistida direto → registrar sessão →
  avaliar (com nota e sem nota) → encerrar rodada → abrir temporada do
  Óscar → definir categoria → nomear → apurar.
- Seguir o mesmo padrão de modularidade já usado: um arquivo de teste
  por módulo de comandos.

### Verificação ao terminar

```bash
uv run pytest -q       # toda a suíte, incluindo os testes novos da CLI
uv run mypy src        # sem erros
uv run ruff check .    # sem violações
uv run filmes-e-cubos --help   # a CLI real deve subir
```

Depois de tudo verde, atualizar `docs/ROADMAP.md` (marcar Fase 3 como
concluída), `docs/ESTRUTURA_PROJETO.md` (preencher `adapters/interfaces/`
na árvore) e esta seção do README (pode ser removida ou reduzida a uma
nota curta, já que a Fase 3 estará concluída).

## Documentação

- [docs/ARQUITETURA.md](docs/ARQUITETURA.md) — estilo arquitetural, camadas
  e decisões de arquitetura.
- [docs/DOMINIO.md](docs/DOMINIO.md) — entidades, regras de negócio e
  invariantes do domínio.
- [docs/CASOS_DE_USO.md](docs/CASOS_DE_USO.md) — casos de uso da aplicação.
- [docs/ESTRUTURA_PROJETO.md](docs/ESTRUTURA_PROJETO.md) — estrutura de
  pastas planejada e ferramentas do projeto.
- [docs/ROADMAP.md](docs/ROADMAP.md) — fases de desenvolvimento previstas.
- [docs/GLOSSARIO.md](docs/GLOSSARIO.md) — termos do domínio do clube.
