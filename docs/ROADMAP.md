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
campos) — e a base das páginas: `web/app.py` (`criar_web`, o app raiz,
com `StaticFiles` em `/estaticos` e páginas de erro), `renderizacao.py`
(ambiente Jinja com `autoescape`, `StrictUndefined` e os filtros de
`formatacao.py`), o padrão Post/Redirect/Get, o visual (`estilo.css`), a
entrada com a senha do clube e as páginas de início e do painel. A
referência das páginas está em [WEB.md](WEB.md).

Plano para o restante (ver "Como continuar"):

- Páginas, todas escopadas por clube (`/clubes/{clube_id}/...`), com
  verificação de que a entidade do caminho pertence ao clube: início
  (sem clube → criar; um clube → redireciona; vários → escolher), painel
  (rodada aberta, próxima sessão, indicar, democracia, sortear,
  encerrar), membros (o botão de reativar só aparece para quem está
  inativo — decisão 33), filmes, histórico de rodadas, nova sessão
  (presença), sessão (avaliações e média), Óscar (edições, categorias,
  nomeações, cédula e confirmação, envio do placar e registro dos
  vencedores).
- Testes com o `TestClient` contra o app completo e `beautifulsoup4`
  para ler o HTML; `docs/WEB.md` com a referência das páginas.

### Publicação na Vercel 🚧 em andamento

Decisões 34 a 37 de [PENDENCIAS.md](PENDENCIAS.md): a web vai ao ar na
Vercel, a partir do repositório do GitHub, com o banco num Postgres da
Neon e protegida por uma senha única do clube até o login da Fase 5.

Feito: a persistência ficou portável entre SQLite e Postgres (ADR 12;
revisão 0006, a ordem de criação), o `app.py` da raiz é a entrada da
Vercel, `DATABASE_URL` configura o banco do servidor e da CLI, e os
testes da API rodam também contra um Postgres; a definição de CI que faz
isso a cada push está pronta em `docs/ci/testes.yml`, esperando ser
ligada (pendência 4). Os passos para publicar estão no README.

## Revisão de regras de 24 e 25/09/2026 — 🚧 falta a votação

O dono do produto respondeu às questões levantadas na Fase 4. As
decisões estão detalhadas, numeradas, em [PENDENCIAS.md](PENDENCIAS.md)
(decisões 3 a 11 e 16 a 33), com as interpretações que ainda pedem
confirmação. Em resumo: só presentes avaliam; um filme nunca se repete
no clube; uma edição do Óscar por ano; ciclo da temporada com o estado
*em votação*; votação ponderada (2/1) com eleitores definidos, cédula
confirmada e desempates automáticos, cujo placar vai por e-mail para quem
monta a cerimônia; vencedores registrados depois do evento; reativar
membro; data do evento; média das notas armazenada; duração do filme; e o
contrato de um módulo de histórico de sessões passadas.

Deve vir **antes** das páginas da web, que dependem dessas regras (a
votação, por exemplo, ganha telas próprias). Tudo já está implementado,
menos parte da votação — o desenho dela está logo abaixo.

### Desenho da votação (em implementação: etapa (a) pronta)

Decisões 8, 16, 20 e 21 a 29 de [PENDENCIAS.md](PENDENCIAS.md) e as
interpretações 1 a 3 e 12 a 15. O sistema recolhe os votos e desfaz os
empates, mas não mostra resultado a ninguém: o placar só sai por e-mail,
para quem monta a cerimônia, e o vencedor de cada categoria é registrado
por quem administra depois do evento. Decisões técnicas podem ser revistas
na implementação, desde que registradas em PENDENCIAS.

O fluxo, dentro da fase *em votação* da edição:

1. Ao entrar na fase, a **votação** começa: os eleitores são os membros
   ativos do clube naquele momento, e cada categoria abre o 1º turno com
   todas as suas nomeações.
2. Cada eleitor preenche a sua **cédula** do turno — em cada categoria, a
   1ª e a 2ª opção (ou, num turno de classificação, a ordem completa) —,
   altera o que quiser e a **confirma**. Confirmada, não muda mais.
3. A confirmação do último eleitor **encerra o turno**: o sistema apura
   cada categoria sem mostrar nada. Topo empatado abre, na categoria, um
   turno seguinte só com as empatadas (dupla; ou classificação, se todas
   empataram numa dupla); as demais categorias estão decididas — por
   vitória ou por empate absoluto. Se algum turno novo foi aberto, os
   eleitores voltam ao passo 2; se não, a votação termina.
4. Terminada a votação, quem administra **envia o placar** a um e-mail,
   quantas vezes precisar, até a edição ser encerrada.
5. Depois da cerimônia, quem administra **registra o vencedor** de cada
   categoria; com todas registradas, a edição pode avançar a *apurada*.

**Domínio**

- `ModoDeVotacao` em `value_objects/status.py`: `DUPLA` (1ª opção 2
  pontos, 2ª opção 1 ponto) e `CLASSIFICACAO` (ordena as X candidatas,
  com pesos X, X−1, …, 1). Precisa de rótulo em `web/formatacao.py` (um
  teste confere) e de espelho `ModoDeVotacaoApi` na API.
- `VotacaoOscar`: `id`, `temporada_id`, `eleitores` (conjunto fixo de
  `MembroId`), `iniciada_em`, `turno_atual` (1, 2, ...) e `encerrada_em`.
  `iniciar(temporada_id, eleitores, momento)` recusa uma lista vazia;
  `verificar_eleitor`, `verificar_aberta`, `pendentes(confirmados)`,
  `abrir_turno_seguinte()` e `encerrar(momento)`.
- `TurnoDeVotacao` — o turno de uma categoria: `id`, `categoria_id`,
  `numero` (o turno da votação em que acontece), `modo`, `candidatas`
  (tupla **ordenada** de `NomeacaoOscarId` — vota-se em nomeações) e,
  depois de apurado, `pontuacao` (os pontos de cada candidata, na mesma
  ordem) e `apurado_em`. `abrir_primeiro(categoria_id, candidatas)` (modo
  `DUPLA`); `conferir_escolhas(escolhas)` — na dupla, duas nomeações
  distintas entre as candidatas (podem ser do mesmo filme); na
  classificação, uma ordem completa; `apurar(escolhas_das_cedulas,
  momento) -> TurnoDeVotacao | None` devolve o turno seguinte quando o
  topo empata (parcial → dupla com as empatadas, decisão 8.4 e
  interpretação 2; total numa dupla → classificação com as mesmas,
  decisão 16) e `None` quando a categoria se decidiu (topo único, ou
  empate total numa classificação: empate absoluto, decisão 8.6). A
  sequência sempre termina: a cada dois turnos, no máximo, o número de
  candidatas cai. Leituras para o placar: `lideres` e `empate_absoluto`.
- `Cedula` — as escolhas de um eleitor num turno: `id`, `votacao_id`,
  `turno`, `membro_id`, `escolhas` (por categoria, em ordem de
  preferência) e `confirmada_em`. `votar(categoria_id, escolhas)` e
  `confirmar(categorias_do_turno, momento)`, que exige voto em todas;
  depois de confirmada, as duas recusam.
- `TemporadaOscar.verificar_em_votacao()`.
- Erros novos, cada um com status em `erros_http.py` e, se aparecer no
  uso normal, texto em `web/mensagens.py`: `VotoInvalidoError` (422),
  `CedulaConfirmadaError` (409), `CedulaIncompletaError` (409),
  `MembroForaDaVotacaoError` (409), `CategoriaForaDoTurnoError` (409),
  `VotacaoEncerradaError` (409) e `VotacaoEmAndamentoError` (409). Ir à
  votação sem nenhum membro ativo é um `TemporadaIncompletaError`.

**Aplicação**

- Ports `VotacaoOscarRepository` (`salvar`, `buscar_por_temporada`),
  `TurnoDeVotacaoRepository` (`salvar`, `listar_por_categoria`) e
  `CedulaRepository` (`salvar`, `buscar`, `listar_por_turno`), com fakes
  em `tests/application/fakes/`.
- `AvancarTemporadaOscar`: ao entrar em `EM_VOTACAO`, inicia a votação e
  abre o 1º turno de cada categoria, com as nomeações na ordem em que
  foram feitas.
- `RegistrarVoto(categoria_id, membro_id, escolhas)`: edição em votação,
  votação aberta, eleitor, categoria no turno atual e cédula não
  confirmada; cria a cédula do turno ou troca as escolhas da categoria.
- `ConfirmarCedula(temporada_id, membro_id)`: confere que a cédula tem
  voto em todas as categorias do turno (a recusa lista as que faltam),
  confirma e, se era o último eleitor, encerra o turno — apura cada
  categoria, grava os turnos seguintes e avança ou termina a votação.
  Devolve a votação atualizada, se o turno se encerrou e quem falta.
- `EnviarPlacarOscar(temporada_id, destinatario)`: votação terminada e
  edição não encerrada; monta o placar (categorias, turnos, nomeações com
  filme, quem indicou e pontos) e o envia pelo port `EnviadorDeEmail`.
- `RegistrarVencedorOscar(categoria_id, nomeacao_id?,
  membro_escolhido_id?)`: votação terminada, categoria sem troféu; com a
  nomeação, o troféu vai para quem a indicou (ou para o membro escolhido,
  se ela veio de uma democracia); sem nomeação, é um empate absoluto e o
  membro escolhido é obrigatório (`EscolhaDoGrupoNecessariaError`, 422,
  no lugar de `VencedorDemocraciaNaoInformadoError`); o membro escolhido
  precisa ser do clube (`MembroDeOutroClubeError`, 422, interpretação 3).
  Substitui `ApurarCategoriaOscar`, que sai junto com o port
  `CriterioApuracaoOscar` e as suas implementações (decisão técnica 24).
- `DesativarMembro` não muda: desativar continua permitido na votação.

**Infraestrutura** — port `EnviadorDeEmail` (`enviar(MensagemDeEmail)`),
genérico: o convite por código da Fase 5 pode usá-lo. Adapter SMTP (da
biblioteca padrão) configurado por variáveis de ambiente; sem
configuração, o envio é recusado com uma mensagem que diz o que
configurar. `EnderecoDeEmail` é value object do domínio.

**Persistência** — revisão 0005 (votação): `votacoes_oscar` (única por
temporada), `votacao_eleitores`, `turnos_votacao` (único por categoria e
número), `turno_candidatas` (`posicao`, `nomeacao_id`, `pontos` anulável
até a apuração), `cedulas` (única por votação, turno e membro) e
`cedula_escolhas`; as edições que já estiverem *em votação* ganham a sua
votação na migração. Revisão 0007 (vencedores):
`trofeus.nomeacao_vencedora_id` anulável, para o empate absoluto.

**Interfaces** — mostram só quem já votou e em quantas categorias; nunca
as cédulas nem o placar (decisão 26).

- CLI: `oscar votacao` (turno atual, categorias com as candidatas
  numeradas, eleitores e andamento), `oscar votar --membro-id ID
  --categoria-id ID ESCOLHA...` (pela posição da candidata ou pelo id da
  nomeação), `oscar confirmar --membro-id ID`, `oscar enviar-placar
  EMAIL`, `oscar categoria nomeacoes CATEGORIA_ID` e `oscar premiar
  CATEGORIA_ID [--nomeacao-id ID] [--membro-escolhido-id ID]`, que
  substitui `oscar apurar`.
- API: `GET /oscar/temporadas/{id}/votacao`,
  `PUT /oscar/categorias/{id}/votos/{membro_id}` (corpo
  `{"escolhas": [...]}`),
  `POST /oscar/temporadas/{id}/votacao/cedulas/{membro_id}/confirmacao`,
  `POST /oscar/temporadas/{id}/placar/envios` (corpo `{"destinatario"}`) e
  `POST /oscar/categorias/{id}/trofeu` (corpo `{"nomeacao_id"?,
  "membro_escolhido_id"?}`), que substitui `/apuracao`.
- Testes: a tabela de desfechos da contagem no domínio (vitória, empate
  parcial, empate geral na dupla e na classificação), cédula e
  confirmação, casos de uso, repositórios, migração, SMTP, CLI e API, e
  os dois fluxos completos votando, enviando o placar e premiando.

Ordem de implementação, um commit por etapa: **(a)** ✅ votação —
eleitores, turnos, cédulas, confirmação e desempates (revisão 0005);
**(b)** ✅ placar por e-mail; **(c)** vencedores registrados e remoção do
critério antigo (revisão 0007; a 0006 foi a da ordem de criação, que o
Postgres pediu).

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

Ordem decidida pelo dono em 13/10/2026 (decisão 36 de
[PENDENCIAS.md](PENDENCIAS.md)): primeiro a web publicada na Vercel,
depois o resto da votação. O trabalho segue no branch
`roadmap/fases-4-e-5`, um commit por etapa, com **push do branch** ao fim
de cada uma (a Vercel gera uma prévia); merge e push da `main`, que é a
produção, só a pedido do dono (decisão 37).

1. **Web na Vercel** (decisões 34 a 37):
   1. ✅ persistência portável — Postgres (Neon) na produção, SQLite local
      e nos testes; ordem de criação em coluna própria (revisão 0006);
      entrada `app.py` da Vercel; CI pronta para ligar;
   2. ✅ senha única do clube (decisão 35), protegendo o site e a API; a
      base da web (app raiz, modelos, visual), o início e o painel;
   3. ✅ páginas do dia a dia, conforme o plano da seção da Fase 4: início,
      painel da rodada, membros, filmes, histórico de rodadas, sessões e
      avaliações;
   4. ✅ Óscar até a votação: edições, categorias, nomeações, cédula e
      confirmação — e, com elas, a etapa (b) da votação, o placar por
      e-mail;
   5. **próximo:** etapa (c) da votação, os vencedores, com a tela de
      premiação.
2. Notas técnicas das etapas (b) e (c) da votação:
   - (b) `EnderecoDeEmail` (value object) e os erros
     `EnderecoDeEmailInvalidoError` (422), `VotacaoEmAndamentoError` (409)
     e, para o envio, um erro de "e-mail não configurado" (503) e um de
     falha do servidor SMTP (502) — os dois pedem título em português em
     `api/erros.py` (`_TITULOS`). O `Contexto` recebe o enviador como
     recebe o relógio (parâmetro opcional, padrão lido do ambiente:
     `FILMES_E_CUBOS_SMTP_HOST`, `_PORTA`, `_USUARIO`, `_SENHA`,
     `_REMETENTE`...), e a `FabricaDeContexto` da CLI também, para os
     testes injetarem um enviador fake. O placar sai de
     `TurnoDeVotacao.pontuacao`, `lideres` e `empate_absoluto`, com o
     título do filme e o nome de quem indicou (interpretação 15). Testar
     o adapter SMTP contra um servidor SMTP de verdade, local (ex.:
     `aiosmtpd` como dependência de desenvolvimento). Vale uma ADR (port
     de e-mail genérico, reaproveitável nos convites da Fase 5);
   - (c) `Trofeu.nomeacao_vencedora_id` opcional (revisão 0007),
     `RegistrarVencedorOscar` no lugar de `ApurarCategoriaOscar`, CLI
     `oscar premiar` e `oscar categoria nomeacoes`, API
     `POST /oscar/categorias/{id}/trofeu`; remover o port, as duas
     implementações, o fake, `obter_criterio_apuracao` da CLI e os
     testes deles; reescrever os dois fluxos de ponta a ponta (CLI e API)
     votando, enviando o placar e premiando, e o "Um ciclo completo" de
     CLI.md e API.md.
3. **Fase 5**: verificações entre clubes, login com convites e
   permissões (no lugar da senha única), TMDB.

Já feito da revisão de regras de 24 e 25/09 (decisões 3 a 11 e 16 a 33):
duração do filme (revisão 0002), reativar membro e data do evento; só
presentes avaliam e a média como fração (revisão 0003); filme que não se
repete; uma edição por ano, nomeações por categoria (revisão 0004) e o
ciclo com *em votação*; o contrato do histórico; e a etapa (a) da
votação — eleitores, cédulas, confirmação e desempates (revisão 0005).

## Pontos explicitamente em aberto

| Decisão | Status | Onde foi/será resolvida |
|---|---|---|
| Implementação concreta de persistência | ✅ Resolvida: SQLite via SQLAlchemy Core | Fase 2 |
| Primeira interface de usuário | ✅ Resolvida: CLI com Typer | Fase 3 |
| Tecnologia da API | ✅ Resolvida: FastAPI, erros RFC 9457 | Fase 4 |
| Tecnologia da interface web | ✅ Resolvida: páginas renderizadas no servidor (Jinja2) | Fase 4 |
| Evolução do esquema do banco | ✅ Resolvida: migrações com Alembic | Fase 4 |
| Mecanismo de apuração de categorias do Óscar (votação vs. critério fixo) | ✅ Decidida em 24 e 25/09/2026: votação ponderada (2/1) com eleitores definidos, cédula confirmada e desempates no sistema; placar enviado por e-mail e apuração fora do sistema; vencedores registrados depois do evento — a implementar | Hoje a CLI e a API ainda delegam a escolha a quem opera (port `CriterioApuracaoOscar`), que sai na etapa dos vencedores. Ver [PENDENCIAS.md](PENDENCIAS.md), decisões 8 e 21 a 29. |
| Módulo de histórico de sessões passadas | Contrato criado (`LeitorDeHistorico`); implementação em aberto | Ver [PENDENCIAS.md](PENDENCIAS.md), decisão 3 e questão em aberto 1. |
