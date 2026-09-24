"""Entidade que representa uma rodada de indicações do clube."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

from filmes_e_cubos.domain.exceptions.rodada import RodadaJaEncerradaError
from filmes_e_cubos.domain.value_objects.identificadores import ClubeId, RodadaId
from filmes_e_cubos.domain.value_objects.status import StatusRodada


class Rodada:
    """Um ciclo de indicações de filmes de um clube.

    Não mantém a lista de `Indicacao` em memória (essas são acessadas via
    `IndicacaoRepository` por `rodada_id`), então os invariantes que
    dependem delas — como "só encerra se todas as indicações estiverem
    assistidas" — são verificados pelo caso de uso `EncerrarRodada`, não
    por este objeto isoladamente.
    """

    def __init__(
        self,
        *,
        id: RodadaId,
        clube_id: ClubeId,
        numero: int,
        data_inicio: date,
        status: StatusRodada = StatusRodada.ABERTA,
        data_encerramento: date | None = None,
    ) -> None:
        self._id = id
        self._clube_id = clube_id
        self._numero = numero
        self._data_inicio = data_inicio
        self._status = status
        self._data_encerramento = data_encerramento

    @classmethod
    def abrir(cls, *, clube_id: ClubeId, numero: int, data_inicio: date) -> Rodada:
        return cls(id=RodadaId(uuid4()), clube_id=clube_id, numero=numero, data_inicio=data_inicio)

    @property
    def id(self) -> RodadaId:
        return self._id

    @property
    def clube_id(self) -> ClubeId:
        return self._clube_id

    @property
    def numero(self) -> int:
        return self._numero

    @property
    def status(self) -> StatusRodada:
        return self._status

    @property
    def data_inicio(self) -> date:
        return self._data_inicio

    @property
    def data_encerramento(self) -> date | None:
        return self._data_encerramento

    @property
    def esta_aberta(self) -> bool:
        return self._status is StatusRodada.ABERTA

    def encerrar(self, *, data_encerramento: date) -> None:
        """Encerra a rodada.

        Verifica apenas a própria transição de status; a regra de que
        todas as indicações precisam estar assistidas é responsabilidade
        do caso de uso `EncerrarRodada`.
        """
        if not self.esta_aberta:
            raise RodadaJaEncerradaError(f"Rodada {self._numero} já está encerrada.")
        self._status = StatusRodada.ENCERRADA
        self._data_encerramento = data_encerramento
