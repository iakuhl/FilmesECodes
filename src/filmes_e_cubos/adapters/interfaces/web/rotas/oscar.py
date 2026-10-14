"""O Óscar do clube: edições, categorias, nomeações, votação e envio do placar.

O voto é secreto (decisão 26 de docs/PENDENCIAS.md): as páginas mostram
quem já votou e em quantas categorias, nunca em quê — nem para o próprio
eleitor, já que, sem login individual, qualquer um que entre no site
abriria a cédula dos outros. O placar só sai por e-mail (decisão 27).
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form, Request
from starlette.responses import Response

from filmes_e_cubos.adapters.composicao import Contexto
from filmes_e_cubos.adapters.interfaces.consultas import obter_clube, obter_filme
from filmes_e_cubos.adapters.interfaces.contexto_http import ContextoDep
from filmes_e_cubos.adapters.interfaces.convencoes import nome_padrao_da_temporada
from filmes_e_cubos.adapters.interfaces.situacao_da_votacao import (
    Disputa,
    SituacaoDaVotacao,
    SituacaoDoEleitor,
    situacao_da_votacao,
)
from filmes_e_cubos.adapters.interfaces.web.escopo import membro_do_clube
from filmes_e_cubos.adapters.interfaces.web.formatacao import rotulo
from filmes_e_cubos.adapters.interfaces.web.formularios import (
    data_obrigatoria,
    id_escolhido,
    inteiro_opcional,
    texto_opcional,
)
from filmes_e_cubos.adapters.interfaces.web.mensagens import (
    FormularioInvalidoError,
    avisar,
    recusas_viram_avisos,
)
from filmes_e_cubos.adapters.interfaces.web.oscar import (
    categoria_da_temporada,
    categoria_na_pagina,
    edicao_na_pagina,
    filmes_assistidos_no_ano,
    nomeacao_na_pagina,
    temporada_do_clube,
)
from filmes_e_cubos.adapters.interfaces.web.renderizacao import pagina, redirecionar
from filmes_e_cubos.domain.entities.nomeacao_oscar import NomeacaoOscar
from filmes_e_cubos.domain.entities.temporada_oscar import (
    NOMEACOES_POR_CATEGORIA_PADRAO,
    TemporadaOscar,
)
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    FilmeId,
    MembroId,
    NomeacaoOscarId,
)
from filmes_e_cubos.domain.value_objects.status import (
    ModoDeVotacao,
    StatusTemporadaOscar,
    TipoCategoriaOscar,
)

roteador = APIRouter(prefix="/clubes/{clube_id}/oscar")


@roteador.get("")
def edicoes(request: Request, clube_id: UUID, contexto: ContextoDep) -> Response:
    clube = obter_clube(contexto.clubes, clube_id)
    return pagina(
        request,
        "oscar.html",
        clube=clube,
        secao="oscar",
        edicoes=sorted(contexto.temporadas.listar_por_clube(clube.id), key=lambda t: -t.ano),
        ano_corrente=contexto.relogio.hoje().year,
        nomeacoes_padrao=NOMEACOES_POR_CATEGORIA_PADRAO,
    )


@roteador.post("")
def abrir_edicao(
    request: Request,
    clube_id: UUID,
    contexto: ContextoDep,
    ano: Annotated[str, Form()] = "",
    nome: Annotated[str, Form()] = "",
    nomeacoes_por_categoria: Annotated[str, Form()] = "",
) -> Response:
    with recusas_viram_avisos(request):
        clube = obter_clube(contexto.clubes, clube_id)
        ano_da_edicao = inteiro_opcional(ano, campo="Ano") or contexto.relogio.hoje().year
        temporada = contexto.abrir_temporada_oscar.executar(
            clube_id=clube.id,
            ano=ano_da_edicao,
            nome=texto_opcional(nome) or nome_padrao_da_temporada(clube.nome, ano_da_edicao),
            nomeacoes_por_categoria=(
                inteiro_opcional(nomeacoes_por_categoria, campo="Nomeações por categoria")
                or NOMEACOES_POR_CATEGORIA_PADRAO
            ),
        )
        avisar(request, "sucesso", f"{temporada.nome} aberta.")
        return redirecionar(f"/clubes/{clube_id}/oscar/{temporada.id}")
    return redirecionar(f"/clubes/{clube_id}/oscar")


@roteador.get("/{temporada_id}")
def edicao(request: Request, clube_id: UUID, temporada_id: UUID, contexto: ContextoDep) -> Response:
    clube = obter_clube(contexto.clubes, clube_id)
    temporada = temporada_do_clube(contexto, clube, temporada_id)
    return pagina(
        request,
        "edicao.html",
        clube=clube,
        secao="oscar",
        edicao=edicao_na_pagina(contexto, temporada),
        situacao=_situacao_ou_nada(contexto, temporada),
    )


@roteador.post("/{temporada_id}/avancar")
def avancar(
    request: Request, clube_id: UUID, temporada_id: UUID, contexto: ContextoDep
) -> Response:
    with recusas_viram_avisos(request):
        temporada = temporada_do_clube(
            contexto, obter_clube(contexto.clubes, clube_id), temporada_id
        )
        temporada = contexto.avancar_temporada_oscar.executar(temporada_id=temporada.id)
        avisar(request, "sucesso", f"{temporada.nome}: agora {rotulo(temporada.status).lower()}.")
    return redirecionar(f"/clubes/{clube_id}/oscar/{temporada_id}")


@roteador.post("/{temporada_id}/data-evento")
def definir_data_evento(
    request: Request,
    clube_id: UUID,
    temporada_id: UUID,
    contexto: ContextoDep,
    data_evento: Annotated[str, Form()] = "",
) -> Response:
    with recusas_viram_avisos(request):
        temporada = temporada_do_clube(
            contexto, obter_clube(contexto.clubes, clube_id), temporada_id
        )
        contexto.definir_data_evento_oscar.executar(
            temporada_id=temporada.id, data_evento=data_obrigatoria(data_evento, campo="Data")
        )
        avisar(request, "sucesso", "Data do evento marcada.")
    return redirecionar(f"/clubes/{clube_id}/oscar/{temporada_id}")


@roteador.post("/{temporada_id}/categorias")
def definir_categoria(
    request: Request,
    clube_id: UUID,
    temporada_id: UUID,
    contexto: ContextoDep,
    nome: Annotated[str, Form()] = "",
    tipo: Annotated[str, Form()] = TipoCategoriaOscar.VARIAVEL.name,
    descricao: Annotated[str, Form()] = "",
) -> Response:
    with recusas_viram_avisos(request):
        temporada = temporada_do_clube(
            contexto, obter_clube(contexto.clubes, clube_id), temporada_id
        )
        if tipo not in TipoCategoriaOscar.__members__:
            raise FormularioInvalidoError("Escolha se a categoria é fixa ou variável.")
        categoria = contexto.definir_categoria_oscar.executar(
            temporada_id=temporada.id,
            nome=nome.strip(),
            tipo=TipoCategoriaOscar[tipo],
            descricao=texto_opcional(descricao),
        )
        avisar(request, "sucesso", f"Categoria {categoria.nome} criada.")
    return redirecionar(f"/clubes/{clube_id}/oscar/{temporada_id}")


@roteador.get("/{temporada_id}/categorias/{categoria_id}")
def categoria(
    request: Request, clube_id: UUID, temporada_id: UUID, categoria_id: UUID, contexto: ContextoDep
) -> Response:
    clube = obter_clube(contexto.clubes, clube_id)
    temporada = temporada_do_clube(contexto, clube, temporada_id)
    escolhida = categoria_da_temporada(contexto, temporada, categoria_id)
    aceita_nomeacoes = temporada.status is StatusTemporadaOscar.ABERTA_PARA_INDICACOES
    return pagina(
        request,
        "categoria.html",
        clube=clube,
        secao="oscar",
        temporada=temporada,
        categoria=categoria_na_pagina(contexto, escolhida),
        filmes=filmes_assistidos_no_ano(contexto, clube, temporada.ano) if aceita_nomeacoes else [],
        aceita_nomeacoes=aceita_nomeacoes,
    )


@roteador.post("/{temporada_id}/categorias/{categoria_id}/nomeacoes")
def nomear(
    request: Request,
    clube_id: UUID,
    temporada_id: UUID,
    categoria_id: UUID,
    contexto: ContextoDep,
    filme_id: Annotated[str, Form()] = "",
) -> Response:
    with recusas_viram_avisos(request):
        temporada = temporada_do_clube(
            contexto, obter_clube(contexto.clubes, clube_id), temporada_id
        )
        escolhida = categoria_da_temporada(contexto, temporada, categoria_id)
        filme = obter_filme(contexto.filmes, id_escolhido(filme_id, campo="o filme"))
        contexto.indicar_filme_para_categoria.executar(
            categoria_id=escolhida.id, filme_id=FilmeId(filme.id)
        )
        avisar(request, "sucesso", f"{filme.titulo} nomeado em {escolhida.nome}.")
    return redirecionar(f"/clubes/{clube_id}/oscar/{temporada_id}/categorias/{categoria_id}")


@roteador.get("/{temporada_id}/votacao")
def votacao(
    request: Request, clube_id: UUID, temporada_id: UUID, contexto: ContextoDep
) -> Response:
    clube = obter_clube(contexto.clubes, clube_id)
    temporada = temporada_do_clube(contexto, clube, temporada_id)
    return pagina(
        request,
        "votacao.html",
        clube=clube,
        secao="oscar",
        temporada=temporada,
        situacao=situacao_da_votacao(contexto, temporada),
    )


@roteador.get("/{temporada_id}/votacao/{membro_id}")
def cedula(
    request: Request, clube_id: UUID, temporada_id: UUID, membro_id: UUID, contexto: ContextoDep
) -> Response:
    clube = obter_clube(contexto.clubes, clube_id)
    temporada = temporada_do_clube(contexto, clube, temporada_id)
    situacao = situacao_da_votacao(contexto, temporada)
    eleitor = _eleitor(situacao, membro_id)
    atual = contexto.cedulas.buscar(
        situacao.votacao.id, situacao.votacao.turno_atual, eleitor.membro.id
    )
    return pagina(
        request,
        "cedula.html",
        clube=clube,
        secao="oscar",
        temporada=temporada,
        situacao=situacao,
        eleitor=eleitor,
        votadas=atual.categorias_votadas if atual is not None else frozenset(),
        dupla=ModoDeVotacao.DUPLA,
        rotulos={
            nomeacao.id: _rotulo_da_nomeacao(contexto, nomeacao)
            for disputa in situacao.disputas
            for nomeacao in disputa.candidatas
        },
    )


@roteador.post("/{temporada_id}/votacao/{membro_id}/votos")
def votar(
    request: Request,
    clube_id: UUID,
    temporada_id: UUID,
    membro_id: UUID,
    contexto: ContextoDep,
    escolhas: Annotated[list[str] | None, Form()] = None,
) -> Response:
    """Grava os votos da cédula, categoria por categoria.

    Cada `<select>` manda `categoria|posição|nomeação`; categorias deixadas
    em branco ficam como estavam, e as incompletas viram aviso.
    """
    destino = f"/clubes/{clube_id}/oscar/{temporada_id}/votacao/{membro_id}"
    with recusas_viram_avisos(request):
        clube = obter_clube(contexto.clubes, clube_id)
        situacao = situacao_da_votacao(contexto, temporada_do_clube(contexto, clube, temporada_id))
        eleitor = membro_do_clube(contexto, clube, membro_id)
        por_categoria = _por_categoria(escolhas)
        votadas = [
            disputa.categoria.nome
            for disputa in situacao.disputas
            if _votar_na_categoria(request, contexto, disputa, eleitor.id, por_categoria)
        ]
        if votadas:
            avisar(
                request, "sucesso", f"Votos de {eleitor.nome} gravados em: {', '.join(votadas)}."
            )
    return redirecionar(destino)


@roteador.post("/{temporada_id}/votacao/{membro_id}/confirmacao")
def confirmar(
    request: Request, clube_id: UUID, temporada_id: UUID, membro_id: UUID, contexto: ContextoDep
) -> Response:
    with recusas_viram_avisos(request):
        clube = obter_clube(contexto.clubes, clube_id)
        temporada = temporada_do_clube(contexto, clube, temporada_id)
        eleitor = membro_do_clube(contexto, clube, membro_id)
        resultado = contexto.confirmar_cedula.executar(
            temporada_id=temporada.id, membro_id=eleitor.id
        )
        avisar(request, "sucesso", f"Cédula de {eleitor.nome} confirmada.")
        if resultado.turno_encerrado and resultado.votacao.encerrada:
            avisar(request, "sucesso", "Todos confirmaram: a votação terminou.")
        elif resultado.turno_encerrado:
            avisar(
                request,
                "sucesso",
                "Todos confirmaram. Houve empate no topo de alguma categoria: começou o "
                f"{resultado.votacao.turno_atual}º turno.",
            )
    return redirecionar(f"/clubes/{clube_id}/oscar/{temporada_id}/votacao")


@roteador.post("/{temporada_id}/placar")
def enviar_placar(
    request: Request,
    clube_id: UUID,
    temporada_id: UUID,
    contexto: ContextoDep,
    destinatario: Annotated[str, Form()] = "",
) -> Response:
    with recusas_viram_avisos(request):
        temporada = temporada_do_clube(
            contexto, obter_clube(contexto.clubes, clube_id), temporada_id
        )
        endereco = contexto.enviar_placar_oscar.executar(
            temporada_id=temporada.id, destinatario=destinatario
        )
        avisar(request, "sucesso", f"Placar enviado para {endereco}.")
    return redirecionar(f"/clubes/{clube_id}/oscar/{temporada_id}")


def _rotulo_da_nomeacao(contexto: Contexto, nomeacao: NomeacaoOscar) -> str:
    item = nomeacao_na_pagina(contexto, nomeacao)
    titulo = item.filme.titulo if item.filme else "(filme removido)"
    autoria = f"indicado por {item.indicado_por.nome}" if item.indicado_por else "democracia"
    return f"{titulo} — {autoria}"


def _situacao_ou_nada(contexto: Contexto, temporada: TemporadaOscar) -> SituacaoDaVotacao | None:
    if contexto.votacoes.buscar_por_temporada(temporada.id) is None:
        return None
    return situacao_da_votacao(contexto, temporada)


def _eleitor(situacao: SituacaoDaVotacao, membro_id: UUID) -> SituacaoDoEleitor:
    for eleitor in situacao.eleitores:
        if eleitor.membro.id == membro_id:
            return eleitor
    raise EntidadeNaoEncontradaError(f"Membro {membro_id} não é eleitor nesta votação.")


def _por_categoria(escolhas: list[str] | None) -> dict[str, dict[int, str]]:
    por_categoria: dict[str, dict[int, str]] = {}
    for valor in escolhas or []:
        if not valor:
            continue
        try:
            categoria_id, posicao, nomeacao_id = valor.split("|")
            por_categoria.setdefault(categoria_id, {})[int(posicao)] = nomeacao_id
        except ValueError as erro:
            raise FormularioInvalidoError(
                "A cédula chegou adulterada; recarregue a página."
            ) from erro
    return por_categoria


def _votar_na_categoria(
    request: Request,
    contexto: Contexto,
    disputa: Disputa,
    membro_id: MembroId,
    por_categoria: dict[str, dict[int, str]],
) -> bool:
    """Grava o voto numa categoria preenchida; devolve se gravou."""
    escolhidas = por_categoria.get(str(disputa.categoria.id))
    if not escolhidas:
        return False
    turno = disputa.turno
    nome = disputa.categoria.nome
    necessarias = 2 if turno.modo is ModoDeVotacao.DUPLA else len(turno.candidatas)
    if sorted(escolhidas) != list(range(1, necessarias + 1)):
        exigencia = "a 1ª e a 2ª opção" if necessarias == 2 else "a ordem de todas as candidatas"
        avisar(request, "erro", f"{nome}: escolha {exigencia}.")
        return False
    with recusas_viram_avisos(request):
        contexto.registrar_voto.executar(
            categoria_id=CategoriaOscarId(disputa.categoria.id),
            membro_id=membro_id,
            escolhas=[NomeacaoOscarId(UUID(escolhidas[i])) for i in range(1, necessarias + 1)],
        )
        return True
    return False
