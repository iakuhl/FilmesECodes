"""Entidade que representa uma edição anual do Óscar do Filmes e Cubos."""

from __future__ import annotations

from datetime import date
from typing import Final
from uuid import uuid4

from filmes_e_cubos.domain.exceptions.oscar import (
    AcaoForaDaFaseError,
    NumeroDeNomeacoesInvalidoError,
    TemporadaOscarInvalidaError,
)
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId, TemporadaOscarId
from filmes_e_cubos.domain.value_objects.status import StatusTemporadaOscar

NOMEACOES_POR_CATEGORIA_PADRAO: Final = 5
"""Quantas nomeações cada categoria tem, salvo outra escolha ao abrir a edição."""

MINIMO_DE_NOMEACOES_POR_CATEGORIA: Final = 2
"""A votação dupla pede duas opções distintas, então uma categoria precisa de ao menos 2."""

_PROXIMO_STATUS: dict[StatusTemporadaOscar, StatusTemporadaOscar] = {
    StatusTemporadaOscar.EM_PREPARACAO: StatusTemporadaOscar.ABERTA_PARA_INDICACOES,
    StatusTemporadaOscar.ABERTA_PARA_INDICACOES: StatusTemporadaOscar.EM_VOTACAO,
    StatusTemporadaOscar.EM_VOTACAO: StatusTemporadaOscar.APURADA,
    StatusTemporadaOscar.APURADA: StatusTemporadaOscar.ENCERRADA,
}

_ACEITAM_CATEGORIAS: Final = frozenset(
    {StatusTemporadaOscar.EM_PREPARACAO, StatusTemporadaOscar.ABERTA_PARA_INDICACOES}
)


class TemporadaOscar:
    """Uma edição anual do Óscar do clube, com suas categorias e apuração.

    O ciclo de vida é fixo e avança um passo por vez, sempre por decisão
    de quem administra: em preparação (define categorias) → aberta para
    indicações (nomeia filmes; ainda aceita categorias) → em votação (os
    membros votam; nomeações travadas) → apurada → encerrada (nada muda).
    Cada ação confere se a fase atual a permite.

    Todas as categorias da edição têm o mesmo número de nomeações,
    escolhido ao abrir a edição (decisão 17 de docs/PENDENCIAS.md).
    """

    def __init__(
        self,
        *,
        id: TemporadaOscarId,
        clube_id: ClubeId,
        ano: int,
        nome: str,
        status: StatusTemporadaOscar = StatusTemporadaOscar.EM_PREPARACAO,
        data_evento: date | None = None,
        nomeacoes_por_categoria: int = NOMEACOES_POR_CATEGORIA_PADRAO,
    ) -> None:
        if nomeacoes_por_categoria < MINIMO_DE_NOMEACOES_POR_CATEGORIA:
            raise NumeroDeNomeacoesInvalidoError(
                f"Cada categoria precisa de ao menos {MINIMO_DE_NOMEACOES_POR_CATEGORIA} "
                f"nomeações, recebido: {nomeacoes_por_categoria}."
            )
        self._id = id
        self._clube_id = clube_id
        self._ano = ano
        self._nome = nome
        self._status = status
        self._data_evento = data_evento
        self._nomeacoes_por_categoria = nomeacoes_por_categoria

    @classmethod
    def abrir(
        cls,
        *,
        clube_id: ClubeId,
        ano: int,
        nome: str,
        nomeacoes_por_categoria: int = NOMEACOES_POR_CATEGORIA_PADRAO,
    ) -> TemporadaOscar:
        return cls(
            id=TemporadaOscarId(uuid4()),
            clube_id=clube_id,
            ano=ano,
            nome=nome,
            nomeacoes_por_categoria=nomeacoes_por_categoria,
        )

    @property
    def id(self) -> TemporadaOscarId:
        return self._id

    @property
    def clube_id(self) -> ClubeId:
        return self._clube_id

    @property
    def ano(self) -> int:
        return self._ano

    @property
    def nome(self) -> str:
        return self._nome

    @property
    def status(self) -> StatusTemporadaOscar:
        return self._status

    @property
    def data_evento(self) -> date | None:
        return self._data_evento

    @property
    def nomeacoes_por_categoria(self) -> int:
        return self._nomeacoes_por_categoria

    @property
    def proximo_status(self) -> StatusTemporadaOscar | None:
        """A fase seguinte do ciclo; `None` numa edição encerrada."""
        return _PROXIMO_STATUS.get(self._status)

    def avancar_para(self, novo_status: StatusTemporadaOscar) -> None:
        """Avança a temporada para o próximo status do seu ciclo de vida."""
        if _PROXIMO_STATUS.get(self._status) is not novo_status:
            raise TemporadaOscarInvalidaError(
                f"Não é possível avançar de {self._status} para {novo_status}."
            )
        self._status = novo_status

    def definir_data_evento(self, data_evento: date) -> None:
        """Marca (ou remarca) o dia da cerimônia; uma edição encerrada não muda mais."""
        if self._status is StatusTemporadaOscar.ENCERRADA:
            raise AcaoForaDaFaseError(
                f"A edição {self._nome} está encerrada: a data do evento não muda mais."
            )
        self._data_evento = data_evento

    def verificar_aceita_categorias(self) -> None:
        """Categorias se definem na preparação e enquanto as nomeações estão abertas."""
        if self._status not in _ACEITAM_CATEGORIAS:
            raise AcaoForaDaFaseError(
                f"A edição {self._nome} não aceita categorias novas na fase atual."
            )

    def verificar_aceita_nomeacoes(self) -> None:
        """Filmes só são nomeados enquanto a edição está aberta para indicações."""
        if self._status is not StatusTemporadaOscar.ABERTA_PARA_INDICACOES:
            raise AcaoForaDaFaseError(
                f"A edição {self._nome} só aceita nomeações quando está aberta para indicações."
            )
