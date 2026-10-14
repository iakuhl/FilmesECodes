# Interface web

Páginas renderizadas no servidor (Jinja2 e CSS próprio, sem JavaScript
obrigatório), servidas pelo mesmo app da API: `uv run
filmes-e-cubos-servidor` localmente, ou a Vercel em produção (ver o
README). A web é só mais uma interface: cada página chama os mesmos casos
de uso da CLI e da API.

## Convenções

- **Post/Redirect/Get:** toda ação é um formulário que faz `POST`; a
  resposta redireciona (303) para uma página comum, que mostra um aviso
  de sucesso ou o motivo da recusa — em texto para pessoas, sem ids.
- **Tudo por clube:** as páginas de um clube moram em
  `/clubes/{clube_id}/...`, com a navegação do clube no topo.
- **Erros:** um endereço que não leva a nada (id inexistente ou
  malformado) mostra a página "Ops" com status 404; uma falha do servidor,
  com 500.
- **Senha do clube:** com `FILMES_E_CUBOS_SENHA` definida, toda página
  pede para entrar antes (decisão 35 de [PENDENCIAS.md](PENDENCIAS.md));
  o botão "Sair" aparece no topo.

## Páginas

| Caminho | O que mostra e o que dá para fazer |
|---|---|
| `/entrar` | Pede a senha do clube e volta à página que se queria abrir. |
| `/` | Sem clube, oferece criar um (nome e indicações por rodada); com um só, vai direto a ele; com vários, lista para escolher. |
| `/clubes/{id}` | O painel: a rodada aberta com as suas indicações (filme, quem indicou, situação, sessão e média em estrelas), os membros ativos e a edição do Óscar do ano. |
