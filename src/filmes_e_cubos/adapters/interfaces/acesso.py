"""Proteção do site e da API por uma senha única do clube.

Decisão 35 de docs/PENDENCIAS.md: provisória, até o login individual da
Fase 5. Quem sabe a senha entra — e pode agir por qualquer membro.

- Na web, a página `/entrar` recebe a senha e marca a sessão (um cookie
  assinado) como autenticada.
- Na API, programas mandam a senha no cabeçalho
  `Authorization: Bearer <senha>`, ou usam a sessão do navegador — o que
  faz a documentação interativa (`/api/v1/docs`) funcionar depois de
  entrar no site.

Sem senha configurada, nada é protegido: é o uso local, numa máquina só.
Na Vercel (que define a variável `VERCEL`), isso deixaria o clube aberto
na internet; por isso, lá, a falta da senha tira o site do ar com uma
mensagem que diz o que configurar.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Final
from urllib.parse import quote

from starlette.requests import Request
from starlette.responses import PlainTextResponse, RedirectResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

from filmes_e_cubos.adapters.interfaces.api.erros import resposta_de_problema

VARIAVEL_DE_AMBIENTE_SENHA: Final = "FILMES_E_CUBOS_SENHA"
"""A senha do clube. Sem ela, o site não é protegido (e, na Vercel, não abre)."""

VARIAVEL_DE_AMBIENTE_CHAVE_SECRETA: Final = "FILMES_E_CUBOS_CHAVE_SECRETA"
"""Chave que assina o cookie da sessão; sem ela, uma é derivada da senha."""

CHAVE_DA_SESSAO: Final = "autenticado"

PAGINA_DE_ENTRADA: Final = "/entrar"

_CAMINHOS_LIVRES: Final = (PAGINA_DE_ENTRADA, "/estaticos/", "/api/v1/saude", "/favicon.ico")
"""O que não pede senha: a própria entrada, o visual dela e a verificação de saúde."""


def senha_confere(tentativa: str, senha: str) -> bool:
    """Compara em tempo constante, para que o tempo da resposta não revele a senha."""
    return hmac.compare_digest(tentativa.encode(), senha.encode())


def chave_secreta_da_senha(senha: str) -> str:
    """Chave de assinatura dos cookies derivada da senha.

    É a mesma em todas as instâncias da função da Vercel (que não
    compartilham memória) e muda junto com a senha — trocar a senha
    desconecta todo mundo.
    """
    return hmac.new(senha.encode(), b"filmes-e-cubos/sessao", hashlib.sha256).hexdigest()


def destino_seguro(proximo: str | None) -> str:
    """Para onde voltar depois de entrar: só caminhos deste site.

    `//outro.site` e `https://...` viram a página inicial, para que o link
    de entrada não sirva de trampolim para outro endereço.
    """
    if proximo and proximo.startswith("/") and not proximo.startswith("//"):
        return proximo
    return "/"


class ProtecaoPorSenha:
    """Middleware ASGI que só deixa passar quem provou saber a senha do clube.

    Precisa rodar *dentro* do `SessionMiddleware`, que lhe entrega a
    sessão já lida do cookie.
    """

    def __init__(self, app: ASGIApp, *, senha: str | None, exigir_senha: bool) -> None:
        self._app = app
        self._senha = senha or None
        self._exigir_senha = exigir_senha

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"].startswith(_CAMINHOS_LIVRES):
            await self._app(scope, receive, send)
            return
        if self._senha is None:
            if self._exigir_senha:
                await _sem_senha_configurada(scope)(scope, receive, send)
                return
            await self._app(scope, receive, send)
            return
        requisicao = Request(scope)
        if requisicao.session.get(CHAVE_DA_SESSAO) is True or self._chave_confere(requisicao):
            await self._app(scope, receive, send)
            return
        await _recusa(requisicao)(scope, receive, send)

    def _chave_confere(self, requisicao: Request) -> bool:
        tipo, _, credencial = requisicao.headers.get("authorization", "").partition(" ")
        return (
            self._senha is not None
            and tipo.lower() == "bearer"
            and senha_confere(credencial, self._senha)
        )


def _recusa(requisicao: Request) -> Response:
    if requisicao.url.path.startswith("/api/"):
        resposta = resposta_de_problema(
            401,
            "Informe a senha do clube no cabeçalho `Authorization: Bearer <senha>`.",
            "nao_autenticado",
        )
        resposta.headers["WWW-Authenticate"] = "Bearer"
        return resposta
    caminho = requisicao.url.path
    if requisicao.url.query:
        caminho = f"{caminho}?{requisicao.url.query}"
    return RedirectResponse(f"{PAGINA_DE_ENTRADA}?proximo={quote(caminho)}", status_code=303)


def _sem_senha_configurada(scope: Scope) -> Response:
    detalhe = (
        f"O site está sem senha: defina {VARIAVEL_DE_AMBIENTE_SENHA} nas variáveis de ambiente "
        "do projeto na Vercel e publique de novo."
    )
    if scope["path"].startswith("/api/"):
        return resposta_de_problema(503, detalhe, "senha_nao_configurada")
    return PlainTextResponse(detalhe, status_code=503)
