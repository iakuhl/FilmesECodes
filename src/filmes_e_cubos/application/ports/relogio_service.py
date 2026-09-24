"""Contrato para obtenção da data/hora atual, isolando o domínio do relógio do sistema."""

from datetime import date, datetime
from typing import Protocol


class RelogioService(Protocol):
    def hoje(self) -> date: ...

    def agora(self) -> datetime: ...
