# CLAUDE.md

Guia para quem continua o desenvolvimento deste repositório com o Claude
Code. O contexto de produto está no [README](README.md); o histórico e o
plano, em [docs/ROADMAP.md](docs/ROADMAP.md).

## O projeto

Software de gestão do clube de cinema **Filmes e Cubos**: membros,
catálogo de filmes, rodadas de indicação, sorteios, sessões, avaliações
e o Óscar anual do clube. Python 3.11+, arquitetura hexagonal (ports &
adapters), SQLite via SQLAlchemy Core, CLI em Typer e API em FastAPI.
Projeto pessoal conduzido com rigor profissional (portfólio), desenhado
para virar produto multi-clube.

## Onde parou e como continuar

- Branch de trabalho: `roadmap/fases-4-e-5` (local, sem push).
- Fases 1–3 concluídas; Fase 4 com a API pronta, migrações com Alembic e
  os módulos de apoio da web; as páginas da web ainda não existem.
- Revisão de regras de 24/09/2026 quase toda implementada (duração,
  reativação, data do evento, só presentes avaliam, média como fração em
  estrelas, filme não se repete, uma edição por ano, nomeações fixas por
  categoria, ciclo com *em votação*, contrato do histórico).
- **Próximo passo:** a **votação** do Óscar, que ainda usa o critério
  antigo (escolha informada). O desenho completo está em "Desenho da
  votação" no [ROADMAP](docs/ROADMAP.md); depois dela, as páginas da web.
  As decisões, numeradas, estão em [docs/PENDENCIAS.md](docs/PENDENCIAS.md)
  — inclusive as interpretações que ainda pedem confirmação.
- Sessões longas: perto de 50% da janela de contexto, termine a etapa em
  curso, documente como continuar (aqui, no ROADMAP e no PENDENCIAS) e
  pare com um resumo — preferência do dono.

## Comandos

```bash
uv sync --dev                        # dependências (runtime + dev)
uv run pytest                        # suíte completa (~40 s)
uv run mypy src                      # tipos, modo estrito (só src/)
uv run ruff check . && uv run ruff format --check .
uv run filmes-e-cubos --help         # CLI
uv run filmes-e-cubos-servidor       # API em http://127.0.0.1:8000/api/v1/docs
uv run alembic revision --autogenerate -m "descrição"   # nova revisão do esquema
```

Um passo só está pronto com os quatro verdes: pytest, mypy, ruff check e
ruff format.

## Arquitetura em uma página

- `domain/`: entidades ricas (construtores validam invariantes), value
  objects e exceções (`DomainError` e subclasses). Não importa nada de
  fora.
- `application/`: um caso de uso por módulo (`executar(...)` com
  argumentos nomeados) e os ports (`typing.Protocol`) de que precisam.
- `adapters/composicao.py`: o composition root — o único lugar que conhece
  ports e implementações ao mesmo tempo; monta o `Contexto` que todas as
  interfaces usam.
- `adapters/persistence/sqlite/`: repositórios com SQLAlchemy Core (sem
  ORM), conversão manual `_para_linha`/`_para_entidade`; esquema em
  `esquema.py`, migrações em `migracao.py` + `migracoes/`.
- `adapters/interfaces/`: `cli/` (Typer), `api/` (FastAPI em `/api/v1`,
  erros RFC 9457), `web/` (em construção) e o que elas compartilham
  (`convencoes.py`, `consultas.py`, `erros_http.py`, `contexto_http.py`,
  `escritas_em_fila.py`, `servidor.py`).
- Decisões de arquitetura registradas como ADRs na tabela de
  [docs/ARQUITETURA.md](docs/ARQUITETURA.md).

## Regras de trabalho

- **Regra de negócio é do dono do produto.** Não invente nem mude regra
  por conta própria: pergunte ou registre a dúvida, numerada, em
  `docs/PENDENCIAS.md`. Decisões técnicas podem ser tomadas, mas também
  ficam registradas lá.
- **Interfaces não têm regra de negócio**: só traduzem entrada e saída
  para os casos de uso. Listagens de leitura vão direto ao repositório
  (ADR 7); toda ação que muda estado passa por um caso de uso.
- **Todo erro de domínio novo precisa de status HTTP** em
  `adapters/interfaces/erros_http.py` — um teste falha se faltar.
- **Toda mudança em `esquema.py` precisa de uma revisão do Alembic** — um
  teste compara o resultado das migrações com o esquema declarado.
- **Testes de adapter usam o componente real**: SQLite de verdade em
  `tmp_path`, a CLI pelo `CliRunner` e a API pelo `TestClient` do app
  completo. Os fixtures montam o cenário pela própria interface, nunca
  inserindo linhas direto no banco. Fakes in-memory só em
  `tests/application/fakes/`, para os testes de casos de uso.
- **Documentação acompanha o código** no mesmo commit: ROADMAP,
  ARQUITETURA (ADRs), ESTRUTURA_PROJETO, CLI.md/API.md, DOMINIO e
  CASOS_DE_USO quando regras mudarem, e PENDENCIAS.
- **Git:** um commit por etapa concluída, no branch local, sem push e sem
  mesclar em `main` (preferência confirmada pelo dono). Mensagens em
  português: título no imperativo, corpo explicando o porquê, e a linha
  `Co-Authored-By` ao final.
- Checklists de perguntas ao usuário sempre numerados.

## Convenções de código

- Conceitos de domínio em **português** (`Membro`, `Rodada`,
  `IndicarFilme`); sufixos técnicos em inglês (`...Repository`,
  `...Service`, `...Error` — a regra N818 do ruff exige `Error`).
- Na API: saídas `...Saida`, criações `Novo...`/`Nova...`, espelhos de
  enumeração `...Api`; na CLI, `...Cli`.
- Docstrings e comentários em português, explicando o porquê.
- `from __future__ import annotations` nos módulos; linhas de até 100
  colunas; tipos em tudo (mypy estrito em `src/`).
- Decimais (notas, escala) são `Decimal`, guardados como texto no banco;
  ids são `NewType` sobre `UUID`, guardados como texto.

## Armadilhas do ambiente

- **Windows + fins de linha:** o repositório é todo LF
  (`.gitattributes`). `Path.write_text` no Windows grava CRLF — ao gerar
  arquivos por script, use `write_bytes` (ou `newline="\n"`), ou as
  ferramentas de edição.
- No shell, `cd` muda o diretório das chamadas seguintes; prefira
  caminhos absolutos.
- **Starlette 1.x:** o `TestClient` espera o pacote `httpx2` (já é
  dependência de dev); `TemplateResponse(request, nome, contexto)` recebe
  a requisição primeiro.
- O venv usa Python 3.14, mas o projeto declara `>=3.11`: não use
  sintaxe exclusiva de versões mais novas (ex.: `type X = ...`).
- O Docker não fica rodando nesta máquina; o deploy, por ora, é só local
  (mas mantenha tudo configurável por variável de ambiente).
