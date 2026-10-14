# Pendências e decisões para revisão

Documento vivo do desenvolvimento das Fases 4 e 5 do [roadmap](ROADMAP.md).
Itens numerados para facilitar a resposta item a item. O caminho para
continuar o trabalho — em que ordem implementar o que está aqui — fica
na seção "Como continuar" do ROADMAP.

## Decisões do dono do produto em 24/09/2026 (a implementar)

Respostas dadas às questões levantadas durante a Fase 4. Nada disto está
implementado ainda, exceto onde indicado.

1. **Interface web renderizada no servidor** (Jinja2 + CSS próprio, sem
   SPA nem build de Node). *Em andamento.*
2. **Git:** um commit por etapa num branch local, sem push; o dono revisa
   e mescla em `main`. *Em prática.*
3. **Data das sessões:** o registro normal continua usando a data do dia.
   Sessões passadas ganham um **módulo específico de histórico**, que
   também importa em massa arquivos de fontes diversas. Nesta etapa, só o
   **contrato** do módulo (ports e estruturas de dados); a implementação
   será decidida depois. *Contrato criado:*
   `application/ports/leitor_de_historico.py`.
4. **Só quem estava presente avalia** uma sessão (nota ou dorminhoco).
5. **Filme não se repete no clube:** é proibido indicar um filme que o
   clube já assistiu — inclusive em sessões democracia — ou que já está
   indicado e ainda não foi assistido. Consequência: cada filme é
   assistido no máximo uma vez por clube, e a nomeação ao Óscar sempre
   tem um indicador inequívoco.
6. **Uma edição do Óscar por clube por ano.**
7. **Os estados da temporada valem**, com um estado novo, *em votação*:
   em preparação (define categorias) → aberta para indicações (nomeia
   filmes; ainda aceita categorias) → **em votação** (membros votam e as
   categorias são apuradas; nomeações travadas) → apurada (só quando
   todas as categorias tiverem resultado) → encerrada (nada muda).
   Avanço manual, um passo por vez.
8. **Apuração por votação ponderada**, no lugar da escolha manual (os
   itens 2 e 3 foram substituídos pela decisão 25, e o item 6 ganhou
   a forma da decisão 29):
   1. cada membro ativo do clube dá, por categoria, uma 1ª opção
      (**2 pontos**) e uma 2ª opção (**1 ponto**); votar no filme que o
      próprio membro indicou é permitido — os pesos existem justamente
      para que "todo mundo vota em si mesmo" não gere empate geral;
   2. um turno só é apurado quando **todos os membros ativos** votaram;
   3. o voto pode ser **alterado até a apuração** do turno (a avaliação
      de uma sessão continua definitiva);
   4. empate no topo entre parte dos filmes (2, 3 ou mais, mas não todos)
      → **2º turno** só com os empatados, mesma lógica de pesos;
   5. empate generalizado (todos os filmes do turno com a mesma
      pontuação) → **votação por classificação**: cada membro ordena os X
      filmes, com pesos X, X−1, …, 1;
   6. se ainda assim todos empatarem → **empate absoluto**: nenhum filme
      vence, e o troféu vai para um membro escolhido pelo grupo — como já
      acontece quando vence um filme democracia.
9. **Funcionalidades pequenas aprovadas:** reativar membro; definir a
   data do evento do Óscar; **média das notas** por sessão (sem
   dorminhocos), **armazenada** — como fração, exibida em estrelas
   (decisão 19, que substituiu a "1 casa decimal" original).
10. **Duração do filme** (em minutos), para saber o tempo assistido no ano
    e quem indica filmes mais longos.
11. **Dados para relatórios futuros:** o sistema deve agregar o máximo de
    informação possível para, no futuro, cruzar dados em relatórios,
    gráficos e estatísticas (duração, notas recebidas pelas indicações
    de cada membro, notas dadas por filme...). Planejado como Fase 6.
12. **Fase 5 — login individual** por membro, com contas criadas por
    **convite com código**: o admin gera o código, o membro cria a
    própria senha; quem cria o clube é o primeiro admin.
13. **Fase 5 — permissões:** administradores gerenciam clube, membros,
    rodadas e Óscar; membros comuns indicam, avaliam e votam **só em
    nome próprio**.
14. **Fase 5 — integração com a TMDB:** sim, desligada até haver uma
    chave configurada.
15. **Deploy:** só local por enquanto, mas o sistema deve continuar fácil
    de levar para um servidor ou para a nuvem — a decisão vai mudar.
    *Mudou em 13/10: decisão 34.*

## Decisões complementares de 24/09/2026

Respostas do dono do produto às interpretações da lista anterior (as de
número 1, 3, 4, 6, 7 e 9 foram respondidas ou superadas aqui).

16. **Empate generalizado no 2º turno:** a votação por classificação é só
    entre os filmes empatados; os eliminados não voltam.
17. **Nomeações por categoria:** todas as categorias de uma edição têm o
    mesmo número de nomeações — 5 por padrão, editável ao abrir a edição.
18. ~~**Membro desativado e votação:** durante uma votação ativa não é
    possível desativar um membro; se, por defeito, algum for desativado
    mesmo assim, o voto dele é desconsiderado.~~ Revogada pelo dono em
    25/09 (decisão 23): a votação tem eleitores definidos, e mexer nos
    membros não a afeta. Nunca chegou a ser implementada.
19. **Média como fração:** a média guarda a soma e a quantidade das notas
    (soma ÷ quantidade), sem arredondar, e é exibida em estrelas — uma
    por inteiro, mais a fração restante com denominador de 2 a 10 (ex.:
    3,66 → ★★★⅔).
20. **Mesmo filme várias vezes na categoria:** continua permitido; uma
    categoria pode ser inteira sobre um único filme.

## Decisões do dono do produto em 25/09/2026

Respostas às interpretações de 24/09 e às perguntas feitas ao redesenhar
a votação. O sistema existe para que o clube brinque no mundo real: ele
recolhe os votos, mas quem conhece o resultado é só quem monta a
cerimônia.

21. **Nomeações por categoria:** no mínimo 2 (a votação dupla pede duas
    opções), sem máximo; 5 por padrão. O número é o mesmo em todas as
    categorias e é definido junto das demais configurações da edição, ao
    abri-la. *Já implementado.*
22. **Ir à votação** exige ao menos uma categoria, cada uma com exatamente
    o número de nomeações da edição; nomear além dele é recusado. *Já
    implementado.*
23. **A votação é um evento com eleitores definidos:** começa quando a
    edição entra *em votação* ("votação ativa" é a edição estar nessa
    fase) e habilita só os membros cadastrados e ativos naquele momento.
    Cadastrar, desativar ou reativar membros continua permitido durante a
    votação, mas não muda os eleitores: quem foi desativado continua
    votando, e quem entrou ou voltou depois não vota. Substitui a
    decisão 18.
24. **Vota-se em nomeações, não em filmes:** as duas opções da votação
    dupla precisam ser nomeações diferentes, mas podem ser do mesmo filme.
25. **Cédula e confirmação:** o eleitor vota em todas as categorias do
    turno e então confirma a cédula. Até confirmar, pode alterar os votos
    à vontade; depois, nada muda. Quando todos os eleitores confirmam, o
    turno se encerra. Substitui os itens 2 e 3 da decisão 8.
26. **Voto secreto:** as telas mostram só quem já votou; as cédulas ficam
    guardadas e nunca aparecem. Nenhuma tela mostra o placar.
27. **Apuração fora do sistema:** terminada a votação, quem administra
    informa um e-mail, sem ver o resultado, e o sistema envia para ele o
    **placar** — a pontuação de cada nomeação, no corpo do e-mail, nunca
    as cédulas. Quem recebe monta as apresentações da cerimônia. O envio
    pode ser repetido, para o mesmo ou outro endereço, até a edição ser
    encerrada.
28. **Desempates dentro do sistema:** ao encerrar um turno, o sistema
    detecta sozinho os empates no topo, sem mostrá-los, e abre um novo
    turno só com as nomeações empatadas, pelas regras das decisões 8.4,
    8.5 e 16. O placar só pode ser enviado quando não restar empate a
    desfazer.
29. **Vencedores registrados depois do evento:** quem administra informa
    o vencedor de cada categoria — a nomeação (o troféu vai para quem a
    indicou) ou, numa vitória de filme democracia ou num empate absoluto,
    o membro escolhido pelo grupo. O histórico de troféus continua no
    sistema, e a edição fica *apurada* quando toda categoria tiver
    vencedor.
30. **Estrelas com mais de 10 notas:** a fração mostrada é a mais próxima
    com denominador até 10; as frações sem caractere próprio aparecem
    compostas, como ²⁄₇. *Já implementado.*
31. **Data do evento** pode mudar em qualquer fase, menos depois de a
    edição ser encerrada. *Já implementado.*
32. **A duração é o único dado do filme editável** depois do cadastro.
    *Já implementado.*
33. **Reativar um membro que já está ativo** não deve aparecer como
    opção nas telas, mas, se acontecer (latência, clique duplo), também
    não é erro. *Já implementado* (a regra das telas vale para a web).

## Decisões do dono do produto em 13/10/2026

Pedido: terminar o trabalho e publicar a web na Vercel, a partir do
repositório do GitHub.

34. **Produção na Vercel com Postgres da Neon:** a Vercel não guarda
    arquivos entre execuções, então o banco da produção é um Postgres da
    Neon (integração oficial da Vercel, plano gratuito). O SQLite continua
    para o uso local e para os testes.
35. **Senha única do clube** protege o site e a API publicados,
    provisoriamente, até o login individual da Fase 5. Enquanto isso, quem
    entra pode agir por qualquer membro.
36. **Ordem do trabalho:** primeiro a web na Vercel (a base do deploy e as
    páginas do dia a dia do clube); depois o placar por e-mail, os
    vencedores e as telas do Óscar.
37. **Git:** push do branch de trabalho ao fim de cada etapa (a Vercel gera
    uma prévia de cada push); merge e push da `main`, que é a produção,
    só quando o dono pedir.

### Interpretações para confirmar

As interpretações 4 a 11 de 24/09 foram respondidas pelas decisões 21 a
33 (a 4 virou a decisão técnica 24). Continuam valendo, salvo correção:

1. No 2º turno com apenas dois filmes, a 1ª e a 2ª opção cobrem os dois.
2. Empate parcial numa votação por classificação leva a um novo turno de
   votação dupla só com os empatados.
3. O membro escolhido pelo grupo (vitória democracia ou empate absoluto)
   precisa ser membro do clube (ativo ou não).

Novas, do redesenho de 25/09:

12. **Os mesmos eleitores em todos os turnos:** o 2º turno (e os
    seguintes) é parte da mesma votação; cada eleitor preenche uma cédula
    nova só com as categorias empatadas e confirma de novo.
13. **Andamento de cada eleitor à mostra:** além de quem confirmou, as
    telas mostram em quantas categorias do turno cada eleitor já votou —
    nunca em quê.
14. **Registro do vencedor** só depois de terminada a votação, com a
    edição ainda *em votação*, e sem conferência com o placar: a apuração
    é de quem recebeu o e-mail. Uma vez registrado, o vencedor da
    categoria não muda (como a antiga apuração).
15. **O e-mail traz o placar de cada turno** da categoria (1º, 2º...), em
    ordem de pontos, e assinala o empate absoluto e as nomeações de filme
    democracia (sem indicador: o grupo escolhe quem leva o troféu).

## Questões ainda em aberto

1. **Implementação do módulo de histórico** (decisão 3): formatos de
   arquivo aceitos, como casar nomes de membros e títulos de filmes com
   os cadastrados, se sessões antigas pertencem a rodadas (e quais), e
   como o histórico convive com a regra de não repetir filmes.
2. ~~**Sigilo do voto**~~ — respondida pela decisão 26: as cédulas nunca
   aparecem.
3. **Eleitor que não confirma:** se alguém da lista de eleitores nunca
   confirmar a cédula (por exemplo, saiu do clube durante a votação), o
   turno não se encerra. Por ora a votação espera todos (decisão do
   dono); uma saída será decidida se o caso acontecer.
4. **Ligar a CI do GitHub** (pede uma ação do dono): a definição está
   pronta em `docs/ci/testes.yml`, mas o GitHub só aceita arquivos em
   `.github/workflows/` de um token com o escopo `workflow`, que o desta
   máquina não tem. Basta rodar `gh auth refresh -h github.com -s
   workflow` (abre o navegador) e mover o arquivo.

## Decisões técnicas tomadas sem consulta

1. **Branch local `roadmap/fases-4-e-5`**, um commit por etapa, sem push
   (confirmado depois pelo dono — decisão 2).
2. **`ruff format`** aplicado a dez arquivos fora do padrão e **fins de
   linha normalizados para LF** (`.gitattributes`); nenhuma mudança de
   conteúdo.
3. **Composition root promovido a `adapters/composicao.py`** (ADR 8).
4. **API com FastAPI, em `/api/v1`, erros em RFC 9457** com um campo
   `codigo` estável (ADR 9). Classificação dos erros de domínio: 404
   (entidade não encontrada), 409 (conflito com o estado), 422 (dado
   inválido), 500 (sorteador devolveu candidato inválido) — em
   `adapters/interfaces/erros_http.py`, compartilhado com a web.
5. **`nota` obrigatória na API**, aceitando `null` para dorminhoco: como
   cada membro avalia uma vez só, esquecer o campo não pode registrar
   ninguém como dorminhoco. Na CLI a convenção continua sendo omitir
   `--nota`.
6. **Escala da avaliação deduzida da sessão na API** (clube dono da
   rodada da indicação), em vez de pedir o clube.
7. **Escritas HTTP enfileiradas no processo** (`EscritasEmFila`, ADR 10)
   em vez de uma Unit of Work transacional.
8. **Servidor ouve só em `127.0.0.1` por padrão**, porque ainda não há
   autenticação.
9. **`httpx2` como dependência de desenvolvimento**: é o cliente que o
   Starlette 1.x espera no `TestClient`.
10. **Migrações de esquema com Alembic** (ADR 11), com configuração
    programática e revisão inicial igual ao esquema das Fases 2 e 3;
    bancos antigos são reconhecidos e migrados sem perda de dados.
11. **Uma revisão do Alembic por mudança de esquema**, no mesmo commit da
    regra que a pede (0002: duração dos filmes), em vez de uma revisão
    única para toda a revisão de regras: cada commit fica completo e
    reversível por si.
12. **Duração corrigível depois do cadastro** (`DefinirDuracaoFilme`,
    `filme duracao`, `PUT /filmes/{id}/duracao`): sem isso, os filmes já
    cadastrados nunca teriam duração, e a soma do tempo assistido no ano
    (decisão 10) ficaria incompleta. É o único dado do filme editável por
    enquanto.
13. **`AcaoForaDaFaseError`** (409) é o erro único para "esta fase da
    edição do Óscar não permite esta ação" — hoje, mudar a data do evento
    de uma edição encerrada; na etapa do ciclo da temporada, as demais
    restrições por fase.
14. **Reativar é idempotente**, como desativar: reativar um membro ativo
    não é erro.
15. **Estrelas num módulo compartilhado** (`adapters/interfaces/estrelas.py`):
    a regra de exibição é do produto, então CLI, API e web a usam do
    mesmo lugar. As frações sem caractere próprio no Unicode (2/7, 5/9,
    7/10...) são compostas com algarismos sobrescritos e subscritos em
    torno da barra de fração: `²⁄₇`.
16. **Média refeita a partir de todas as avaliações** a cada avaliação
    nova, em vez de somar só a última: se uma gravação falhar no meio, a
    próxima avaliação corrige a média.
17. **Sessão sem notas guarda soma 0 e quantidade 0** (colunas não
    anuláveis), e o domínio as lê como "sem média"; a API expõe a soma, a
    quantidade e as estrelas, sem nenhum valor arredondado.
18. **`AvaliarFilme` deduz o clube da própria sessão**, e o `--clube-id`
    saiu de `avaliacao registrar`: informar o clube permitia avaliar com a
    escala de outro clube.
19. **"Filme já passou pelo clube" = ter qualquer indicação no clube**,
    em qualquer situação: como a rodada só se encerra com tudo assistido,
    toda indicação do clube ou foi assistida ou está pendente na rodada
    aberta. A regra mora num módulo de apoio dos casos de uso
    (`application/use_cases/_filme_inedito.py`), usado pela indicação
    normal e pela democracia, com mensagens distintas para "já assistido"
    e "já indicado".
20. **"Uma edição por ano" só no caso de uso**, sem restrição única no
    banco: um banco antigo com duas edições no mesmo ano faria a migração
    falhar. O mesmo vale para o número de nomeações, conferido na
    nomeação e no avanço.
21. **`TemporadaIncompletaError`** (409) é o erro único do avanço de fase
    que esbarra em pendências (sem categorias, nomeações faltando,
    categorias sem resultado); a mensagem lista o que falta, ex.:
    "Pior criança (1/5)".
22. **A apuração ainda usa o critério antigo** (escolha informada por
    quem opera) e ainda não é restrita à fase *em votação*: a etapa da
    votação a substitui por inteiro, com as suas restrições. Até lá, a
    passagem para *apurada* conta os troféus emitidos por ela.
23. **O contrato do histórico cobre só a leitura** (`LeitorDeHistorico`):
    um adapter por formato, que devolve os registros com os nomes como
    vieram na fonte e relata as linhas ilegíveis sem parar. Casar nomes
    com cadastros, escolher rodadas e gravar dependem da questão em
    aberto 1 e serão casos de uso próprios. O conteúdo chega em bytes para
    servir à CLI (arquivo local) e à web (envio de arquivo).
24. **Fim do critério de apuração plugável:** com a contagem de votos
    como regra do domínio (decisão 28) e o vencedor informado por quem
    administra (decisão 29), o port `CriterioApuracaoOscar` e suas
    implementações (a interativa da CLI e a `CriterioEscolhaInformada` da
    API) deixam de existir. *A implementar na etapa dos vencedores.*
25. **Ir à votação exige ao menos um membro ativo**
    (`TemporadaIncompletaError`): sem eleitores, a votação nunca
    terminaria.
26. **O turno atual de cada categoria é o seu turno aberto:** quando um
    turno se encerra, todos os abertos são apurados juntos, então "aberto"
    e "do turno atual da votação" coincidem, sem guardar em cada categoria
    qual turno vale.
27. **A situação da votação é montada num módulo compartilhado**
    (`adapters/interfaces/situacao_da_votacao.py`), para que CLI, API e
    web mostrem o mesmo — quem confirmou e em quantas categorias cada
    eleitor votou (interpretação 13) — e nenhuma mostre mais.
28. **A API devolve a cédula sem as escolhas** (só as categorias votadas e
    se foi confirmada): nem quem acabou de votar recebe o voto de volta.
29. **Na CLI, o voto aceita a posição da candidata** (a numeração de
    `oscar votacao`) ou o id da nomeação: colar dois UUIDs por voto seria
    ruído.
30. **Edições já em votação antes da revisão 0005** ganham a sua votação
    na migração, com os membros ativos de agora como eleitores — a melhor
    aproximação de "ativos quando a votação começou". Categorias que já
    têm troféu (da apuração antiga) ou menos de duas nomeações não abrem
    turno.
31. **Sem login, qualquer um opera o voto de qualquer eleitor** pela CLI
    ou pela API, como já acontece com as avaliações; "votar só em nome
    próprio" chega com o login da Fase 5 (decisão 13).
32. **Persistência portável entre SQLite e Postgres** (decisão 34): o
    upsert usa o `INSERT ... ON CONFLICT` do dialeto da conexão, e toda
    listagem tem ordem explícita — nome, título, ano, data ou, onde a
    ordem é a de criação (indicações, avaliações, categorias e nomeações,
    cuja ordem é a da cédula), uma coluna `ordem` gravada pelo repositório
    (revisão 0006; nos bancos antigos, vem do `rowid`). O SQLite devolvia
    as linhas na ordem de inserção; o Postgres não garante ordem sem
    `ORDER BY`.
33. **O pacote continua `adapters/persistence/sqlite/`**, embora sirva
    também ao Postgres: renomeá-lo mexeria em dezenas de arquivos sem
    mudar comportamento.
34. **Migrações no Postgres com trava consultiva**
    (`pg_advisory_xact_lock`): na Vercel, várias instâncias podem subir
    juntas, e cada uma migra ao abrir o banco.
35. **Pool de conexões com `pool_pre_ping` e `pool_recycle`** no Postgres:
    a instância da função pode ficar congelada, e o servidor fecha as
    conexões paradas.
36. **Os testes da API rodam também contra o Postgres** quando
    `FILMES_E_CUBOS_TESTE_POSTGRES` aponta um servidor (um banco novo por
    teste); a definição de CI em `docs/ci/testes.yml` sobe um Postgres
    para isso (ligá-la é a pendência 4 abaixo). Os testes de
    repositório ficam no SQLite: gravam entidades sem as "mães", e o
    Postgres confere as chaves estrangeiras (ver a dívida técnica 1).
37. **Entrada da Vercel em `app.py`, na raiz**, com o caminho de `src/`
    acrescentado ali, para não depender de como a Vercel instala o
    pacote; `.vercelignore` deixa testes e documentação fora da função.
38. **`DATABASE_URL` vale para o servidor e para a CLI** (`--db-url`), no
    lugar do arquivo SQLite: o nome é o que a integração da Neon define,
    e assim a CLI local também consegue administrar a produção.
39. **A senha do clube vale para o site e para a API** (decisão 35), num
    middleware ASGI compartilhado (`adapters/interfaces/acesso.py`): no
    navegador, a página `/entrar` marca a sessão (cookie assinado,
    `HttpOnly`, `SameSite=Lax` — o que já barra formulários forjados por
    outros sites —, `Secure` na Vercel); programas mandam
    `Authorization: Bearer <senha>`. Ficam livres só a entrada, os
    arquivos estáticos e `/api/v1/saude`. A comparação é em tempo
    constante.
40. **A chave que assina a sessão vem da senha**, a menos que
    `FILMES_E_CUBOS_CHAVE_SECRETA` seja definida: é a mesma em todas as
    instâncias da Vercel e muda com a senha — trocar a senha desconecta
    todo mundo.
41. **Na Vercel, sem senha o site não abre** (503 com a instrução do que
    configurar): esquecer a variável não pode deixar o clube aberto na
    internet. Localmente, sem senha, nada muda.
42. **A web virou o app raiz** e a API é montada dentro dela, em
    `/api/v1`; a raiz, que antes redirecionava à documentação da API,
    agora é a página inicial.
43. **Visual próprio, sem framework de CSS** (um `estilo.css` com tema
    escuro automático): nada de build nem de dependência de terceiros
    para o que a página precisa.
44. **Os testes da web rodam também contra o Postgres**, como os da API.
45. **Cada página confere que o que vem no endereço é do clube dela**
    (`web/escopo.py`): membro, rodada, indicação ou sessão de outro clube
    vira 404 (ou aviso, numa ação) — a web já respeita a separação entre
    clubes que a dívida técnica 3 cobra das demais interfaces.
46. **As ações da rodada aberta moram no painel** (indicar, democracia,
    sortear, encerrar, abrir a próxima), e a sessão é registrada a partir
    da indicação, com os membros ativos já marcados como presentes — a
    presença padrão da CLI e da API.
47. **Os formulários de indicação listam o catálogo inteiro:** filme que
    já passou pelo clube é recusado com a mensagem da regra (decisão 5).
    Esconder esses filmes da lista exigiria percorrer todas as rodadas a
    cada abertura do painel; fica para quando o catálogo crescer.
48. **O texto do placar é montado na aplicação** (`_placar_oscar.py`), e
    não num adapter: é o documento que o produto envia, e o port de
    e-mail fica genérico (ADR 14).
49. **O servidor de e-mail é configurado por `FILMES_E_CUBOS_SMTP_*`**
    (servidor, porta, segurança, usuário, senha, remetente). Sem servidor,
    o envio é recusado com instrução (503); recusa ou silêncio do servidor
    viram 502. Os testes do adapter conversam com um servidor SMTP mínimo
    que sobe dentro do próprio teste, sem dependência nova.
50. **O placar só pode ser reenviado até a edição ser encerrada**
    (decisão 27): `AcaoForaDaFaseError` depois disso, e também antes de a
    edição ir à votação.

## Dívidas técnicas conhecidas

1. **Chaves estrangeiras não são verificadas pelo SQLite.** O esquema as
   declara, mas o SQLite só as aplica com `PRAGMA foreign_keys=ON`, que o
   projeto não liga. Ligar exige revisar testes de repositório que gravam
   entidades sem as "mães". No Postgres da produção elas valem — os testes
   da API, que rodam lá também, confirmam que o programa as respeita.
2. **Sem transação por caso de uso.** Cada repositório abre a sua. O
   middleware de escritas cobre o servidor HTTP; a CLI não precisa (um
   comando por processo). Vários processos servidores exigiriam uma Unit
   of Work (ADR 10).
3. **Verificações entre clubes incompletas.** Com mais de um clube, nada
   impede hoje que um membro de um clube indique na rodada de outro.
   Já resolvido: a avaliação usa a escala do clube da sessão, a nomeação
   ao Óscar só considera sessões do próprio clube e a regra de filme
   repetido olha só o clube da rodada. O restante está na Fase 5.
