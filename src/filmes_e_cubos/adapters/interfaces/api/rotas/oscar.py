"""Rotas do Óscar do Filmes e Cubos: temporadas, categorias, nomeações, votação e apuração.

O voto é secreto (decisão 26 de docs/PENDENCIAS.md): nenhuma rota mostra
em que alguém votou, nem o placar.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, status

from filmes_e_cubos.adapters.interfaces.api.esquemas import (
    CategoriaSaida,
    CedulaSaida,
    ConfirmacaoSaida,
    EnvioDoPlacarSaida,
    NomeacaoSaida,
    NovaCategoria,
    NovaDataDoEvento,
    NovaNomeacao,
    NovaTemporada,
    NovoEnvioDoPlacar,
    NovoTrofeu,
    NovoVoto,
    TemporadaSaida,
    TrofeuSaida,
    VotacaoSaida,
)
from filmes_e_cubos.adapters.interfaces.consultas import (
    obter_categoria,
    obter_clube,
    obter_nomeacao,
    obter_temporada,
)
from filmes_e_cubos.adapters.interfaces.contexto_http import ContextoDep
from filmes_e_cubos.adapters.interfaces.convencoes import nome_padrao_da_temporada
from filmes_e_cubos.adapters.interfaces.situacao_da_votacao import situacao_da_votacao
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    FilmeId,
    MembroId,
    NomeacaoOscarId,
    TemporadaOscarId,
)

roteador = APIRouter(tags=["óscar"])


@roteador.get("/clubes/{clube_id}/oscar/temporadas", summary="Lista as edições do Óscar")
def listar_temporadas(clube_id: UUID, contexto: ContextoDep) -> list[TemporadaSaida]:
    clube = obter_clube(contexto.clubes, clube_id)
    return [
        TemporadaSaida.de_dominio(temporada)
        for temporada in contexto.temporadas.listar_por_clube(clube.id)
    ]


@roteador.post(
    "/clubes/{clube_id}/oscar/temporadas",
    status_code=status.HTTP_201_CREATED,
    summary="Abre uma edição do Óscar",
    description="O corpo é opcional: sem `ano`, usa o ano corrente; sem `nome`, "
    '"Óscar do <clube> <ano>"; sem `nomeacoes_por_categoria`, 5. `409` se o clube já tiver '
    "a edição daquele ano.",
)
def abrir_temporada(
    clube_id: UUID,
    contexto: ContextoDep,
    nova: Annotated[NovaTemporada | None, Body()] = None,
) -> TemporadaSaida:
    clube = obter_clube(contexto.clubes, clube_id)
    pedido = nova or NovaTemporada()
    ano = pedido.ano if pedido.ano is not None else contexto.relogio.hoje().year
    temporada = contexto.abrir_temporada_oscar.executar(
        clube_id=clube.id,
        ano=ano,
        nome=pedido.nome if pedido.nome is not None else nome_padrao_da_temporada(clube.nome, ano),
        nomeacoes_por_categoria=pedido.nomeacoes_por_categoria,
    )
    return TemporadaSaida.de_dominio(temporada)


@roteador.get("/oscar/temporadas/{temporada_id}", summary="Consulta uma edição do Óscar")
def consultar_temporada(temporada_id: UUID, contexto: ContextoDep) -> TemporadaSaida:
    return TemporadaSaida.de_dominio(obter_temporada(contexto.temporadas, temporada_id))


@roteador.post(
    "/oscar/temporadas/{temporada_id}/avancar",
    summary="Avança a edição para a fase seguinte",
    description="Em preparação → aberta para indicações → em votação → apurada → encerrada, "
    "um passo por vez. Ir à votação exige ao menos uma categoria, cada uma com exatamente o "
    "número de nomeações da edição; ir a apurada exige resultado em toda categoria (`409` "
    "`temporada_incompleta` se faltar algo).",
)
def avancar_temporada(temporada_id: UUID, contexto: ContextoDep) -> TemporadaSaida:
    temporada = contexto.avancar_temporada_oscar.executar(
        temporada_id=TemporadaOscarId(temporada_id)
    )
    return TemporadaSaida.de_dominio(temporada)


@roteador.put(
    "/oscar/temporadas/{temporada_id}/data-evento",
    summary="Marca (ou remarca) a data do evento",
    description="`409` se a edição já estiver encerrada.",
)
def definir_data_evento(
    temporada_id: UUID, nova: NovaDataDoEvento, contexto: ContextoDep
) -> TemporadaSaida:
    temporada = contexto.definir_data_evento_oscar.executar(
        temporada_id=TemporadaOscarId(temporada_id), data_evento=nova.data_evento
    )
    return TemporadaSaida.de_dominio(temporada)


@roteador.get(
    "/oscar/temporadas/{temporada_id}/categorias", summary="Lista as categorias de uma edição"
)
def listar_categorias(temporada_id: UUID, contexto: ContextoDep) -> list[CategoriaSaida]:
    temporada = obter_temporada(contexto.temporadas, temporada_id)
    return [
        CategoriaSaida.de_dominio(categoria)
        for categoria in contexto.categorias.listar_por_temporada(temporada.id)
    ]


@roteador.post(
    "/oscar/temporadas/{temporada_id}/categorias",
    status_code=status.HTTP_201_CREATED,
    summary="Define uma categoria",
)
def definir_categoria(
    temporada_id: UUID, nova: NovaCategoria, contexto: ContextoDep
) -> CategoriaSaida:
    categoria = contexto.definir_categoria_oscar.executar(
        temporada_id=TemporadaOscarId(temporada_id),
        nome=nova.nome,
        tipo=nova.tipo.para_dominio(),
        descricao=nova.descricao,
    )
    return CategoriaSaida.de_dominio(categoria)


@roteador.get("/oscar/categorias/{categoria_id}", summary="Consulta uma categoria")
def consultar_categoria(categoria_id: UUID, contexto: ContextoDep) -> CategoriaSaida:
    return CategoriaSaida.de_dominio(obter_categoria(contexto.categorias, categoria_id))


@roteador.get(
    "/oscar/categorias/{categoria_id}/nomeacoes", summary="Lista as nomeações de uma categoria"
)
def listar_nomeacoes(categoria_id: UUID, contexto: ContextoDep) -> list[NomeacaoSaida]:
    categoria = obter_categoria(contexto.categorias, categoria_id)
    return [
        NomeacaoSaida.de_dominio(nomeacao)
        for nomeacao in contexto.nomeacoes.listar_por_categoria(categoria.id)
    ]


@roteador.post(
    "/oscar/categorias/{categoria_id}/nomeacoes",
    status_code=status.HTTP_201_CREATED,
    summary="Nomeia um filme para a categoria",
    description="O filme precisa ter sido assistido pelo clube dentro do ano da edição. A "
    "nomeação herda quem indicou o filme — é essa pessoa que leva o troféu.",
)
def nomear(categoria_id: UUID, nova: NovaNomeacao, contexto: ContextoDep) -> NomeacaoSaida:
    nomeacao = contexto.indicar_filme_para_categoria.executar(
        categoria_id=CategoriaOscarId(categoria_id), filme_id=FilmeId(nova.filme_id)
    )
    return NomeacaoSaida.de_dominio(nomeacao)


@roteador.get("/oscar/nomeacoes/{nomeacao_id}", summary="Consulta uma nomeação")
def consultar_nomeacao(nomeacao_id: UUID, contexto: ContextoDep) -> NomeacaoSaida:
    return NomeacaoSaida.de_dominio(obter_nomeacao(contexto.nomeacoes, nomeacao_id))


@roteador.get(
    "/oscar/temporadas/{temporada_id}/votacao",
    summary="Consulta a situação da votação",
    description="O turno atual, as categorias em disputa (com as candidatas na ordem da "
    "cédula) e, de cada eleitor, em quantas categorias já votou e se confirmou. `404` antes "
    "de a edição chegar à votação.",
)
def consultar_votacao(temporada_id: UUID, contexto: ContextoDep) -> VotacaoSaida:
    temporada = obter_temporada(contexto.temporadas, temporada_id)
    return VotacaoSaida.de_situacao(situacao_da_votacao(contexto, temporada))


@roteador.put(
    "/oscar/categorias/{categoria_id}/votos/{membro_id}",
    summary="Registra ou troca o voto de um eleitor na categoria",
    description="O voto vai para a cédula do eleitor no turno atual e pode ser trocado até a "
    "cédula ser confirmada. Só votam os membros que estavam ativos quando a votação começou.",
)
def votar(
    categoria_id: UUID, membro_id: UUID, voto: NovoVoto, contexto: ContextoDep
) -> CedulaSaida:
    cedula = contexto.registrar_voto.executar(
        categoria_id=CategoriaOscarId(categoria_id),
        membro_id=MembroId(membro_id),
        escolhas=[NomeacaoOscarId(escolha) for escolha in voto.escolhas],
    )
    return CedulaSaida.de_dominio(cedula)


@roteador.post(
    "/oscar/temporadas/{temporada_id}/votacao/cedulas/{membro_id}/confirmacao",
    summary="Confirma a cédula do eleitor no turno atual",
    description="Exige voto em todas as categorias do turno (`409` `cedula_incompleta`, com as "
    "que faltam). Confirmada, a cédula não muda mais. A última confirmação encerra o turno: o "
    "sistema apura sem mostrar nada e abre o turno seguinte nas categorias empatadas.",
)
def confirmar_cedula(
    temporada_id: UUID, membro_id: UUID, contexto: ContextoDep
) -> ConfirmacaoSaida:
    temporada = obter_temporada(contexto.temporadas, temporada_id)
    resultado = contexto.confirmar_cedula.executar(
        temporada_id=temporada.id, membro_id=MembroId(membro_id)
    )
    return ConfirmacaoSaida(
        turno_encerrado=resultado.turno_encerrado,
        votacao=VotacaoSaida.de_situacao(situacao_da_votacao(contexto, temporada)),
    )


@roteador.post(
    "/oscar/temporadas/{temporada_id}/placar/envios",
    summary="Envia o placar da votação por e-mail",
    description="O placar não aparece em nenhuma resposta (decisão 27): vai direto para o "
    "e-mail de quem monta a cerimônia. Só com a votação terminada (`409` `votacao_em_andamento`) "
    "e até a edição ser encerrada; pode ser reenviado. `503` `envio_de_email_indisponivel` sem "
    "servidor de e-mail configurado; `502` `falha_no_envio_de_email` se ele recusar.",
)
def enviar_placar(
    temporada_id: UUID, envio: NovoEnvioDoPlacar, contexto: ContextoDep
) -> EnvioDoPlacarSaida:
    endereco = contexto.enviar_placar_oscar.executar(
        temporada_id=TemporadaOscarId(temporada_id), destinatario=envio.destinatario
    )
    return EnvioDoPlacarSaida(destinatario=str(endereco))


@roteador.post(
    "/oscar/categorias/{categoria_id}/trofeu",
    status_code=status.HTTP_201_CREATED,
    summary="Registra o vencedor da categoria",
    description="A apuração acontece fora do sistema, com o placar que foi por e-mail: aqui se "
    "registra o resultado, depois da cerimônia, com a votação terminada e a edição ainda em "
    "votação. O troféu vai para quem indicou a nomeação vencedora; num filme democracia ou num "
    "empate absoluto (sem `nomeacao_id`), para `membro_escolhido_id`, obrigatório nesses casos "
    "(`422` `escolha_do_grupo_necessaria`). `409` `categoria_ja_apurada` se já houver vencedor.",
)
def registrar_vencedor(categoria_id: UUID, novo: NovoTrofeu, contexto: ContextoDep) -> TrofeuSaida:
    trofeu = contexto.registrar_vencedor_oscar.executar(
        categoria_id=CategoriaOscarId(categoria_id),
        nomeacao_id=NomeacaoOscarId(novo.nomeacao_id) if novo.nomeacao_id else None,
        membro_escolhido_id=(
            MembroId(novo.membro_escolhido_id) if novo.membro_escolhido_id else None
        ),
    )
    return TrofeuSaida.de_dominio(trofeu)


@roteador.get(
    "/oscar/categorias/{categoria_id}/trofeu",
    summary="Consulta o troféu de uma categoria",
    description="404 enquanto a categoria não tiver vencedor registrado.",
)
def consultar_trofeu(categoria_id: UUID, contexto: ContextoDep) -> TrofeuSaida:
    categoria = obter_categoria(contexto.categorias, categoria_id)
    trofeu = contexto.trofeus.buscar_por_categoria(categoria.id)
    if trofeu is None:
        raise EntidadeNaoEncontradaError(f"A categoria {categoria.nome} ainda não foi apurada.")
    return TrofeuSaida.de_dominio(trofeu)
