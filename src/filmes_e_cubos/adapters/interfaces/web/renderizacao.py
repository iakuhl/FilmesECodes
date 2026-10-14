"""Como as páginas são montadas: o ambiente Jinja e as respostas padrão da web.

Os modelos ficam em `templates/`, com escape automático de HTML e
`StrictUndefined` (uma variável esquecida vira erro, não um buraco
silencioso na página). As funções de `formatacao.py` viram filtros: nos
modelos, `{{ sessao.data_sessao | data }}`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Final

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates, _TemplateResponse

from filmes_e_cubos.adapters.interfaces.acesso import CHAVE_DA_SESSAO
from filmes_e_cubos.adapters.interfaces.web.formatacao import (
    formatar_data,
    formatar_data_hora,
    formatar_decimal,
    formatar_duracao,
    formatar_estrelas,
    rotulo,
)
from filmes_e_cubos.adapters.interfaces.web.mensagens import consumir_avisos
from filmes_e_cubos.domain.entities.clube import Clube

DIRETORIO_DOS_MODELOS: Final = Path(__file__).parent / "templates"

_ambiente = Environment(
    loader=FileSystemLoader(DIRETORIO_DOS_MODELOS),
    autoescape=select_autoescape(["html"]),
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
)
_ambiente.filters.update(
    rotulo=rotulo,
    data=formatar_data,
    data_hora=formatar_data_hora,
    decimal=formatar_decimal,
    duracao=formatar_duracao,
    estrelas=formatar_estrelas,
)
_ambiente.globals["secoes_do_clube"] = (
    # (chave da seção, nome no menu, caminho depois de /clubes/{id})
    ("painel", "Painel", ""),
    ("membros", "Membros", "/membros"),
    ("filmes", "Filmes", "/filmes"),
    ("rodadas", "Rodadas", "/rodadas"),
    ("oscar", "Óscar", "/oscar"),
)
_modelos = Jinja2Templates(env=_ambiente)


def pagina(
    request: Request,
    nome: str,
    *,
    clube: Clube | None = None,
    secao: str = "",
    status_code: int = 200,
    **contexto: Any,
) -> _TemplateResponse:
    """Renderiza o modelo `nome` com o que toda página usa.

    `clube` liga a navegação do clube no topo, e `secao` marca nela a
    página atual. Os avisos pendentes (da ação anterior, no padrão
    Post/Redirect/Get) são consumidos aqui.
    """
    return _modelos.TemplateResponse(
        request,
        nome,
        {
            "avisos": consumir_avisos(request),
            "autenticado": request.session.get(CHAVE_DA_SESSAO) is True,
            "clube": clube,
            "secao": secao,
            **contexto,
        },
        status_code=status_code,
    )


def redirecionar(url: str) -> RedirectResponse:
    """A resposta de toda ação de formulário: 303, para a página seguir com um GET."""
    return RedirectResponse(url, status_code=303)
