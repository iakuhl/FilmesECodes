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

## Fase 4 — API / Web 🚧 em andamento

Objetivo original: "caso haja interesse em uma interface mais rica (web)
ou em uso remoto pelos membros do clube, adicionar um adapter de API
(ex.: FastAPI) e, posteriormente, um frontend web", reaproveitando
integralmente os casos de uso das fases anteriores.

### API HTTP ✅ concluída

Decisão tomada e implementada: **FastAPI**, servida pelo novo entry point
`filmes-e-cubos-servidor` (uvicorn). A referência completa está em
[API.md](API.md); a documentação interativa, em `/api/v1/docs`.

Como na CLI, nenhuma regra de negócio nasceu aqui, e `domain/` não mudou.
O que a fase acrescentou, e por quê:

- **Composition root compartilhado** (`adapters/composicao.py`): o
  `Contexto` saiu da CLI, porque a segunda interface precisava
  exatamente do mesmo grafo. O critério de apuração do Óscar passou a
  ser escolhido por interface (`Contexto.apurar_categoria_oscar(criterio)`).
- **Convenções e consultas compartilhadas**
  (`adapters/interfaces/convencoes.py` e `consultas.py`): nome padrão da
  temporada, presença padrão da sessão, clube de uma sessão e buscas por
  id que precisam encontrar a entidade — para que todas as interfaces se
  comportem igual.
- **`adapters/interfaces/api/`**: um sub-app FastAPI montado em
  `/api/v1`, com um módulo de rotas por grupo de recursos, esquemas
  Pydantic explícitos (o domínio nunca é exposto diretamente) e um
  contrato de erro único: toda falha vira `application/problem+json`
  (RFC 9457) com um `codigo` estável. A classificação de cada erro de
  domínio em 404/409/422 é explícita, e um teste impede que um erro novo
  fique sem classificação.
- **`CriterioEscolhaInformada`** (`adapters/servicos/`): a API recebe no
  corpo da requisição qual nomeação o grupo escolheu — o mesmo papel do
  critério interativo da CLI, sem decidir o mecanismo de apuração, que
  continua em aberto.
- **`EscritasEmFila`**: middleware que enfileira as requisições que
  alteram dados, para que duas requisições simultâneas (um duplo clique)
  não furem juntas uma regra "lê, confere, grava" — ver a ADR 10.
- **`RodadaRepository.listar_por_clube`**: única mudança em
  `application/`, um método de leitura para o histórico de rodadas
  (mesmo padrão das listagens acrescentadas na Fase 2).

Testes: 95 testes da API em `tests/adapters/interfaces/api/` (app ASGI
completo contra SQLite real, um arquivo por grupo de rotas, contrato de
erro, OpenAPI e fluxo de ponta a ponta), mais os do middleware, do
servidor, das convenções e do novo critério.

Depois da API, ainda na Fase 4: a classificação de erros HTTP e a
injeção do `Contexto` viraram módulos compartilhados
(`adapters/interfaces/erros_http.py` e `contexto_http.py`), e o esquema
do banco passou a evoluir por **migrações com Alembic** (ADR 11) —
pré-requisito das mudanças de esquema da revisão de regras abaixo.

### Interface web 🚧 em andamento

Decisão confirmada pelo dono do produto: **páginas renderizadas no
servidor com Jinja2**, sem SPA nem build de JavaScript — a web é só mais
um adapter chamando os mesmos casos de uso. Um SPA ou app futuro, se
vier, consome a API que já existe.

Feito: os módulos de apoio em `adapters/interfaces/web/` — `formatacao.py`
(datas, decimais, rótulos), `mensagens.py` (avisos na sessão e textos
amigáveis para as recusas de negócio) e `formularios.py` (conversão de
campos), com testes. As dependências (`jinja2`, `python-multipart`,
`itsdangerous`) já estão no `pyproject.toml`.

Plano para o restante (ver "Como continuar"):

- `web/app.py` com `criar_web(contexto, chave_secreta=...)`: app FastAPI
  com `SessionMiddleware` (avisos), `StaticFiles` em `/estaticos` e
  handlers que transformam erros em páginas HTML. `servidor.py` passa a
  usar a web como app raiz e monta a API em `/api/v1` dentro dela.
- Ambiente Jinja próprio (`autoescape`, `StrictUndefined`, filtros de
  `formatacao.py`); `TemplateResponse(request, nome, contexto)` — a
  assinatura do Starlette 1.x.
- Padrão Post/Redirect/Get em toda ação: a rota roda o caso de uso dentro
  de `recusas_viram_avisos(request)`, registra o aviso de sucesso e
  redireciona com 303.
- Páginas, todas escopadas por clube (`/clubes/{clube_id}/...`), com
  verificação de que a entidade do caminho pertence ao clube: início
  (sem clube → criar; um clube → redireciona; vários → escolher), painel
  (rodada aberta, próxima sessão, indicar, democracia, sortear,
  encerrar), membros, filmes, histórico de rodadas, nova sessão
  (presença), sessão (avaliações e média), Óscar (edições, categorias,
  nomeações, votação e apuração).
- Testes com o `TestClient` contra o app completo e `beautifulsoup4`
  para ler o HTML; `docs/WEB.md` com a referência das páginas.

## Revisão de regras de 24/09/2026 — 🚧 falta a votação

O dono do produto respondeu às questões levantadas na Fase 4. As
decisões estão detalhadas, numeradas, em [PENDENCIAS.md](PENDENCIAS.md)
(decisões 3 a 11 e 16 a 20), com as interpretações que ainda pedem
confirmação. Em
resumo: só presentes avaliam; um filme nunca se repete no clube; uma
edição do Óscar por ano; ciclo da temporada com o estado *em votação*;
apuração por votação ponderada (2/1) com 2º turno, votação por
classificação e empate absoluto; voto alterável até a apuração; reativar
membro; data do evento; média das notas armazenada; duração do filme; e o
contrato de um módulo de histórico de sessões passadas.

Deve vir **antes** das páginas da web, que dependem dessas regras (a
votação, por exemplo, ganha telas próprias). Tudo já está implementado,
menos a votação — o desenho dela está logo abaixo.

### Desenho da votação (a implementar)

Decisões 8, 16, 18 e 20 de [PENDENCIAS.md](PENDENCIAS.md) e as
interpretações 1 a 4 e 7 a 9. É o desenho que a sessão anterior deixou
pronto; decisões técnicas podem ser revistas na implementação, desde que
registradas em PENDENCIAS.

**Domínio**

- Enumerações novas em `value_objects/status.py`: `ModoDeVotacao`
  (`DUPLA`: 1ª opção 2 pontos, 2ª opção 1 ponto; `CLASSIFICACAO`: ordena
  todas as X candidatas, com pesos X, X−1, …, 1) e `StatusTurno`
  (`ABERTO`, `APURADO`). Precisam de rótulo em `web/formatacao.py` (um
  teste confere) e de espelho `...Api` na API.
- Entidade `TurnoDeVotacao`: `id`, `categoria_id`, `numero` (1, 2, ...),
  `modo`, `candidatas` (tupla **ordenada** de `NomeacaoOscarId` — vota-se
  em nomeações, não em filmes, porque o mesmo filme pode ocupar várias),
  `status`, `pontuacao` (preenchida na apuração, para guardar o placar
  exato mesmo que um membro seja desativado depois) e `data_apuracao`.
  Métodos: `abrir_primeiro(categoria_id, candidatas)` (modo `DUPLA`);
  `conferir_escolhas(escolhas)` — turno aberto; na dupla, duas nomeações
  distintas entre as candidatas (podem ser do mesmo filme); na
  classificação, uma ordem completa das candidatas; e
  `apurar(votos, *, eleitores, data_apuracao) -> Desfecho`.
- Regras da contagem, dentro de `apurar`: `eleitores` são os membros
  ativos do clube no momento da apuração; o voto de quem não é eleitor é
  desconsiderado (decisão 18); falta de voto de algum eleitor recusa a
  apuração (decisão 8.2), listando quem falta. Desfechos (três pequenas
  dataclasses, para `match` no caso de uso): `Vitoria(nomeacao_id)` se o
  topo é único; `NovoTurno(turno)` se o topo empata entre parte das
  candidatas (novo turno `DUPLA` só com as empatadas — decisão 8.4 e
  interpretação 2) ou se todas empatam num turno `DUPLA` (novo turno
  `CLASSIFICACAO` com as mesmas — decisão 16); `EmpateAbsoluto` se todas
  empatam num turno `CLASSIFICACAO` (decisão 8.6). A sequência sempre
  termina: a cada dois turnos, no máximo, o número de candidatas cai.
- Entidade `Voto`: `id`, `turno_id`, `membro_id`, `escolhas` (tupla em
  ordem de preferência), `registrado_em` (`datetime`, via
  `RelogioService.agora`); `alterar(escolhas, registrado_em)` — o voto
  muda até a apuração (decisão 8.3).
- `Trofeu.nomeacao_vencedora_id` passa a ser opcional: `None` no empate
  absoluto, quando o troféu vai para um membro escolhido pelo grupo.
- Erros novos (cada um com status em `erros_http.py` e, se aparecer no
  uso normal, texto em `web/mensagens.py`): `VotoInvalidoError` (422);
  `TurnoJaApuradoError` (409); `VotacaoIncompletaError` (409);
  `EscolhaDoGrupoNecessariaError` (422) — substitui
  `VencedorDemocraciaNaoInformadoError`, cobrindo a vitória de um filme
  democracia e o empate absoluto; `VotacaoEmAndamentoError` (409); e a
  recusa de um membro escolhido que não é do clube (interpretação 3).

**Aplicação**

- Ports `TurnoDeVotacaoRepository` (`salvar`, `buscar_por_id`,
  `buscar_aberto_por_categoria`, `listar_por_categoria`) e
  `VotoRepository` (`salvar`, `buscar_por_turno_e_membro`,
  `listar_por_turno`), com fakes em `tests/application/fakes/`.
- `RegistrarVoto(turno_id, membro_id, escolhas)`: edição `EM_VOTACAO`
  (um `TemporadaOscar.verificar_em_votacao()` novo), turno aberto, membro
  ativo e do clube da edição; cria o voto ou substitui as escolhas.
- `ApurarCategoriaOscar(categoria_id, membro_escolhido_id=None)`, nova:
  edição `EM_VOTACAO`; apura o turno aberto da categoria; `Vitoria` →
  troféu para quem indicou a nomeação (ou para o membro escolhido, se ela
  veio de uma democracia); `EmpateAbsoluto` → troféu sem nomeação, para o
  membro escolhido; `NovoTurno` → grava o turno seguinte. Se faltar a
  escolha do grupo, falha **antes de gravar qualquer coisa** — quem chama
  repete com `membro_escolhido_id` (a contagem é determinística). Devolve
  um resultado com o turno apurado, o troféu ou o próximo turno. A
  escolha informada sem necessidade é ignorada.
- `AvancarTemporadaOscar`: ao entrar em `EM_VOTACAO`, abre o turno 1 de
  cada categoria, com todas as nomeações na ordem em que foram feitas.
- `DesativarMembro`: recusa enquanto o clube do membro tiver uma edição
  `EM_VOTACAO` (interpretação 7).
- Remover `CriterioApuracaoOscar` e as implementações
  (`cli/criterio_apuracao_interativo.py`,
  `servicos/criterio_apuracao_escolha_informada.py`, o fake e os testes),
  e `Contexto.apurar_categoria_oscar(criterio)` vira um atributo comum.

**Persistência** — revisão 0005: `turnos_votacao` (`id`, `categoria_id`,
`numero`, `modo`, `status`, `data_apuracao`; único por categoria e
número), `turno_candidatas` (`turno_id`, `posicao`, `nomeacao_id`,
`pontos` anulável até a apuração), `votos` (`id`, `turno_id`,
`membro_id`, `registrado_em`; único por turno e membro), `voto_escolhas`
(`voto_id`, `posicao`, `nomeacao_id`) e `trofeus.nomeacao_vencedora_id`
anulável (`batch_alter_table`).

**Interfaces** — antes da apuração, mostram só *quem* já votou; depois,
a pontuação de cada nomeação; as cédulas não são exibidas
(interpretação 9, questão em aberto 2).

- CLI: `oscar nomeacoes --categoria-id ID` (posição, filme, quem
  indicou), `oscar votacao CATEGORIA_ID` (turno aberto: modo, candidatas,
  quem votou e quem falta), `oscar votar --categoria-id ID --membro-id ID
  NOMEACAO_ID...` (resolve o turno aberto da categoria) e `oscar apurar
  CATEGORIA_ID [--membro-escolhido-id ID]` (placar e desfecho).
- API: `GET /oscar/categorias/{id}/turnos`, `GET /oscar/turnos/{id}`,
  `PUT /oscar/turnos/{id}/votos/{membro_id}` (corpo `{"escolhas": [...]}`;
  cria ou substitui) e `POST /oscar/categorias/{id}/apuracao` (corpo
  `{"membro_escolhido_id"?}`; devolve `{"turno", "trofeu"?,
  "proximo_turno"?}`).
- Testes: a tabela de desfechos da contagem no domínio (vitória, empate
  parcial, empate geral na dupla e na classificação, voto de desativado
  ignorado, voto faltando), os casos de uso, os repositórios, CLI e API,
  e os dois fluxos completos votando em vez de escolher.

## Fase 5 — Evolução comercial

- Suporte a múltiplos clubes (a entidade `Clube` já foi desenhada para
  isso desde a Fase 1): fechar as verificações entre clubes (dívida
  técnica 3 de [PENDENCIAS.md](PENDENCIAS.md)).
- Autenticação/autorização — **decidido**: login individual por membro,
  contas criadas por convite com código (quem cria o clube é o primeiro
  admin); administradores gerenciam clube, membros, rodadas e Óscar,
  membros comuns indicam, avaliam e votam só em nome próprio.
- Integração externa — **decidido**: TMDB, para autocompletar título,
  ano, diretor, duração, gêneros etc.; desligada até haver chave.
- Empacotamento e distribuição — **decidido**: por ora só uso local,
  mas com configuração por variáveis de ambiente e nada preso à máquina
  local, para que levar o sistema a um servidor ou à nuvem seja fácil
  quando essa decisão mudar.

## Fase 6 — Relatórios e estatísticas (futuro)

Pedido do dono do produto: o sistema deve agregar o máximo de informação
possível, para no futuro cruzar os dados em relatórios, gráficos e
estatísticas — por exemplo, tempo total de filmes assistidos no ano,
quem indica filmes mais longos, notas recebidas pelas indicações de cada
membro, notas dadas a cada filme, evolução das médias. Até lá, cada
fase deve preferir guardar dado bruto e normalizado (quem, quando,
quanto) a guardar só o resultado final.

## Como continuar

Ordem recomendada para a próxima sessão de trabalho, a partir do branch
`roadmap/fases-4-e-5`:

1. **Revisão de regras de 24/09** (decisões 3 a 11 e 16 a 20 de
   [PENDENCIAS.md](PENDENCIAS.md)), em commits pequenos, cada um com CLI,
   API, testes e documentação atualizados. Cada mudança de esquema ganha
   a sua própria revisão do Alembic, no commit da regra que a pede:
   1. ✅ duração do filme (revisão 0002: `filmes.duracao_minutos`);
      reativar membro; data do evento do Óscar;
   2. ✅ só presentes avaliam (`AvaliarFilme` passa a deduzir o clube da
      própria sessão, e o `--clube-id` da avaliação sai da CLI); média
      guardada como fração — soma e quantidade das notas na sessão
      (revisão 0003, que calcula as das sessões já avaliadas) —,
      recalculada a cada avaliação e exibida em estrelas;
   3. ✅ filme nunca se repete no clube (`IndicarFilme` e
      `AdicionarFilmeDemocracia`; novo `IndicacaoRepository.listar_por_filme`)
      e `IndicarFilmeParaCategoria` restrito às sessões do próprio clube;
   4. ✅ uma edição por ano; número de nomeações por categoria (revisão
      0004); ciclo da temporada com `EM_VOTACAO` e o caso de uso de
      avanço, restringindo cada ação à sua fase;
   5. **próximo passo:** votação, conforme o "Desenho da votação"
      acima (revisão 0005: turnos, candidatas, votos e escolhas;
      `trofeus.nomeacao_vencedora_id` anulável para o empate absoluto):
      entidades `TurnoDeVotacao` e `Voto`, contagem como regra do domínio,
      `RegistrarVoto` e a nova `ApurarCategoriaOscar`; desativar membro
      bloqueado durante a votação; remoção de `CriterioApuracaoOscar`.
      Grande o bastante para pedir uma sessão só para ela;
   6. ✅ contrato do módulo de histórico (só ports e estruturas de dados).
2. **Páginas da interface web** sobre o domínio já revisado (plano na
   seção da Fase 4), fechando a Fase 4.
3. **Fase 5**: verificações entre clubes, login com convites e
   permissões, TMDB e configuração por ambiente.

## Pontos explicitamente em aberto

| Decisão | Status | Onde foi/será resolvida |
|---|---|---|
| Implementação concreta de persistência | ✅ Resolvida: SQLite via SQLAlchemy Core | Fase 2 |
| Primeira interface de usuário | ✅ Resolvida: CLI com Typer | Fase 3 |
| Tecnologia da API | ✅ Resolvida: FastAPI, erros RFC 9457 | Fase 4 |
| Tecnologia da interface web | ✅ Resolvida: páginas renderizadas no servidor (Jinja2) | Fase 4 |
| Evolução do esquema do banco | ✅ Resolvida: migrações com Alembic | Fase 4 |
| Mecanismo de apuração de categorias do Óscar (votação vs. critério fixo) | ✅ Decidida em 24/09/2026: votação ponderada (2/1), com 2º turno, classificação e empate absoluto — a implementar | Hoje a CLI e a API ainda delegam a escolha a quem opera (port `CriterioApuracaoOscar`); a votação substitui esse port. Ver [PENDENCIAS.md](PENDENCIAS.md), decisão 8. |
| Módulo de histórico de sessões passadas | Contrato criado (`LeitorDeHistorico`); implementação em aberto | Ver [PENDENCIAS.md](PENDENCIAS.md), decisão 3 e questão em aberto 1. |
