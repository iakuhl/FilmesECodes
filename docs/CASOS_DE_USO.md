# Casos de Uso

Cada caso de uso vive na camada `application` e orquestra entidades de
`domain` através dos ports necessários. Nenhum caso de uso conhece uma
implementação concreta — apenas os contratos (ver
[ARQUITETURA.md](ARQUITETURA.md)).

Convenção: casos de uso são nomeados como verbo + objeto, e cada um lista
os ports (repositórios/serviços) de que depende.

## Gestão de clube e membros

### CriarClube
- **Intenção**: criar um novo clube, com configuração padrão ou
  customizada.
- **Ports**: `ClubeRepository`.
- **Regras**: nome obrigatório (validado pela própria entidade `Clube`);
  sem configuração informada, usa `ConfiguracaoClube.padrao()`.

### CadastrarMembro
- **Intenção**: adicionar um novo membro ao clube.
- **Ports**: `MembroRepository`.
- **Regras**: nome obrigatório; membro criado como `ativo`.

### DesativarMembro
- **Intenção**: marcar um membro como inativo sem apagar seu histórico.
- **Ports**: `MembroRepository`.
- **Regras**: um membro desativado deixa de contar para o
  `tamanho_rodada`, mas seus registros passados (indicações, avaliações,
  troféus) permanecem intactos.

### ReativarMembro
- **Intenção**: devolver às rodadas um membro desativado.
- **Ports**: `MembroRepository`.
- **Regras**: o membro volta a contar para o `tamanho_rodada` e a
  indicar, avaliar e votar, com o histórico que já tinha.

## Catálogo de filmes

### CadastrarFilme
- **Intenção**: adicionar um filme ao catálogo, disponível para ser
  indicado por qualquer clube.
- **Ports**: `FilmeRepository`.
- **Regras**: título obrigatório (validado pela própria entidade
  `Filme`); demais campos (ano, diretor, identificador externo, duração
  em minutos) são opcionais; a duração, quando informada, é positiva.

### DefinirDuracaoFilme
- **Intenção**: informar ou corrigir a duração de um filme já cadastrado
  (os cadastrados antes de o campo existir não a têm).
- **Ports**: `FilmeRepository`.
- **Regras**: duração positiva, em minutos.

## Rodadas e indicações

### AbrirNovaRodada
- **Intenção**: iniciar uma nova rodada de indicações.
- **Ports**: `RodadaRepository`, `MembroRepository`, `RelogioService`.
- **Regras**: só permite abrir uma nova rodada se não houver outra
  `aberta` para o clube.

### IndicarFilme
- **Intenção**: registrar a indicação `normal` de um filme por um membro
  na rodada corrente.
- **Ports**: `RodadaRepository`, `IndicacaoRepository`, `FilmeRepository`,
  `MembroRepository`, `ClubeRepository`.
- **Regras**: a rodada precisa estar `aberta`; um membro não pode indicar
  duas vezes na mesma rodada; a rodada não pode exceder o
  `tamanho_rodada` configurado. Indicações `democracia` não entram nessas
  contagens (ver `AdicionarFilmeDemocracia`).

### AdicionarFilmeDemocracia
- **Intenção**: registrar uma indicação `democracia` — sessão extra,
  escolhida em grupo, quando a sessão programada precisa ser adiada. Não
  substitui a indicação normal da semana.
- **Ports**: `RodadaRepository`, `IndicacaoRepository`, `FilmeRepository`.
- **Regras**: precisa haver uma rodada `aberta` para o clube; não exige
  (nem aceita) um membro indicador; não conta na cota de `tamanho_rodada`
  nem na checagem de indicação duplicada por membro.

### RealizarSorteio
- **Intenção**: sortear uma das indicações `pendente` da rodada corrente
  para a próxima sessão. Ferramenta **opcional** de apoio — nada obriga
  uma indicação a passar por aqui antes de ser assistida.
- **Ports**: `RodadaRepository`, `IndicacaoRepository`, `SorteioRepository`,
  `SorteadorService`, `RelogioService`.
- **Regras**: só considera indicações `pendente` da rodada corrente;
  marca a indicação sorteada como `sorteada`; registra o `Sorteio` para
  auditoria.

### EncerrarRodada
- **Intenção**: encerrar a rodada corrente quando todas as indicações
  estiverem `assistida`.
- **Ports**: `RodadaRepository`, `IndicacaoRepository`, `RelogioService`.
- **Regras**: falha se houver qualquer indicação não `assistida`.

## Sessões e avaliações

### RegistrarSessaoExibicao
- **Intenção**: registrar que o filme da indicação foi assistido em uma
  data, com os membros presentes.
- **Ports**: `IndicacaoRepository`, `SessaoRepository`, `RelogioService`.
- **Regras**: possível a partir de `pendente` (sorteio pulado) ou
  `sorteada`; ao concluir, marca a indicação como `assistida`.

### AvaliarFilme
- **Intenção**: um membro registra o resultado da sessão para si: uma
  nota (e comentário opcional), ou, sem nota, o registro de que cochilou
  (`dorminhoco`).
- **Ports**: `SessaoRepository`, `AvaliacaoRepository`, `MembroRepository`,
  `ClubeRepository`.
- **Regras**: nota, quando informada, precisa estar dentro da
  `escala_avaliacao` do clube; um membro avalia cada sessão no máximo uma
  vez, dê nota ou fique `dorminhoco`.

## Óscar do Filmes e Cubos

### AbrirTemporadaOscar
- **Intenção**: criar uma nova edição anual do Óscar.
- **Ports**: `TemporadaOscarRepository`, `RelogioService`.
- **Regras**: normalmente uma temporada por ano civil; nome pode ser
  customizado.

### DefinirDataEventoOscar
- **Intenção**: marcar (ou remarcar) o dia da cerimônia de uma edição.
- **Ports**: `TemporadaOscarRepository`.
- **Regras**: permitido em qualquer fase, menos depois de a edição ser
  encerrada (`AcaoForaDaFaseError`).

### DefinirCategoriaOscar
- **Intenção**: adicionar uma categoria (fixa ou variável) a uma
  temporada.
- **Ports**: `TemporadaOscarRepository`.
- **Regras**: nome obrigatório; tipo (`fixa`/`variavel`) obrigatório.

### IndicarFilmeParaCategoria
- **Intenção**: nomear um filme, assistido pelo clube **dentro do ano da
  temporada**, para concorrer em uma categoria.
- **Ports**: `NomeacaoOscarRepository`, `CategoriaOscarRepository`,
  `TemporadaOscarRepository`, `IndicacaoRepository`, `SessaoRepository`.
- **Regras**: o filme precisa ter sido assistido pelo clube (existir uma
  `Indicacao` `assistida` correspondente) e essa sessão precisa ter
  ocorrido dentro do ano da temporada da categoria — um filme assistido
  em outro ano não é elegível, mesmo já tendo sido assistido alguma vez.
  A `NomeacaoOscar` herda o `indicado_por_membro_id` da indicação
  original (`None` se ela for `democracia`) — essa rastreabilidade é o
  que permite entregar o troféu a quem indicou.

### ApurarCategoriaOscar
- **Intenção**: calcular/registrar o vencedor de uma categoria e emitir o
  `Trofeu` correspondente.
- **Ports**: `TrofeuRepository`, `NomeacaoOscarRepository`,
  `CategoriaOscarRepository`, `CriterioApuracaoOscar`, `RelogioService`.
- **Regras**: a apuração pode ser por votação dos membros ou por critério
  definido por categoria — o mecanismo de apuração em si é um detalhe a
  refinar depois (por isso é um port plugável, `CriterioApuracaoOscar`).
  Quando a nomeação vencedora tem `indicado_por_membro_id` (indicação
  `normal`), o troféu vai automaticamente para esse membro. Quando não
  tem (indicação `democracia`), o caso de uso exige um
  `membro_vencedor_manual_id` — a escolha do grupo, feita na hora da
  apuração/premiação — e levanta erro se ele não for informado.
