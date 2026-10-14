"""Implementação fake de `EnviadorDeEmail`: guarda as mensagens em vez de enviá-las."""

from __future__ import annotations

from filmes_e_cubos.application.ports.enviador_de_email import MensagemDeEmail


class EnviadorDeEmailFake:
    def __init__(self) -> None:
        self.enviadas: list[MensagemDeEmail] = []

    def enviar(self, mensagem: MensagemDeEmail) -> None:
        self.enviadas.append(mensagem)
