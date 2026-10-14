# FilmesECodes

Software de gestão para o clube de cinema **Filmes e Cubos**.

## O clube

O "Filmes e Cubos" é um clube de cinema com 5 membros fixos que assistem a
um filme por semana. Toda semana cada membro indica um filme; um dos
filmes indicados é sorteado para a sessão daquela semana. O ciclo (uma
"rodada") só se encerra quando as 5 indicações da rodada tiverem sido
sorteadas e assistidas — aí uma nova rodada de indicações começa.

Depois de cada sessão, todos os membros dão uma nota ao filme assistido,
em uma escala de 0,5 a 5 estrelas. Essas notas são guardadas ao longo do
ano para alimentar o **"Óscar do Filmes e Cubos"**: um evento anual com
categorias de premiação, algumas fixas e outras variáveis de ano para
ano (e via de regra bem irreverentes — "Melhor veículo", "Pior criança",
"Personagem mais detestável" etc.). O troféu de cada categoria é entregue
ao membro que indicou o filme premiado, não a quem "atua" na categoria.

O nome do clube vem de uma brincadeira: durante a pandemia o grupo jogava
um jogo de blocos (cubos) online, até migrar para sessões de cinema — e
"Filmes e Cubos" pegou. Todas as redes sociais, grupos e nomes do clube
remetem a essa origem (por exemplo, este próprio projeto, "FilmesECodes").

## O que é este projeto

Este repositório é o software de apoio ao clube: cadastro de membros e
filmes, controle de rodadas e sorteios, registro de sessões e notas, e
apuração do Óscar anual. É um projeto pessoal, mas conduzido com rigor
profissional — serve como peça de portfólio e é desenhado para,
eventualmente, evoluir para uma versão comercializável (multi-clube).

**Status atual:** Fases 1, 2 e 3 do roadmap **concluídas e testadas**, e
a Fase 4 em andamento — o sistema é utilizável de ponta a ponta pela
linha de comando e por uma API HTTP. Ver
[docs/ROADMAP.md](docs/ROADMAP.md) para o histórico completo.

- ✅ **Fase 1** — núcleo de domínio (12 entidades, 6 value objects) e
  15 casos de uso, em `src/filmes_e_cubos/domain/` e
  `src/filmes_e_cubos/application/`.
- ✅ **Fase 2** — persistência SQLite via SQLAlchemy Core, em
  `src/filmes_e_cubos/adapters/persistence/sqlite/` (12 repositórios) e
  `src/filmes_e_cubos/adapters/servicos/` (relógio e sorteador reais).
- ✅ **Fase 3** — CLI com Typer, em
  `src/filmes_e_cubos/adapters/interfaces/cli/` (8 grupos de comando).
- 🚧 **Fase 4** — ✅ API HTTP com FastAPI, em
  `src/filmes_e_cubos/adapters/interfaces/api/`; ✅ migrações de esquema
  com Alembic; 🚧 interface web (módulos de apoio prontos, páginas a
  seguir).
- ⏭️ **Próximo passo**: a revisão de regras decidida em 24/09/2026
  (votação ponderada no Óscar, só presentes avaliam, filme não se repete
  no clube...) — ver "Como continuar" em
  [docs/ROADMAP.md](docs/ROADMAP.md) e as decisões em
  [docs/PENDENCIAS.md](docs/PENDENCIAS.md).

Suíte de testes verde: 379 testes (`uv run pytest`), `uv run mypy src`
(modo estrito) limpo em 134 arquivos e `uv run ruff check .` sem
violações.

## Uso

```bash
uv run filmes-e-cubos --help
```

A referência completa dos comandos, com as convenções da interface, está
em [docs/CLI.md](docs/CLI.md). Um ciclo típico do clube:

```bash
filmes-e-cubos clube criar "Filmes e Cubos"
filmes-e-cubos membro cadastrar "Iano"
filmes-e-cubos filme cadastrar "Parasita" --ano 2019
filmes-e-cubos rodada abrir
filmes-e-cubos indicacao indicar --membro-id <MEMBRO> --filme-id <FILME>
filmes-e-cubos indicacao sortear
filmes-e-cubos sessao registrar <INDICACAO>
filmes-e-cubos avaliacao registrar --sessao-id <SESSAO> --membro-id <MEMBRO> --nota 4,5
filmes-e-cubos rodada encerrar
```

Os dados ficam em um arquivo SQLite (`filmes_e_cubos.db` no diretório
atual, por padrão; configurável com `--db-path` ou a variável de ambiente
`FILMES_E_CUBOS_DB`).

### Web e API HTTP

```bash
uv run filmes-e-cubos-servidor          # site em http://127.0.0.1:8000
                                        # API em http://127.0.0.1:8000/api/v1/docs
```

O servidor usa o mesmo banco da CLI. As páginas estão descritas em
[docs/WEB.md](docs/WEB.md); a referência dos recursos e das convenções da
API (incluindo o formato de erro, RFC 9457), em [docs/API.md](docs/API.md).
Com `FILMES_E_CUBOS_SENHA` definida, site e API pedem a senha do clube;
sem ela, nada é protegido — por isso o padrão é ouvir só na própria
máquina.

## Publicando na Vercel

O repositório já está pronto para a [Vercel](https://vercel.com): o
`app.py` da raiz entrega o app completo, e a Vercel instala as
dependências a partir do `pyproject.toml` e do `uv.lock`.

1. Na Vercel, **Add New → Project** e importe este repositório do GitHub.
   Nenhuma configuração de build é necessária.
2. Em **Storage**, crie um banco **Neon (Postgres)** e conecte-o ao
   projeto. A integração define `DATABASE_URL`, e as tabelas são criadas
   sozinhas no primeiro acesso (migrações do Alembic). Vale ativar, na
   integração, um banco separado para cada prévia, para que as prévias
   não mexam nos dados da produção.
3. Faça o deploy. A `main` vira a produção; cada push em outro branch
   gera uma prévia.

| Variável | Obrigatória | O que é |
|---|---|---|
| `DATABASE_URL` | sim | URL do Postgres (a integração da Neon define). |
| `FILMES_E_CUBOS_SENHA` | sim | A senha do clube, pedida para entrar no site e para usar a API (`Authorization: Bearer <senha>`). Sem ela, o site não abre na Vercel. |
| `FILMES_E_CUBOS_CHAVE_SECRETA` | não | Chave que assina o cookie da sessão. Sem ela, uma é derivada da senha — trocar a senha desconecta todo mundo. |

Sem `DATABASE_URL`, o app usa um arquivo SQLite — o que só serve
localmente: na Vercel, o arquivo sumiria a cada reinício. A mesma
variável (ou `--db-url`) aponta a CLI para o banco da produção.

## Desenvolvimento

O projeto é gerenciado com [uv](https://docs.astral.sh/uv/).

```bash
uv sync --dev        # instala dependências (runtime + dev)
uv run pytest        # roda a suíte de testes
uv run mypy src      # checagem estática de tipos
uv run ruff check .  # lint
```

Os testes da API também rodam contra um Postgres (o banco da produção)
quando `FILMES_E_CUBOS_TESTE_POSTGRES` aponta um servidor em que a suíte
possa criar e apagar bancos. A definição de CI em `docs/ci/testes.yml`
faz isso a cada push, quando for ligada (ver a pendência em
[docs/PENDENCIAS.md](docs/PENDENCIAS.md)):

```bash
FILMES_E_CUBOS_TESTE_POSTGRES=postgresql://postgres@localhost:5432/postgres \
  uv run pytest tests/adapters/interfaces/api tests/adapters/persistence/sqlite/test_postgres.py
```

## Documentação

- [docs/ARQUITETURA.md](docs/ARQUITETURA.md) — estilo arquitetural, camadas
  e decisões de arquitetura.
- [docs/DOMINIO.md](docs/DOMINIO.md) — entidades, regras de negócio e
  invariantes do domínio.
- [docs/CASOS_DE_USO.md](docs/CASOS_DE_USO.md) — casos de uso da aplicação.
- [docs/ESTRUTURA_PROJETO.md](docs/ESTRUTURA_PROJETO.md) — estrutura de
  pastas e ferramentas do projeto.
- [docs/CLI.md](docs/CLI.md) — referência da interface de linha de
  comando.
- [docs/WEB.md](docs/WEB.md) — as páginas da interface web.
- [docs/API.md](docs/API.md) — referência da API HTTP.
- [docs/ROADMAP.md](docs/ROADMAP.md) — fases de desenvolvimento previstas.
- [docs/PENDENCIAS.md](docs/PENDENCIAS.md) — questões de negócio em aberto,
  decisões técnicas para revisão e dívidas técnicas conhecidas.
- [docs/GLOSSARIO.md](docs/GLOSSARIO.md) — termos do domínio do clube.
