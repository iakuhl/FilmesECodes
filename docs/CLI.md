# Interface de linha de comando

A CLI é o adapter de interface da Fase 3 (ver
[ARQUITETURA.md](ARQUITETURA.md) e [ROADMAP.md](ROADMAP.md)). Ela apenas
traduz entrada e saída de terminal em chamadas aos casos de uso de
[CASOS_DE_USO.md](CASOS_DE_USO.md) — nenhuma regra de negócio vive aqui.

```bash
uv run filmes-e-cubos --help
```

## Convenções

Valem para todos os comandos, e existem para que um comando novo não
precise reinventar nada:

- **Alvo posicional, resto nomeado.** Quando o comando tem um alvo
  evidente, ele é um argumento posicional (`membro desativar <MEMBRO_ID>`,
  `filme cadastrar "Parasita"`); todo o resto são opções nomeadas.
- **Ids dedutíveis são opcionais.** O clube, a rodada aberta e a
  temporada do ano corrente são deduzidos quando não informados. A CLI só
  deduz o que é inequívoco: com dois clubes cadastrados, ela para e pede
  `--clube-id` em vez de escolher por conta própria.
- **Erros vão para `stderr` com código de saída 1**, e `stdout` fica
  limpo — o que permite encadear a saída de um comando em um pipe. Erros
  de sintaxe do próprio parser (um id que não é UUID, um valor fora das
  opções aceitas) saem com código 2, como manda a convenção do Click.
- **Criou, mostra o id.** Todo comando de criação imprime o id da
  entidade criada, porque é ele que alimenta o comando seguinte.
- **Campo vazio aparece como `—`**, nunca como célula em branco.
- **Números aceitam vírgula ou ponto** na entrada (`--nota 4,5` ou
  `--nota 4.5`) e saem sempre com vírgula.

## Onde ficam os dados

Um arquivo SQLite, por padrão `filmes_e_cubos.db` no diretório atual.
Para usar outro:

```bash
filmes-e-cubos --db-path /caminho/do/clube.db clube listar
export FILMES_E_CUBOS_DB=/caminho/do/clube.db   # equivalente, persistente
```

O banco é criado na primeira vez que um comando precisa dele. Consultar a
ajuda não cria nada.

## Comandos

### `clube`

| Comando | O que faz |
|---|---|
| `clube criar NOME [--tamanho-rodada N] [--nota-minima X] [--nota-maxima X] [--passo X]` | Cria um clube. Sem opções, usa a configuração padrão do domínio (rodadas de 5, notas de 0,5 a 5,0 em passos de 0,5). |
| `clube listar` | Lista os clubes com sua configuração. |

### `membro`

| Comando | O que faz |
|---|---|
| `membro cadastrar NOME [--apelido X] [--clube-id ID]` | Cadastra um membro, já ativo. |
| `membro desativar MEMBRO_ID` | Desativa o membro. O histórico dele (indicações, avaliações, troféus) permanece intacto; ele só deixa de contar para a rodada. |
| `membro reativar MEMBRO_ID` | Reativa o membro, com o histórico que ele já tinha. |
| `membro listar [--apenas-ativos] [--clube-id ID]` | Lista os membros e sua situação. |

### `filme`

O catálogo é compartilhado: um filme não pertence a um clube.

| Comando | O que faz |
|---|---|
| `filme cadastrar TITULO [--ano N] [--diretor X] [--id-externo X] [--duracao MIN]` | Cadastra um filme. Só o título é obrigatório; a duração é em minutos. |
| `filme duracao FILME_ID MINUTOS` | Informa ou corrige a duração de um filme já cadastrado. |
| `filme listar` | Lista o catálogo. |

### `rodada`

| Comando | O que faz |
|---|---|
| `rodada abrir [--clube-id ID]` | Abre uma rodada. Falha se já houver uma aberta. |
| `rodada status [--rodada-id ID] [--clube-id ID]` | Mostra a rodada e a situação de cada indicação. Sem `--rodada-id`, mostra a aberta. |
| `rodada encerrar [--rodada-id ID] [--clube-id ID]` | Encerra a rodada. Falha se alguma indicação ainda não tiver sido assistida. |

### `indicacao`

| Comando | O que faz |
|---|---|
| `indicacao indicar --membro-id ID --filme-id ID [--rodada-id ID]` | Indicação semanal de um membro. Um membro indica uma vez por rodada, e a rodada respeita o `tamanho_rodada` do clube. |
| `indicacao democracia --filme-id ID [--clube-id ID]` | Sessão extra escolhida em grupo, para quando a sessão programada é adiada. Não tem membro indicador e não consome a cota da rodada. |
| `indicacao sortear [--rodada-id ID] [--clube-id ID]` | Sorteia uma das indicações pendentes. É apoio **opcional**: nada impede de registrar a sessão de uma indicação que nunca passou pelo sorteio. |

### `sessao`

| Comando | O que faz |
|---|---|
| `sessao registrar INDICACAO_ID [--presente MEMBRO_ID]...` | Registra que o filme foi assistido e marca a indicação como assistida. Sem nenhum `--presente`, assume todos os membros ativos do clube. |

### `avaliacao`

| Comando | O que faz |
|---|---|
| `avaliacao registrar --sessao-id ID --membro-id ID [--nota X] [--comentario X]` | Registra a nota de um membro. **Sem `--nota`, registra que ele cochilou** (`dorminhoco`): o voto fica para a posteridade, mas é ignorado em médias. Cada membro avalia cada sessão uma vez só. |
| `avaliacao listar SESSAO_ID` | Lista as avaliações da sessão. |

### `oscar`

| Comando | O que faz |
|---|---|
| `oscar temporada abrir [--ano N] [--nome X] [--clube-id ID]` | Abre a edição anual. Sem `--ano`, usa o ano corrente. |
| `oscar temporada listar [--clube-id ID]` | Lista as edições do clube, com a situação e a data do evento. |
| `oscar temporada data-evento DATA [--temporada-id ID] [--clube-id ID]` | Marca (ou remarca) o dia da cerimônia: `AAAA-MM-DD` ou `DD/MM/AAAA`. Recusado depois que a edição é encerrada. |
| `oscar categoria definir NOME [--tipo fixa\|variavel] [--descricao X] [--temporada-id ID]` | Adiciona uma categoria. O padrão é `variavel`. |
| `oscar categoria listar [--temporada-id ID]` | Lista as categorias e quem já levou cada troféu. |
| `oscar nomear --categoria-id ID --filme-id ID` | Nomeia um filme para a categoria. O filme precisa ter sido assistido pelo clube **dentro do ano da temporada**. |
| `oscar apurar CATEGORIA_ID [--membro-vencedor-id ID]` | Apura a categoria e emite o troféu. |

#### Como a apuração decide o vencedor

O mecanismo de apuração continua em aberto no produto (votação? média de
notas? júri?), então a CLI não inventa um: ela lista as nomeações e
pergunta qual venceu.

```
Nomeações desta categoria:
  1) Parasita  [nomeação 11435ed2-...]
  2) Interestelar  [nomeação 9e438f84-...]

Número da nomeação vencedora: 2
✔ Troféu para Bia (55f6746e-...)
```

Isso não é um atalho: é o port `CriterioApuracaoOscar` cumprindo
exatamente o papel para o qual foi criado. No dia em que o clube decidir
um critério automático, basta escrever outro adapter e trocá-lo no
composition root — sem tocar em domínio nem em aplicação.

O troféu vai para **quem indicou o filme vencedor**, não para quem "atua"
na categoria. Quando o filme vencedor veio de uma sessão `democracia`
(que não tem membro indicador), o comando exige
`--membro-vencedor-id` com a escolha do grupo.

## Um ciclo completo

```bash
filmes-e-cubos clube criar "Filmes e Cubos"
filmes-e-cubos membro cadastrar "Iano"
filmes-e-cubos membro cadastrar "Bia"
filmes-e-cubos filme cadastrar "Parasita" --ano 2019 --diretor "Bong Joon-ho"
filmes-e-cubos filme cadastrar "Interestelar" --ano 2014

filmes-e-cubos rodada abrir
filmes-e-cubos indicacao indicar --membro-id <IANO> --filme-id <PARASITA>
filmes-e-cubos indicacao indicar --membro-id <BIA> --filme-id <INTERESTELAR>
filmes-e-cubos rodada status

filmes-e-cubos indicacao sortear                    # imprime a indicação sorteada
filmes-e-cubos sessao registrar <INDICACAO_SORTEADA>
filmes-e-cubos avaliacao registrar --sessao-id <SESSAO> --membro-id <IANO> --nota 4,5
filmes-e-cubos avaliacao registrar --sessao-id <SESSAO> --membro-id <BIA>   # dorminhoco
filmes-e-cubos avaliacao listar <SESSAO>

# ... repete até todas as indicações da rodada terem sido assistidas
filmes-e-cubos rodada encerrar

filmes-e-cubos oscar temporada abrir
filmes-e-cubos oscar categoria definir "Melhor veículo" --tipo variavel
filmes-e-cubos oscar nomear --categoria-id <CATEGORIA> --filme-id <PARASITA>
filmes-e-cubos oscar apurar <CATEGORIA>
filmes-e-cubos oscar categoria listar
```
