# Pendências e decisões para revisão

Documento vivo, mantido durante o desenvolvimento autônomo das Fases 4 e
5 do [roadmap](ROADMAP.md). Reúne três coisas, numeradas para facilitar
a resposta item a item:

- **Questões de negócio em aberto** — regras que o código não pode
  decidir sozinho. Nada aqui foi implementado por suposição: o
  comportamento atual continua o que já era, e cada item diz qual é.
- **Decisões técnicas tomadas sem consulta** — escolhas que não mexem em
  regra de negócio, registradas para revisão (e reversão, se for o caso).
- **Dívidas técnicas conhecidas** — limitações aceitas conscientemente,
  com o caminho de saída.

## Questões de negócio em aberto

1. **Mecanismo de apuração do Óscar** (já estava em aberto). Votação dos
   membros? Média das notas? Júri? *Hoje:* quem opera escolhe a vencedora
   — no terminal (CLI) ou na requisição (API). Qualquer mecanismo
   automático entra como um novo adapter de `CriterioApuracaoOscar`.
2. **Sessões com data no passado.** `RegistrarSessaoExibicao` sempre usa a
   data de hoje. Não dá para registrar uma sessão esquecida da semana
   passada, nem importar o histórico do clube (sessões desde a pandemia).
   Como a data da sessão decide em qual Óscar o filme concorre (regra 8),
   isso é regra de negócio: pode registrar com data retroativa? Até
   quando? Quem pode?
3. **Mesmo filme assistido duas vezes no mesmo ano.** Se dois membros
   indicaram o mesmo filme em rodadas diferentes do mesmo ano, a
   nomeação ao Óscar herda o indicador da primeira indicação que o banco
   devolver — na prática, arbitrário. Quem deve levar o troféu nesse caso?
4. **Quem pode avaliar uma sessão.** `AvaliarFilme` não confere se o
   membro estava presente na sessão nem se pertence ao clube da sessão.
   Membro ausente pode dar nota (por exemplo, depois de ver o filme em
   casa)?
5. **Ciclo de vida da temporada do Óscar.** A entidade `TemporadaOscar`
   tem os estados `em_preparacao` → `aberta_para_indicacoes` → `apurada`
   → `encerrada` e um `data_evento`, mas nenhum caso de uso os altera:
   toda temporada fica eternamente `em_preparacao`, e nomear ou apurar
   não depende do estado. Os estados devem restringir as ações (ex.: só
   nomear com a temporada aberta para indicações)? Quem avança o estado?
6. **Uma temporada por ano?** `AbrirTemporadaOscar` aceita duas edições
   do mesmo clube no mesmo ano (o caso de uso diz "normalmente uma por
   ano civil"). Deve recusar?
7. **Nomeação repetida.** O mesmo filme pode ser nomeado duas vezes na
   mesma categoria. Deve recusar?
8. **Reativar membro.** A entidade `Membro` tem `reativar()`, mas não
   existe caso de uso para isso — um membro desativado por engano não
   volta. Criar o caso de uso `ReativarMembro`?
9. **Média das notas.** O domínio já define que avaliações `dorminhoco`
   ficam fora de qualquer média, mas nenhuma média é calculada ou
   exibida. Exibir a média por sessão/filme? Com quantas casas decimais?

## Decisões técnicas tomadas sem consulta

1. **Trabalho num branch local, com um commit por etapa, sem push.** O
   branch `roadmap/fases-4-e-5` sai de `main`; revisar, mesclar ou
   descartar fica a seu critério.
2. **`ruff format` aplicado** a dez arquivos que estavam fora do padrão,
   e **fins de linha normalizados para LF** (`.gitattributes`) — oito
   arquivos estavam versionados com CRLF. Nenhuma mudança de conteúdo.
3. **Composition root promovido a `adapters/composicao.py`**, e o
   critério de apuração do Óscar passou a ser escolhido por interface
   (ADR 8).
4. **API com FastAPI, em `/api/v1`, erros em RFC 9457** com um campo
   `codigo` estável (ADR 9). Classificação dos erros de domínio: 404
   (entidade não encontrada), 409 (conflito com o estado: rodada já
   aberta, indicação duplicada, rodada lotada, membro inativo...), 422
   (dado inválido: nome em branco, nota fora da escala, filme não
   assistido no ano...), 500 (sorteador devolveu candidato inválido).
5. **`nota` obrigatória na API**, aceitando `null` para dorminhoco: como
   cada membro avalia uma vez só, esquecer o campo não pode registrar
   ninguém como dorminhoco por engano. Na CLI a convenção continua sendo
   omitir `--nota`.
6. **Escala da avaliação deduzida da sessão na API** (clube dono da
   rodada da indicação), em vez de pedir o clube ou assumir o único
   cadastrado.
7. **Escritas HTTP enfileiradas no processo** (`EscritasEmFila`, ADR 10)
   em vez de uma Unit of Work transacional.
8. **Servidor ouve só em `127.0.0.1` por padrão**, porque ainda não há
   autenticação.
9. **`httpx2` como dependência de desenvolvimento**: é o cliente que o
   Starlette 1.x espera no `TestClient` (o `httpx` clássico gera aviso
   de depreciação).

## Dívidas técnicas conhecidas

1. **Chaves estrangeiras não são verificadas pelo SQLite.** O esquema as
   declara, mas o SQLite só as aplica com `PRAGMA foreign_keys=ON`, que o
   projeto não liga. Hoje dá para, por exemplo, apurar um troféu para um
   `membro_vencedor_id` inexistente. Ligar o pragma exige revisar testes
   de repositório que gravam entidades sem as "mães".
2. **Sem transação por caso de uso.** Cada repositório abre a sua. O
   middleware de escritas cobre o servidor HTTP; a CLI não precisa (um
   comando por processo). Vários processos servidores exigiriam uma Unit
   of Work (ADR 10).
3. **Sem migrações de esquema.** `metadata.create_all` cria tabelas
   novas, mas não altera as existentes. A primeira mudança numa tabela já
   em uso vai exigir uma ferramenta de migração (ex.: Alembic).
