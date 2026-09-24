"""Entidade que representa uma edição anual do Óscar do Filmes e Cubos."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

from filmes_e_cubos.domain.exceptions.oscar import TemporadaOscarInvalidaError
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId, TemporadaOscarId
from filmes_e_cubos.domain.value_objects.status import StatusTemporadaOscar

_PROXIMO_STATUS: dict[StatusTemporadaOscar, StatusTemporadaOscar] = {
    StatusTemporadaOscar.EM_PREPARACAO: StatusTemporadaOscar.ABERTA_PARA_INDICACOES,
    StatusTemporadaOscar.ABERTA_PARA_INDICACOES: StatusTemporadaOscar.APURADA,
    StatusTemporadaOscar.APURADA: StatusTemporadaOscar.ENCERRADA,
}


class TemporadaOscar:
    """Uma edição anual do Óscar do clube, com suas categorias e apuração."""

    def __init__(
        self,
        *,
        id: TemporadaOscarId,
        clube_id: ClubeId,
        ano: int,
        nome: str,
        status: StatusTemporadaOscar = StatusTemporadaOscar.EM_PREPARACAO,
        data_evento: date | None = None,
    ) -> None:
        self._id = id
        self._clube_id = clube_id
        self._ano = ano
        self._nome = nome
        self._status = status
        self._data_evento = data_evento

    @classmethod
    def abrir(cls, *, clube_id: ClubeId, ano: int, nome: str) -> TemporadaOscar:
        return cls(id=TemporadaOscarId(uuid4()), clube_id=clube_id, ano=ano, nome=nome)

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

    def avancar_para(self, novo_status: StatusTemporadaOscar) -> None:
        """Avança a temporada para o próximo status do seu ciclo de vida."""
        if _PROXIMO_STATUS.get(self._status) is not novo_status:
            raise TemporadaOscarInvalidaError(
                f"Não é possível avançar de {self._status} para {novo_status}."
            )
        self._status = novo_status

    def definir_data_evento(self, data_evento: date) -> None:
        self._data_evento = data_evento
