"""Implementação fake de `RelogioService`, com data/hora fixas e controláveis."""

from __future__ import annotations

from datetime import date, datetime


class RelogioFake:
    def __init__(self, agora: datetime) -> None:
        self._agora = agora

    def hoje(self) -> date:
        return self._agora.date()

    def agora(self) -> datetime:
        return self._agora
