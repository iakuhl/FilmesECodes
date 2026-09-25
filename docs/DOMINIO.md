# Modelo de Domínio

Este documento descreve as entidades, value objects e regras de negócio do
núcleo do sistema. Nomes de conceitos de domínio são mantidos em português,
fiéis à linguagem que o clube já usa no dia a dia (linguagem ubíqua).

## Visão geral das entidades

```
Clube 1 ── * Membro
Clube 1 ── * Rodada
Rodada 1 ── * Indicacao ── 1 Filme
Rodada 1 ── * Sorteio ── 1 Indicacao
Indicacao 1 ── 0..1 SessaoExibicao ── * Avaliacao ── 1 Membro
Clube 1 ── * TemporadaOscar
TemporadaOscar 1 ── * CategoriaOscar
CategoriaOscar 1 ── * NomeacaoOscar ── 1 Filme
CategoriaOscar 1 ── 0..1 Trofeu ── 1 Membro (indicador do filme vencedor)
```

Na implementação (Fase 1 do roadmap), as relações a partir de `Clube` são
representadas por um `clube_id` guardado em `Membro`, `Rodada` e
`TemporadaOscar` — não por `Clube` compor essas coleções diretamente. Isso
mantém cada entidade independente do tamanho do histórico do clube e já
prepara o terreno para múltiplos clubes (ver ROADMAP.md, Fase 5). Ver
[ARQUITETURA.md](ARQUITETURA.md) para o racional dessa escolha.

## Entidades

### Clube

Representa um clube de cinema. Existe desde já como entidade de primeira
classe (mesmo havendo um único clube, "Filmes e Cubos", em uso) para que
uma futura versão comercial possa suportar múltiplos clubes sem redesenho
do domínio.

- `id`
- `nome` (ex.: "Filmes e Cubos")
- `configuracao`: value object com parâmetros do clube, entre eles:
  - `tamanho_rodada`: quantas indicações compõem uma rodada (regra atual:
    igual ao número de membros ativos — hoje 5 — mas modelado como
    configuração, não como constante fixa no código).
  - `escala_avaliacao`: faixa e granularidade das notas (hoje: 0,5 a 5,0,
    em passos de 0,5).

### Membro

Uma pessoa do clube.

- `id`
- `clube_id`
- `nome`
- `apelido` (opcional)
- `data_ingresso`
- `ativo`: um membro pode ser desativado sem perder seu histórico de
  indicações, sessões e troféus — e reativado depois, com o mesmo
  histórico.

### Filme

Um filme do catálogo, compartilhado entre clubes. Dentro de um clube,
ele passa **uma vez só**: é indicado uma vez e assistido uma vez.

- `id`
- `titulo`
- `ano_lancamento`
- `diretor` (opcional)
- `identificador_externo` (opcional; reservado para integração futura com
  uma base de dados de filmes, ex. TMDB — não implementada nesta fase).
- `duracao_minutos` (opcional; positiva quando informada). Pode ser
  informada depois do cadastro — os filmes cadastrados antes de o campo
  existir não a têm. Serve para somar o tempo assistido no ano e comparar
  indicações (ver a Fase 6 do roadmap).

### Rodada

Um ciclo de indicações: começa quando os membros ativos começam a indicar
filmes e termina quando todas as indicações da rodada (normais e
DEMOCRACIA) tiverem sido assistidas.

- `id`
- `clube_id`
- `numero`: sequencial dentro do clube.
- `status`: `aberta` (aceitando indicações/sorteios) ou `encerrada`.
- `data_inicio`, `data_encerramento` (opcional até encerrar).

**Invariante**: uma rodada só pode ser encerrada quando todas as suas
`Indicacao` estiverem com status `assistida`.

### Indicacao

O filme que um membro indicou para uma rodada específica — ou que o
grupo escolheu assistir como sessão extra (indicação DEMOCRACIA).

- `id`
- `rodada_id`
- `membro_id`: quem indicou. **Ausente** (`None`) para indicações do
  tipo `democracia`, que não têm um indicador individual.
- `filme_id`
- `tipo`: `normal` (indicação semanal de um membro) ou `democracia`
  (sessão extra, escolhida em grupo — ver regra 7 abaixo).
- `status`: `pendente` (aguardando ser assistida), `sorteada`
  (passou pelo sorteio, opcional, e aguarda sessão) ou `assistida`.
- `data_indicacao`

**Invariantes**:
- cada membro ativo indica no máximo uma indicação `normal` por rodada
  (o número de indicações `normal` de uma rodada é limitado pelo
  `tamanho_rodada` configurado no `Clube`; indicações `democracia` ficam
  de fora dessa contagem);
- uma indicação vai de `pendente` direto para `assistida`, ou passa por
  `sorteada` no meio — o sorteio é uma etapa opcional de apoio, não
  obrigatória (ver regra 2 abaixo).

### Sorteio

Registro de qual `Indicacao` foi sorteada para a sessão da semana, dentre
as indicações ainda `pendente` da rodada corrente. Ferramenta opcional de
apoio: nem toda indicação passa por um sorteio antes de ser assistida.

- `id`
- `rodada_id`
- `indicacao_sorteada_id`
- `data_sorteio`
- `metodo`: identifica como o sorteio foi realizado (relevante para
  auditabilidade/reprodutibilidade — ver `SorteadorService` em
  [ARQUITETURA.md](ARQUITETURA.md)).

**Invariante**: só entram no sorteio indicações da rodada corrente com
status `pendente`.

### SessaoExibicao

A sessão em que o clube efetivamente assistiu ao filme (indicado
normalmente ou via DEMOCRACIA).

- `id`
- `indicacao_id`
- `data_sessao`
- `membros_presentes`: subconjunto dos membros do clube — **só eles
  avaliam** o filme.
- `media_das_notas` (value object `MediaDasNotas`, opcional): a média das
  notas recebidas, guardada como **fração exata** — a soma e a quantidade
  das notas —, sem arredondamento. Dorminhocos não entram. É refeita a
  partir de todas as avaliações da sessão a cada avaliação nova; fica
  ausente enquanto ninguém deu nota. As interfaces a exibem em estrelas:
  uma por inteiro e a fração restante com denominador de 2 a 10 (11/3 →
  ★★★⅔).

**Invariante**: uma sessão só existe para uma indicação com status
`pendente` ou `sorteada`; ao ser criada, a indicação correspondente passa
a `assistida`.

### Avaliacao

O resultado de um membro para uma sessão assistida: uma nota, ou o
registro de que o membro cochilou.

- `id`
- `sessao_id`
- `membro_id`: quem avaliou (ou cochilou) — precisa ter estado presente
  na sessão.
- `status`: `nota_registrada` ou `dorminhoco`.
- `nota`: valor entre 0,5 e 5,0, em passos de 0,5 (10 valores possíveis).
  Presente apenas quando `status` é `nota_registrada`; ausente
  (`None`) quando `dorminhoco`.
- `comentario` (opcional).

**Invariantes**: um membro avalia uma mesma sessão no máximo uma vez
(dê nota ou fique `dorminhoco`); uma nota informada deve respeitar a
`escala_avaliacao` configurada no `Clube`; avaliações `dorminhoco` devem
ser excluídas de qualquer cálculo de média (nenhum cálculo de média está
implementado ainda — esta é uma regra para quando ele existir).

### TemporadaOscar

Uma edição anual do "Óscar do Filmes e Cubos".

- `id`
- `clube_id`
- `ano`
- `nome` (ex.: "Óscar do Filmes e Cubos 2025")
- `status`: `em_preparacao` (define categorias) → `aberta_para_indicacoes`
  (nomeia filmes; ainda aceita categorias) → `em_votacao` (os membros
  votam; nomeações travadas) → `apurada` (toda categoria tem resultado) →
  `encerrada` (nada muda). O avanço é manual, um passo por vez, e cada
  ação confere se a fase atual a permite.
- `nomeacoes_por_categoria`: quantas nomeações **toda** categoria da
  edição tem — 5 por padrão, escolhido ao abrir a edição, no mínimo 2 (a
  votação pede duas opções distintas).
- `data_evento` (opcional até definida): pode ser marcada e remarcada
  em qualquer fase, menos depois de a edição ser encerrada.

### CategoriaOscar

Uma categoria de premiação dentro de uma `TemporadaOscar`.

- `id`
- `temporada_id`
- `nome` (ex.: "Melhor veículo", "Pior criança")
- `tipo`: `fixa` (se repete todo ano) ou `variavel` (exclusiva daquela
  edição).
- `descricao` (opcional, para categorias mais específicas/humorísticas).

Uma categoria recebe exatamente `nomeacoes_por_categoria` nomeações da
sua edição antes da votação — nem mais (a nomeação excedente é recusada),
nem menos (a edição não vai à votação).

### NomeacaoOscar

Um filme concorrendo em uma `CategoriaOscar` de uma temporada — um filme
assistido pelo clube dentro do ano daquela temporada.

- `id`
- `categoria_id`
- `filme_id`
- `indicado_por_membro_id`: **o mesmo membro que originalmente indicou
  esse filme em sua `Indicacao` semanal** — é ele quem receberá o troféu
  se o filme vencer a categoria. **Ausente** (`None`) quando o filme veio
  de uma indicação `democracia`, que não tem indicador individual — nesse
  caso, quem recebe o troféu é decidido pelo grupo no momento da
  apuração (ver `Trofeu` e regra 7 abaixo).

O mesmo filme pode ocupar várias nomeações da mesma categoria — uma
categoria pode até ser inteira sobre um filme só.

### Trofeu

O resultado da apuração de uma `CategoriaOscar`: qual `NomeacaoOscar`
venceu.

- `id`
- `categoria_id`
- `nomeacao_vencedora_id`
- `membro_vencedor_id`: normalmente derivado de
  `NomeacaoOscar.indicado_por_membro_id` — reforça a regra central de que
  **o troféu é entregue a quem indicou o filme**, não a quem "atua"
  tematicamente na categoria. Quando a nomeação vencedora não tem
  indicador (veio de uma indicação `democracia`), este campo vem de uma
  escolha manual do grupo, feita no momento da apuração/premiação.
- `data_apuracao`

## Regras de negócio centrais (resumo)

1. O tamanho de uma rodada (quantas indicações `normal` a compõem) é um
   parâmetro de configuração do `Clube`, não uma constante do código —
   hoje vale 5 porque há 5 membros ativos, mas o domínio não assume esse
   número.
2. O sorteio é uma etapa **opcional** de apoio, não obrigatória: uma
   indicação pode ser marcada como assistida diretamente a partir de
   `pendente` (ex.: o grupo decide pular o sorteio e escolher direto) ou
   passar por `sorteada` no meio. Só quando todas as indicações da
   rodada (normais e `democracia`) estiverem `assistida` é que uma nova
   rodada pode começar.
3. O sorteio, quando usado, só pode escolher entre indicações `pendente`
   da rodada corrente — nunca de rodadas já encerradas nem de indicações
   já sorteadas.
4. A escala de notas (0,5 a 5,0 em passos de 0,5) é uma configuração do
   clube, verificada como invariante de `Avaliacao` quando uma nota é
   informada. Uma avaliação sem nota vira `dorminhoco` e é ignorada em
   qualquer cálculo de média. Só avalia quem esteve presente na sessão, e
   a média da sessão fica guardada como fração exata (soma ÷ quantidade).
5. O troféu de uma categoria do Óscar aponta para o membro que
   originalmente indicou o filme vencedor no clube — é essa rastreabilidade
   entre `Indicacao` e `NomeacaoOscar` que torna a apuração possível. Para
   filmes indicados via `democracia` (sem indicador individual), o
   membro do troféu é escolhido pelo grupo no momento da apuração.
6. Categorias do Óscar podem ser fixas (recorrentes) ou variáveis
   (definidas a cada edição); ambas convivem na mesma `TemporadaOscar`.
7. Uma indicação `democracia` é uma sessão **extra**, não uma
   substituição da indicação normal da semana: acontece quando a sessão
   programada precisa ser adiada por imprevisto, e o clube assiste a um
   filme escolhido em grupo. Não conta na cota da rodada, não exige um
   membro indicador, e o filme concorre ao Óscar normalmente (desde que
   assistido dentro do ano da temporada).
8. Uma categoria do Óscar só aceita nomear filmes assistidos pelo clube
   **dentro do ano da temporada em questão** — um filme assistido em
   outro ano não pode concorrer, mesmo que já tenha sido assistido
   alguma vez. Só contam as sessões do próprio clube.
9. **Um filme não se repete no clube**: não se indica (nem em sessão
   `democracia`) um filme que o clube já assistiu ou que já está indicado
   e ainda não foi assistido. Por isso cada filme é assistido no máximo
   uma vez por clube, e a nomeação ao Óscar sempre tem um indicador
   inequívoco.
