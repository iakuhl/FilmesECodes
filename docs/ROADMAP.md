# Roadmap

Fases sugeridas de desenvolvimento, do núcleo de domínio até uma eventual
versão comercial. Cada fase só começa depois da anterior estar
razoavelmente sólida e testada — a arquitetura hexagonal existe justamente
para que essa progressão não exija retrabalho nas fases já prontas.

## Fase 1 — Núcleo de domínio e casos de uso

- Implementar as entidades e value objects descritos em
  [DOMINIO.md](DOMINIO.md), com seus invariantes garantidos por código
  (não apenas por documentação).
- Implementar os ports (`Protocol`) descritos em
  [ARQUITETURA.md](ARQUITETURA.md) e os casos de uso de
  [CASOS_DE_USO.md](CASOS_DE_USO.md), usando implementações de teste
  (fakes/in-memory) dos ports para validar as regras de negócio.
- Cobertura de testes de domínio e de aplicação como critério de saída
  desta fase — nenhum adapter real é necessário para isso.
- **Decisões ainda em aberto ao final desta fase**: nenhuma decisão de
  persistência ou interface é necessária aqui.

## Fase 2 — Primeiro adapter de persistência

- Decidir e implementar a primeira implementação concreta dos
  repositórios (candidatos discutidos: SQLite via SQLAlchemy, ou
  arquivos JSON — decisão explicitamente adiada na Fase 1).
- Testes de integração validando que a implementação concreta respeita
  os mesmos contratos usados pelos fakes da Fase 1.

## Fase 3 — Primeira interface de usuário

- Decidir e implementar a primeira interface (candidata natural: CLI, por
  simplicidade de implementação e por não exigir infraestrutura extra).
- A interface apenas traduz entrada/saída para chamadas aos casos de uso
  já existentes — nenhuma regra de negócio nova nasce aqui.

## Fase 4 — API / Web

- Caso haja interesse em uma interface mais rica (web) ou em uso remoto
  pelos membros do clube, adicionar um adapter de API (ex.: FastAPI) e,
  posteriormente, um frontend web.
- Reaproveita integralmente os casos de uso das fases anteriores.

## Fase 5 — Evolução comercial

- Suporte a múltiplos clubes (a entidade `Clube` já foi desenhada para
  isso desde a Fase 1).
- Autenticação/autorização de membros.
- Eventuais integrações externas (ex.: base de dados de filmes para
  autocompletar título/ano/diretor).
- Empacotamento e distribuição como produto.

## Pontos explicitamente em aberto

| Decisão | Status | Onde será resolvida |
|---|---|---|
| Implementação concreta de persistência | Adiada | Fase 2 |
| Primeira interface de usuário | Adiada | Fase 3 |
| Mecanismo de apuração de categorias do Óscar (votação vs. critério fixo) | A refinar | Fase 1, ao detalhar `ApurarCategoriaOscar` |
