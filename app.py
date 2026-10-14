"""Ponto de entrada da Vercel: o app completo (web e API) configurado pelo ambiente.

A Vercel procura um `app` em `app.py` na raiz do repositório e o serve
como uma função. Em produção, o banco é o Postgres da Neon, que a
integração da Vercel entrega em `DATABASE_URL`; ver o README.

O pacote mora em `src/` e a Vercel o instala a partir do código; o
caminho é acrescentado também aqui, para que o ponto de entrada funcione
mesmo sem a instalação.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from filmes_e_cubos.adapters.interfaces.servidor import (  # noqa: E402
    criar_aplicacao_do_ambiente,
)

app = criar_aplicacao_do_ambiente()
