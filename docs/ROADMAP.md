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

## Fase 3 — Primeira interface de usuário — ⏳ NÃO iniciada

Decisão tomada (ainda não implementada): **CLI**, usando
[Typer](https://typer.tiangolo.com/) (já adicionado a `pyproject.toml`
como dependência, junto com `sqlalchemy`). O entry point
`filmes-e-cubos` já está registrado em `pyproject.toml`
(`[project.scripts]`), apontando para
`filmes_e_cubos.adapters.interfaces.cli.main:app` — **esse módulo ainda
não existe**, então rodar a CLI agora falhará até a Fase 3 ser
implementada. Ver a seção "Como continuar a Fase 3" no
[README.md](../README.md) para o plano detalhado do que falta: estrutura
de pastas sugerida, lista de comandos por caso de uso (incluindo os 13
casos de uso já existentes + os 2 novos desta fase), a decisão pendente
de como implementar `CriterioApuracaoOscar` para a CLI (sugestão:
critério interativo, que pergunta ao usuário quem venceu) e o esquema de
composição (engine → repositórios → casos de uso → comandos).
A interface deve apenas traduzir entrada/saída para chamadas aos casos
de uso já existentes — nenhuma regra de negócio nova deve nascer aqui.

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
| Primeira interface de usuário | ⏳ Decidida (CLI/Typer), não implementada | Fase 3 |
| Mecanismo de apuração de categorias do Óscar (votação vs. critério fixo) | Continua em aberto — port `CriterioApuracaoOscar` plugável | Sugestão: critério interativo na CLI (Fase 3) |
