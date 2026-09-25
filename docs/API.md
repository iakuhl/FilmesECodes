# API HTTP

A API é o adapter de interface HTTP da Fase 4 (ver
[ARQUITETURA.md](ARQUITETURA.md) e [ROADMAP.md](ROADMAP.md)). Como a
[CLI](CLI.md), ela apenas traduz requisições em chamadas aos casos de uso
de [CASOS_DE_USO.md](CASOS_DE_USO.md) — nenhuma regra de negócio vive
aqui. Existe para o uso remoto pelos membros do clube e para qualquer
cliente futuro (um app, outro frontend, uma automação).

```bash
uv run filmes-e-cubos-servidor            # http://127.0.0.1:8000
```

A documentação interativa (OpenAPI/Swagger), gerada a partir do próprio
código, fica em **`/api/v1/docs`**; o documento OpenAPI bruto, em
`/api/v1/openapi.json`.

## Rodando o servidor

| Opção | Padrão | O que faz |
|---|---|---|
| `--host` | `127.0.0.1` | Endereço em que o servidor escuta. O padrão só aceita conexões da própria máquina. |
| `--porta` | `8000` | Porta TCP. |
| `--db-path` | `filmes_e_cubos.db` | Arquivo SQLite — o mesmo da CLI. Também lido de `FILMES_E_CUBOS_DB`. |
| `--recarregar` | desligado | Reinicia ao detectar mudança no código (desenvolvimento). |

> **Ainda não há autenticação.** Qualquer pessoa que alcance o servidor
> pode ler e alterar os dados do clube. Por isso o padrão é ouvir só em
> `127.0.0.1`; expor na rede (`--host 0.0.0.0`) é uma decisão explícita,
> que só faz sentido numa rede de confiança ou atrás de um proxy que
> autentique. Autenticação está prevista na Fase 5 do roadmap.

CLI e servidor podem usar o mesmo arquivo de banco — o que um registra, o
outro enxerga.

## Convenções

- **Tudo sob `/api/v1`.** A versão no caminho permite evoluir a API sem
  quebrar clientes antigos, quando isso for necessário.
- **Recursos aninhados só quando pertencem a um clube.** Coleções que
  pertencem a um clube ficam sob ele (`/clubes/{id}/membros`,
  `/clubes/{id}/rodadas`); cada recurso, uma vez criado, é endereçado
  pelo próprio id (`/membros/{id}`, `/rodadas/{id}`). O catálogo de
  filmes é compartilhado entre clubes e fica na raiz (`/filmes`).
- **Ações de domínio são `POST` em um sub-recurso com verbo** quando não
  criam nada (`POST /rodadas/{id}/encerrar`, `POST /membros/{id}/desativar`)
  e devolvem `200` com o recurso atualizado. Criações devolvem `201` com
  o recurso criado.
- **Ids** são UUIDs em texto. **Datas** em ISO 8601.
- **Decimais** (notas, escala) saem como texto (`"4.5"`), para preservar
  a precisão exata que o domínio guarda; na entrada, aceitam número ou
  texto (`4.5` ou `"4.5"`).
- **Enumerações** em minúsculas: `"aberta"`, `"pendente"`, `"dorminhoco"`,
  `"democracia"`, `"variavel"`.
- **Campos desconhecidos no corpo são recusados** (422), para que um erro
  de digitação não seja ignorado em silêncio.
- **Escritas acontecem uma de cada vez** (ver ADR 10 em
  [ARQUITETURA.md](ARQUITETURA.md)): duas requisições simultâneas — um
  duplo clique, por exemplo — nunca furam juntas uma regra do tipo "cada
  membro indica uma vez por rodada".

## Erros

Toda resposta de erro é `application/problem+json`, no formato da
[RFC 9457](https://www.rfc-editor.org/rfc/rfc9457), com um campo extra,
`codigo`, que identifica o erro de forma estável:

```json
{
  "type": "about:blank",
  "title": "Conflito com o estado atual",
  "status": 409,
  "detail": "Já existe uma rodada aberta para o clube 56052edc-....",
  "codigo": "rodada_ja_aberta"
}
```

O `codigo` deriva do nome da exceção de domínio (`RodadaJaAbertaError` →
`rodada_ja_aberta`), então programas podem reagir a um erro específico sem
depender do texto da mensagem.

| Status | Quando | Exemplos de `codigo` |
|---|---|---|
| `404` | O recurso do caminho — ou uma entidade referenciada no corpo — não existe. | `entidade_nao_encontrada`, `recurso_nao_encontrado` |
| `409` | A ação é válida, mas colide com o estado atual. | `rodada_ja_aberta`, `indicacao_duplicada`, `rodada_lotada`, `membro_inativo`, `avaliacao_duplicada`, `categoria_ja_apurada` |
| `422` | Dados ausentes, malformados ou que violam uma regra de negócio. | `requisicao_invalida`, `nota_fora_da_escala`, `nome_clube_obrigatorio`, `filme_nao_assistido_no_ano_da_temporada` |
| `500` | Defeito do servidor. O detalhe nunca vaza informação interna. | `erro_interno` |

Erros de validação do próprio formato (`requisicao_invalida`) trazem
também a lista `erros`, com o campo e o motivo:

```json
{ "...": "...", "codigo": "requisicao_invalida",
  "erros": [{"campo": "body.nota", "mensagem": "Field required", "tipo": "missing"}] }
```

## Recursos

### Clubes

| Método e caminho | O que faz |
|---|---|
| `GET /clubes` | Lista os clubes. |
| `POST /clubes` | Cria um clube. Corpo: `{"nome", "configuracao"?: {"tamanho_rodada"?, "escala_avaliacao"?: {"nota_minima"?, "nota_maxima"?, "passo"?}}}`. Todo campo de configuração omitido usa o padrão do domínio (rodadas de 5, notas de 0,5 a 5,0 em passos de 0,5). |
| `GET /clubes/{clube_id}` | Consulta um clube. |

### Membros

| Método e caminho | O que faz |
|---|---|
| `GET /clubes/{clube_id}/membros[?apenas_ativos=true]` | Lista os membros do clube. |
| `POST /clubes/{clube_id}/membros` | Cadastra um membro, já ativo. Corpo: `{"nome", "apelido"?}`. |
| `GET /membros/{membro_id}` | Consulta um membro. |
| `POST /membros/{membro_id}/desativar` | Desativa o membro, preservando o histórico dele. |
| `POST /membros/{membro_id}/reativar` | Reativa o membro, com o histórico que ele já tinha. |

### Filmes

| Método e caminho | O que faz |
|---|---|
| `GET /filmes` | Lista o catálogo (compartilhado entre clubes). |
| `POST /filmes` | Cadastra um filme. Corpo: `{"titulo", "ano_lancamento"?, "diretor"?, "identificador_externo"?, "duracao_minutos"?}`. |
| `PUT /filmes/{filme_id}/duracao` | Informa ou corrige a duração. Corpo: `{"duracao_minutos"}` (positiva; `422` se não for). |
| `GET /filmes/{filme_id}` | Consulta um filme. |

### Rodadas

| Método e caminho | O que faz |
|---|---|
| `GET /clubes/{clube_id}/rodadas` | Histórico de rodadas do clube, da primeira à mais recente. |
| `POST /clubes/{clube_id}/rodadas` | Abre uma rodada. `409` se já houver uma aberta. |
| `GET /clubes/{clube_id}/rodadas/aberta` | A rodada aberta do clube; `404` se não houver. |
| `GET /rodadas/{rodada_id}` | Consulta uma rodada. |
| `POST /rodadas/{rodada_id}/encerrar` | Encerra a rodada. `409` se alguma indicação ainda não tiver sido assistida. |

### Indicações e sorteios

| Método e caminho | O que faz |
|---|---|
| `GET /rodadas/{rodada_id}/indicacoes` | Lista as indicações da rodada. |
| `POST /rodadas/{rodada_id}/indicacoes` | Indicação semanal de um membro. Corpo: `{"membro_id", "filme_id"}`. `409` (`filme_repetido_no_clube`) se o filme já passou pelo clube — assistido, ou indicado e ainda pendente; vale também para a democracia. |
| `POST /clubes/{clube_id}/indicacoes-democracia` | Sessão extra escolhida em grupo, na rodada aberta do clube. Corpo: `{"filme_id"}`. Não tem membro indicador e não consome a cota da rodada. |
| `GET /indicacoes/{indicacao_id}` | Consulta uma indicação. |
| `GET /rodadas/{rodada_id}/sorteios` | Lista os sorteios da rodada. |
| `POST /rodadas/{rodada_id}/sorteios` | Sorteia uma das indicações pendentes. Apoio **opcional**. |

### Sessões

| Método e caminho | O que faz |
|---|---|
| `POST /indicacoes/{indicacao_id}/sessao` | Registra que o filme foi assistido e marca a indicação como assistida. Corpo opcional: `{"membros_presentes"?: [ids]}`. Sem a lista, assume todos os membros ativos do clube; uma lista vazia registra a sessão sem presentes. |
| `GET /indicacoes/{indicacao_id}/sessao` | A sessão da indicação; `404` enquanto ela não tiver sido assistida. |
| `GET /sessoes/{sessao_id}` | Consulta uma sessão, com a média das notas: `{"soma_das_notas", "quantidade_de_notas", "estrelas"}` — a média exata é a soma dividida pela quantidade; `null` enquanto ninguém deu nota. |

### Avaliações

| Método e caminho | O que faz |
|---|---|
| `GET /sessoes/{sessao_id}/avaliacoes` | Lista as avaliações da sessão. |
| `POST /sessoes/{sessao_id}/avaliacoes` | Registra a avaliação de um membro presente na sessão (`409` para quem não esteve). Corpo: `{"membro_id", "nota", "comentario"?}`. A média da sessão é refeita a cada avaliação. |

A escala que vale é a do clube dono da sessão — a API a descobre pela
própria sessão, sem pedir o clube.

**`"nota": null` registra que o membro cochilou** (`dorminhoco`). O campo
`nota` é obrigatório mesmo assim: como cada membro avalia cada sessão uma
vez só, esquecer o campo não pode transformar ninguém em dorminhoco por
engano — a API recusa com `422`. (Na CLI a convenção é omitir `--nota`,
porque ali a omissão é um gesto explícito de quem digita o comando.)

### Óscar

| Método e caminho | O que faz |
|---|---|
| `GET /clubes/{clube_id}/oscar/temporadas` | Lista as edições do Óscar do clube. |
| `POST /clubes/{clube_id}/oscar/temporadas` | Abre uma edição — uma por ano (`409` `temporada_oscar_duplicada`). Corpo opcional: `{"ano"?, "nome"?, "nomeacoes_por_categoria"?}`. Sem `ano`, usa o corrente; sem `nome`, `"Óscar do <clube> <ano>"`; sem `nomeacoes_por_categoria`, 5 (mínimo 2). |
| `POST /oscar/temporadas/{temporada_id}/avancar` | Leva a edição à fase seguinte (em preparação → aberta para indicações → em votação → apurada → encerrada). `409` `temporada_incompleta` se faltar algo: categorias, nomeações ou resultados. |
| `GET /oscar/temporadas/{temporada_id}` | Consulta uma edição. |
| `PUT /oscar/temporadas/{temporada_id}/data-evento` | Marca (ou remarca) o dia da cerimônia. Corpo: `{"data_evento": "AAAA-MM-DD"}`. `409` se a edição já estiver encerrada. |
| `GET /oscar/temporadas/{temporada_id}/categorias` | Lista as categorias da edição. |
| `POST /oscar/temporadas/{temporada_id}/categorias` | Define uma categoria. Corpo: `{"nome", "tipo"?: "fixa" \| "variavel", "descricao"?}`. O padrão é `variavel`. |
| `GET /oscar/categorias/{categoria_id}` | Consulta uma categoria. |
| `GET /oscar/categorias/{categoria_id}/nomeacoes` | Lista as nomeações da categoria. |
| `POST /oscar/categorias/{categoria_id}/nomeacoes` | Nomeia um filme. Corpo: `{"filme_id"}`. O filme precisa ter sido assistido pelo clube **dentro do ano da edição**. `409` fora da fase de indicações (`acao_fora_da_fase`) ou com a categoria completa (`categoria_completa`). |
| `GET /oscar/nomeacoes/{nomeacao_id}` | Consulta uma nomeação. |
| `POST /oscar/categorias/{categoria_id}/apuracao` | Apura a categoria e emite o troféu. Corpo: `{"nomeacao_vencedora_id", "membro_vencedor_id"?}`. |
| `GET /oscar/categorias/{categoria_id}/trofeu` | O troféu da categoria; `404` enquanto ela não tiver sido apurada. |

#### Como a apuração decide o vencedor

O mecanismo de apuração continua em aberto no produto, então a API não
inventa um: **quem chama informa qual nomeação o grupo escolheu**
(`nomeacao_vencedora_id`), e a API confere que ela concorre na categoria.
É o mesmo papel do `CriterioApuracaoInterativo` da CLI — o port
`CriterioApuracaoOscar` recebe aqui a implementação
`CriterioEscolhaInformada`, e trocá-la por um critério automático, quando
o clube decidir um, não exige mexer em domínio nem em aplicação.

O troféu vai para **quem indicou o filme vencedor**. Quando o filme veio
de uma sessão democracia (sem membro indicador), `membro_vencedor_id` é
obrigatório, com a escolha do grupo.

### Infraestrutura

| Método e caminho | O que faz |
|---|---|
| `GET /saude` | `{"status": "ok", "versao": "..."}` — para monitoramento. |

## Um ciclo completo

```bash
API=http://127.0.0.1:8000/api/v1
curl -s -X POST $API/clubes -H 'content-type: application/json' -d '{"nome": "Filmes e Cubos"}'
curl -s -X POST $API/clubes/<CLUBE>/membros -H 'content-type: application/json' -d '{"nome": "Iano"}'
curl -s -X POST $API/filmes -H 'content-type: application/json' -d '{"titulo": "Parasita", "ano_lancamento": 2019}'
curl -s -X POST $API/clubes/<CLUBE>/rodadas
curl -s -X POST $API/rodadas/<RODADA>/indicacoes -H 'content-type: application/json' \
     -d '{"membro_id": "<IANO>", "filme_id": "<PARASITA>"}'
curl -s -X POST $API/rodadas/<RODADA>/sorteios
curl -s -X POST $API/indicacoes/<INDICACAO>/sessao
curl -s -X POST $API/sessoes/<SESSAO>/avaliacoes -H 'content-type: application/json' \
     -d '{"membro_id": "<IANO>", "nota": 4.5}'
curl -s -X POST $API/rodadas/<RODADA>/encerrar
```
