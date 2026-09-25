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
   será decidida depois.
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
8. **Apuração por votação ponderada**, no lugar da escolha manual:
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

## Decisões complementares de 24/09/2026

Respostas do dono do produto às interpretações da lista anterior (as de
número 1, 3, 4, 6, 7 e 9 foram respondidas ou superadas aqui).

16. **Empate generalizado no 2º turno:** a votação por classificação é só
    entre os filmes empatados; os eliminados não voltam.
17. **Nomeações por categoria:** todas as categorias de uma edição têm o
    mesmo número de nomeações — 5 por padrão, editável ao abrir a edição.
18. **Membro desativado e votação:** durante uma votação ativa não é
    possível desativar um membro; se, por defeito, algum for desativado
    mesmo assim, o voto dele é desconsiderado.
19. **Média como fração:** a média guarda a soma e a quantidade das notas
    (soma ÷ quantidade), sem arredondar, e é exibida em estrelas — uma
    por inteiro, mais a fração restante com denominador de 2 a 10 (ex.:
    3,66 → ★★★⅔).
20. **Mesmo filme várias vezes na categoria:** continua permitido; uma
    categoria pode ser inteira sobre um único filme.

### Interpretações minhas, para confirmar

Pontos que as respostas não fecharam por completo; é assim que estou
implementando, salvo correção:

1. No 2º turno com apenas dois filmes, a 1ª e a 2ª opção cobrem os dois.
2. Empate parcial numa votação por classificação leva a um novo turno de
   votação dupla só com os empatados.
3. O membro escolhido pelo grupo (vitória democracia ou empate absoluto)
   precisa ser membro do clube (ativo ou não).
4. Como o mecanismo de apuração foi decidido, o port plugável
   `CriterioApuracaoOscar` e suas implementações (a interativa da CLI e a
   `CriterioEscolhaInformada` da API) deixam de existir; a contagem de
   votos vira regra do domínio.
5. **Mínimo de 2 nomeações por categoria** (decisão 17): a votação dupla
   pede duas opções distintas. Não há máximo. Com isso, a antiga
   interpretação "categoria com uma única nomeação vence sem votação"
   deixa de existir.
6. Nomear além do número da edição é recusado; passar para *em votação*
   exige que **toda categoria tenha exatamente esse número** de nomeações
   e que a edição tenha **ao menos uma categoria**.
7. **"Votação ativa"** (decisão 18) é a edição do Óscar do clube estar no
   estado *em votação*. Cadastrar ou reativar um membro nesse período
   continua permitido: ele passa a votar, e os turnos abertos esperam o
   voto dele.
8. **Vota-se em nomeações, não em filmes:** como o mesmo filme pode ser
   nomeado várias vezes na mesma categoria (decisão 20), cada escolha do
   voto aponta uma nomeação. As duas opções da votação dupla precisam ser
   nomeações diferentes (podem ser do mesmo filme).
9. **Sigilo do voto:** antes da apuração, as interfaces mostram só *quem*
   já votou; depois, a pontuação de cada nomeação. As cédulas
   individuais ficam guardadas (para relatórios), mas nenhuma interface
   as exibe — ver a questão em aberto 2.
10. **Estrelas com mais de 10 notas:** quando a fração exata tem
    denominador maior que 10, exibe-se a fração mais próxima com
    denominador até 10 (ex.: 34/11 = 3,09… → ★★★⅒); se ela arredondar
    para zero ou para um inteiro, só aparecem estrelas inteiras.
11. **Data do evento** pode ser definida ou trocada em qualquer estado da
    edição, menos *encerrada* ("nada muda", decisão 7).

## Questões ainda em aberto

1. **Implementação do módulo de histórico** (decisão 3): formatos de
   arquivo aceitos, como casar nomes de membros e títulos de filmes com
   os cadastrados, se sessões antigas pertencem a rodadas (e quais), e
   como o histórico convive com a regra de não repetir filmes.
2. **Sigilo do voto:** as cédulas individuais podem ser exibidas (a todos,
   só depois da apuração, ou nunca)? Hoje nenhuma interface as mostra
   (interpretação 9).

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

## Dívidas técnicas conhecidas

1. **Chaves estrangeiras não são verificadas pelo SQLite.** O esquema as
   declara, mas o SQLite só as aplica com `PRAGMA foreign_keys=ON`, que o
   projeto não liga. Ligar exige revisar testes de repositório que gravam
   entidades sem as "mães".
2. **Sem transação por caso de uso.** Cada repositório abre a sua. O
   middleware de escritas cobre o servidor HTTP; a CLI não precisa (um
   comando por processo). Vários processos servidores exigiriam uma Unit
   of Work (ADR 10).
3. **Verificações entre clubes incompletas.** Com mais de um clube, nada
   impede hoje que um membro de um clube indique na rodada de outro, e
   `IndicarFilmeParaCategoria` considera sessões de qualquer clube
   (contrariando a regra 8 do domínio, "assistido pelo clube"). Parte
   disso se resolve com as decisões 4 e 5; o restante está na Fase 5.
