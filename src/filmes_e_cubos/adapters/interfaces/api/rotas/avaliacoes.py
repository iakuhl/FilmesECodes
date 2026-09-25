"""Rotas de avaliação do filme assistido em uma sessão."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from filmes_e_cubos.adapters.interfaces.api.esquemas import AvaliacaoSaida, NovaAvaliacao
from filmes_e_cubos.adapters.interfaces.consultas import obter_sessao
from filmes_e_cubos.adapters.interfaces.contexto_http import ContextoDep
from filmes_e_cubos.domain.value_objects.identificadores import MembroId
from filmes_e_cubos.domain.value_objects.nota import Nota

roteador = APIRouter(tags=["avaliações"])


@roteador.get("/sessoes/{sessao_id}/avaliacoes", summary="Lista as avaliações de uma sessão")
def listar_avaliacoes(sessao_id: UUID, contexto: ContextoDep) -> list[AvaliacaoSaida]:
    sessao = obter_sessao(contexto.sessoes, sessao_id)
    return [
        AvaliacaoSaida.de_dominio(avaliacao)
        for avaliacao in contexto.avaliacoes.listar_por_sessao(sessao.id)
    ]


@roteador.post(
    "/sessoes/{sessao_id}/avaliacoes",
    status_code=status.HTTP_201_CREATED,
    summary="Registra a avaliação de um membro",
    description="Só avalia quem esteve presente na sessão (`409` para os demais). A nota "
    "precisa respeitar a escala do clube dono da sessão. `nota: null` registra que o membro "
    "cochilou (dorminhoco): o voto fica para a posteridade, mas é ignorado na média. Cada "
    "membro avalia cada sessão uma vez só; a média da sessão é refeita a cada avaliação.",
)
def avaliar(sessao_id: UUID, nova: NovaAvaliacao, contexto: ContextoDep) -> AvaliacaoSaida:
    sessao = obter_sessao(contexto.sessoes, sessao_id)
    avaliacao = contexto.avaliar_filme.executar(
        sessao_id=sessao.id,
        membro_id=MembroId(nova.membro_id),
        nota=Nota.criar(nova.nota) if nova.nota is not None else None,
        comentario=nova.comentario,
    )
    return AvaliacaoSaida.de_dominio(avaliacao)
