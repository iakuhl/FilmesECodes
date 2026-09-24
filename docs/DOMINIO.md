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
  indicações, sessões e troféus.

### Filme

Um filme indicado e potencialmente assistido pelo clube.

- `id`
- `titulo`
- `ano_lancamento`
- `diretor` (opcional)
- `identificador_externo` (opcional; reservado para integração futura com
  uma base de dados de filmes, ex. TMDB — não implementada nesta fase).

### Rodada

Um ciclo de indicações: começa quando os membros ativos começam a indicar
filmes e termina quando todas as indicações da rodada tiverem sido
sorteadas e assistidas.

- `id`
- `clube_id`
- `numero`: sequencial dentro do clube.
- `status`: `aberta` (aceitando indicações/sorteios) ou `encerrada`.
- `data_inicio`, `data_encerramento` (opcional até encerrar).

**Invariante**: uma rodada só pode ser encerrada quando todas as suas
`Indicacao` estiverem com status `assistida`.

### Indicacao

O filme que um membro indicou para uma rodada específica.

- `id`
- `rodada_id`
- `membro_id`: quem indicou.
- `filme_id`
- `status`: `pendente` (aguardando sorteio), `sorteada` (aguardando
  sessão) ou `assistida`.
- `data_indicacao`

**Invariante**: cada membro ativo indica no máximo um filme por rodada
(o número de indicações de uma rodada é limitado pelo
`tamanho_rodada` configurado no `Clube`).

### Sorteio

Registro de qual `Indicacao` foi sorteada para a sessão da semana, dentre
as indicações ainda `pendente` da rodada corrente.

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

A sessão em que o clube efetivamente assistiu ao filme sorteado.

- `id`
- `indicacao_id`
- `data_sessao`
- `membros_presentes`: subconjunto dos membros do clube.

**Invariante**: uma sessão só existe para uma indicação com status
`sorteada`; ao ser criada, a indicação correspondente passa a
`assistida`.

### Avaliacao

A nota que um membro dá ao filme assistido em uma sessão.

- `id`
- `sessao_id`
- `membro_id`: quem avaliou.
- `nota`: valor entre 0,5 e 5,0, em passos de 0,5 (10 valores possíveis).
- `comentario` (opcional).

**Invariante**: um membro avalia uma mesma sessão no máximo uma vez; a
nota deve respeitar a `escala_avaliacao` configurada no `Clube`.

### TemporadaOscar

Uma edição anual do "Óscar do Filmes e Cubos".

- `id`
- `clube_id`
- `ano`
- `nome` (ex.: "Óscar do Filmes e Cubos 2025")
- `status`: `em_preparacao`, `aberta_para_indicacoes`, `apurada`,
  `encerrada`.
- `data_evento` (opcional até definida).

### CategoriaOscar

Uma categoria de premiação dentro de uma `TemporadaOscar`.

- `id`
- `temporada_id`
- `nome` (ex.: "Melhor veículo", "Pior criança")
- `tipo`: `fixa` (se repete todo ano) ou `variavel` (exclusiva daquela
  edição).
- `descricao` (opcional, para categorias mais específicas/humorísticas).

### NomeacaoOscar

Um filme concorrendo em uma `CategoriaOscar` de uma temporada — tipicamente
um filme já assistido pelo clube naquele ano.

- `id`
- `categoria_id`
- `filme_id`
- `indicado_por_membro_id`: **o mesmo membro que originalmente indicou
  esse filme em sua `Indicacao` semanal** — é ele quem receberá o troféu
  se o filme vencer a categoria.

### Trofeu

O resultado da apuração de uma `CategoriaOscar`: qual `NomeacaoOscar`
venceu.

- `id`
- `categoria_id`
- `nomeacao_vencedora_id`
- `membro_vencedor_id`: derivado de `NomeacaoOscar.indicado_por_membro_id`
  — reforça a regra central de que **o troféu é entregue a quem indicou
  o filme**, não a quem "atua" tematicamente na categoria.
- `data_apuracao`

## Regras de negócio centrais (resumo)

1. O tamanho de uma rodada (quantas indicações a compõem) é um parâmetro
   de configuração do `Clube`, não uma constante do código — hoje vale 5
   porque há 5 membros ativos, mas o domínio não assume esse número.
2. Uma rodada avança indicação por indicação: sorteio → sessão → nota; só
   quando todas as indicações da rodada estiverem `assistida` é que uma
   nova rodada pode começar.
3. O sorteio só pode escolher entre indicações `pendente` da rodada
   corrente — nunca de rodadas já encerradas nem de indicações já
   sorteadas.
4. A escala de notas (0,5 a 5,0 em passos de 0,5) é uma configuração do
   clube, verificada como invariante de `Avaliacao`.
5. O troféu de uma categoria do Óscar sempre aponta para o membro que
   originalmente indicou o filme vencedor no clube — é essa rastreabilidade
   entre `Indicacao` e `NomeacaoOscar` que torna a apuração possível.
6. Categorias do Óscar podem ser fixas (recorrentes) ou variáveis
   (definidas a cada edição); ambas convivem na mesma `TemporadaOscar`.
