"""Resolução das entidades "correntes" quando o usuário não as informa.

O clube usa o sistema no dia a dia com um único clube, uma rodada aberta
por vez e a temporada do Óscar do ano corrente. Obrigar quem digita a
colar um UUID em todo comando seria ruído puro, então os comandos aceitam
os ids como opcionais e caem aqui quando não vêm.

Nada disto é regra de negócio: é conveniência de interface. Por isso as
funções só leem dos repositórios e falham com `CliError` — nunca alteram
estado nem decidem algo que o domínio deveria decidir.
"""

from __future__ import annotations

from uuid import UUID

from filmes_e_cubos.adapters.interfaces.cli.contexto import Contexto
from filmes_e_cubos.adapters.interfaces.cli.erros import CliError
from filmes_e_cubos.domain.entities.clube import Clube
from filmes_e_cubos.domain.entities.rodada import Rodada
from filmes_e_cubos.domain.entities.temporada_oscar import TemporadaOscar
from filmes_e_cubos.domain.value_objects.identificadores import (
    ClubeId,
    RodadaId,
    TemporadaOscarId,
)


def resolver_clube(contexto: Contexto, clube_id: UUID | None) -> Clube:
    """O clube informado ou, se houver exatamente um cadastrado, esse."""
    if clube_id is not None:
        clube = contexto.clubes.buscar_por_id(ClubeId(clube_id))
        if clube is None:
            raise CliError(f"Clube {clube_id} não encontrado.")
        return clube

    clubes = contexto.clubes.listar_todos()
    if not clubes:
        raise CliError("Nenhum clube cadastrado. Crie um com `filmes-e-cubos clube criar`.")
    if len(clubes) > 1:
        raise CliError(
            "Há mais de um clube cadastrado — informe qual com --clube-id "
            "(veja os ids em `filmes-e-cubos clube listar`)."
        )
    return clubes[0]


def resolver_rodada(
    contexto: Contexto, rodada_id: UUID | None, clube_id: UUID | None = None
) -> Rodada:
    """A rodada informada ou a rodada aberta do clube resolvido."""
    if rodada_id is not None:
        rodada = contexto.rodadas.buscar_por_id(RodadaId(rodada_id))
        if rodada is None:
            raise CliError(f"Rodada {rodada_id} não encontrada.")
        return rodada

    clube = resolver_clube(contexto, clube_id)
    rodada = contexto.rodadas.buscar_aberta_por_clube(clube.id)
    if rodada is None:
        raise CliError(
            f"O clube {clube.nome} não tem rodada aberta. "
            "Abra uma com `filmes-e-cubos rodada abrir`."
        )
    return rodada


def resolver_temporada(
    contexto: Contexto, temporada_id: UUID | None, clube_id: UUID | None = None
) -> TemporadaOscar:
    """A temporada informada ou a do ano corrente no clube resolvido."""
    if temporada_id is not None:
        temporada = contexto.temporadas.buscar_por_id(TemporadaOscarId(temporada_id))
        if temporada is None:
            raise CliError(f"Temporada {temporada_id} não encontrada.")
        return temporada

    clube = resolver_clube(contexto, clube_id)
    ano = contexto.relogio.hoje().year
    temporada = contexto.temporadas.buscar_por_clube_e_ano(clube.id, ano)
    if temporada is None:
        raise CliError(
            f"O clube {clube.nome} não tem temporada do Óscar de {ano}. "
            "Abra uma com `filmes-e-cubos oscar temporada abrir` ou informe --temporada-id."
        )
    return temporada
