"""Rodadas: abrir, indicar, democracia, sortear, encerrar e o histórico.

As ações da rodada aberta ficam no painel do clube, para onde voltam.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form, Request
from starlette.responses import Response

from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.adapters.interfaces.consultas import obter_clube, obter_filme
from filmes_e_cubos.adapters.interfaces.contexto_http import ContextoDep
from filmes_e_cubos.adapters.interfaces.web.escopo import membro_do_clube, rodada_do_clube
from filmes_e_cubos.adapters.interfaces.web.formularios import id_escolhido
from filmes_e_cubos.adapters.interfaces.web.mensagens import avisar, recusas_viram_avisos
from filmes_e_cubos.adapters.interfaces.web.painel import indicacoes_da_rodada
from filmes_e_cubos.adapters.interfaces.web.renderizacao import pagina, redirecionar
from filmes_e_cubos.domain.entities.indicacao import Indicacao
from filmes_e_cubos.domain.value_objects.identificadores import FilmeId, RodadaId

roteador = APIRouter(prefix="/clubes/{clube_id}")


@roteador.get("/rodadas")
def historico(request: Request, clube_id: UUID, contexto: ContextoDep) -> Response:
    clube = obter_clube(contexto.clubes, clube_id)
    rodadas = list(reversed(contexto.rodadas.listar_por_clube(clube.id)))
    quantas = {
        rodada.id: len(contexto.indicacoes.listar_por_rodada(rodada.id)) for rodada in rodadas
    }
    return pagina(
        request, "rodadas.html", clube=clube, secao="rodadas", rodadas=rodadas, quantas=quantas
    )


@roteador.get("/rodadas/{rodada_id}")
def rodada(request: Request, clube_id: UUID, rodada_id: UUID, contexto: ContextoDep) -> Response:
    clube = obter_clube(contexto.clubes, clube_id)
    escolhida = rodada_do_clube(contexto, clube, rodada_id)
    return pagina(
        request,
        "rodada.html",
        clube=clube,
        secao="rodadas",
        rodada=escolhida,
        indicacoes=indicacoes_da_rodada(contexto, escolhida),
    )


@roteador.post("/rodadas")
def abrir(request: Request, clube_id: UUID, contexto: ContextoDep) -> Response:
    with recusas_viram_avisos(request):
        nova = contexto.abrir_nova_rodada.executar(
            clube_id=obter_clube(contexto.clubes, clube_id).id
        )
        avisar(request, "sucesso", f"Rodada {nova.numero} aberta.")
    return redirecionar(f"/clubes/{clube_id}")


@roteador.post("/rodadas/{rodada_id}/indicacoes")
def indicar(
    request: Request,
    clube_id: UUID,
    rodada_id: UUID,
    contexto: ContextoDep,
    membro_id: Annotated[str, Form()] = "",
    filme_id: Annotated[str, Form()] = "",
) -> Response:
    with recusas_viram_avisos(request):
        clube = obter_clube(contexto.clubes, clube_id)
        aberta = rodada_do_clube(contexto, clube, rodada_id)
        membro = membro_do_clube(contexto, clube, id_escolhido(membro_id, campo="quem indica"))
        filme = obter_filme(contexto.filmes, id_escolhido(filme_id, campo="o filme"))
        contexto.indicar_filme.executar(
            rodada_id=RodadaId(aberta.id), membro_id=membro.id, filme_id=FilmeId(filme.id)
        )
        avisar(request, "sucesso", f"{membro.nome} indicou {filme.titulo}.")
    return redirecionar(f"/clubes/{clube_id}")


@roteador.post("/democracia")
def democracia(
    request: Request,
    clube_id: UUID,
    contexto: ContextoDep,
    filme_id: Annotated[str, Form()] = "",
) -> Response:
    with recusas_viram_avisos(request):
        clube = obter_clube(contexto.clubes, clube_id)
        filme = obter_filme(contexto.filmes, id_escolhido(filme_id, campo="o filme"))
        contexto.adicionar_filme_democracia.executar(clube_id=clube.id, filme_id=FilmeId(filme.id))
        avisar(request, "sucesso", f"Sessão democracia com {filme.titulo}.")
    return redirecionar(f"/clubes/{clube_id}")


@roteador.post("/rodadas/{rodada_id}/sorteio")
def sortear(request: Request, clube_id: UUID, rodada_id: UUID, contexto: ContextoDep) -> Response:
    with recusas_viram_avisos(request):
        aberta = rodada_do_clube(contexto, obter_clube(contexto.clubes, clube_id), rodada_id)
        sorteio = contexto.realizar_sorteio.executar(rodada_id=RodadaId(aberta.id))
        sorteada = contexto.indicacoes.buscar_por_id(sorteio.indicacao_sorteada_id)
        avisar(request, "sucesso", _anuncio_do_sorteio(contexto, sorteada))
    return redirecionar(f"/clubes/{clube_id}")


@roteador.post("/rodadas/{rodada_id}/encerrar")
def encerrar(request: Request, clube_id: UUID, rodada_id: UUID, contexto: ContextoDep) -> Response:
    with recusas_viram_avisos(request):
        aberta = rodada_do_clube(contexto, obter_clube(contexto.clubes, clube_id), rodada_id)
        encerrada = contexto.encerrar_rodada.executar(rodada_id=RodadaId(aberta.id))
        avisar(request, "sucesso", f"Rodada {encerrada.numero} encerrada.")
    return redirecionar(f"/clubes/{clube_id}")


def _anuncio_do_sorteio(contexto: Contexto, sorteada: Indicacao | None) -> str:
    if sorteada is None:
        return "Sorteio feito."
    filme = contexto.filmes.buscar_por_id(sorteada.filme_id)
    titulo = filme.titulo if filme is not None else "o filme"
    if sorteada.membro_id is None:
        return f"Sorteado: {titulo} (democracia)."
    membro = contexto.membros.buscar_por_id(sorteada.membro_id)
    return f"Sorteado: {titulo}, indicado por {membro.nome if membro else 'um ex-membro'}."
