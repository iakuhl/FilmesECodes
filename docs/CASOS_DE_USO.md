# Casos de Uso

Cada caso de uso vive na camada `application` e orquestra entidades de
`domain` através dos ports necessários. Nenhum caso de uso conhece uma
implementação concreta — apenas os contratos (ver
[ARQUITETURA.md](ARQUITETURA.md)).

Convenção: casos de uso são nomeados como verbo + objeto, e cada um lista
os ports (repositórios/serviços) de que depende.

## Gestão de clube e membros

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

## Rodadas e indicações

### AbrirNovaRodada
- **Intenção**: iniciar uma nova rodada de indicações.
- **Ports**: `RodadaRepository`, `MembroRepository`, `RelogioService`.
- **Regras**: só permite abrir uma nova rodada se não houver outra
  `aberta` para o clube.

### IndicarFilme
- **Intenção**: registrar a indicação de um filme por um membro na rodada
  corrente.
- **Ports**: `RodadaRepository`, `IndicacaoRepository`, `FilmeRepository`,
  `MembroRepository`.
- **Regras**: a rodada precisa estar `aberta`; um membro não pode indicar
  duas vezes na mesma rodada; a rodada não pode exceder o
  `tamanho_rodada` configurado.

### RealizarSorteio
- **Intenção**: sortear uma das indicações `pendente` da rodada corrente
  para a próxima sessão.
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
- **Intenção**: registrar que o filme sorteado foi assistido em uma data,
  com os membros presentes.
- **Ports**: `IndicacaoRepository`, `SessaoRepository`, `RelogioService`.
- **Regras**: só é possível para uma indicação com status `sorteada`;
  ao concluir, marca a indicação como `assistida`.

### AvaliarFilme
- **Intenção**: um membro registra sua nota (e comentário opcional) para
  o filme assistido em uma sessão.
- **Ports**: `SessaoRepository`, `AvaliacaoRepository`, `MembroRepository`.
- **Regras**: nota dentro da `escala_avaliacao` do clube; um membro avalia
  cada sessão no máximo uma vez.

## Óscar do Filmes e Cubos

### AbrirTemporadaOscar
- **Intenção**: criar uma nova edição anual do Óscar.
- **Ports**: `TemporadaOscarRepository`, `RelogioService`.
- **Regras**: normalmente uma temporada por ano civil; nome pode ser
  customizado.

### DefinirCategoriaOscar
- **Intenção**: adicionar uma categoria (fixa ou variável) a uma
  temporada.
- **Ports**: `TemporadaOscarRepository`.
- **Regras**: nome obrigatório; tipo (`fixa`/`variavel`) obrigatório.

### IndicarFilmeParaCategoria
- **Intenção**: nomear um filme (já assistido pelo clube) para concorrer
  em uma categoria da temporada.
- **Ports**: `TemporadaOscarRepository`, `IndicacaoRepository`,
  `FilmeRepository`.
- **Regras**: o filme precisa ter sido efetivamente assistido pelo clube
  (existir uma `Indicacao` `assistida` correspondente); a `NomeacaoOscar`
  herda o `indicado_por_membro_id` da indicação original — essa
  rastreabilidade é o que permite entregar o troféu a quem indicou.

### ApurarCategoriaOscar
- **Intenção**: calcular/registrar o vencedor de uma categoria e emitir o
  `Trofeu` correspondente ao membro que indicou o filme vencedor.
- **Ports**: `TemporadaOscarRepository`, `RelogioService`.
- **Regras**: a apuração pode ser por votação dos membros ou por critério
  definido por categoria — o mecanismo de apuração em si é um detalhe a
  refinar na fase de implementação; o caso de uso apenas garante que o
  `Trofeu` resultante aponta corretamente para o membro indicador.
