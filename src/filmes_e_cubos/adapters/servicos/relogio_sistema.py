"""Implementação de `RelogioService` usando o relógio real do sistema."""

from __future__ import annotations

from datetime import date, datetime


class RelogioSistema:
    def hoje(self) -> date:
        return date.today()

    def agora(self) -> datetime:
        return datetime.now()
