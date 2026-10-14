"""Contrato para enviar e-mails, isolando os casos de uso do servidor de e-mail.

Genérico de propósito: hoje leva o placar do Óscar a quem monta a
cerimônia (decisão 27 de docs/PENDENCIAS.md); na Fase 5, pode levar os
convites de entrada no clube.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from filmes_e_cubos.domain.value_objects.endereco_de_email import EnderecoDeEmail


@dataclass(frozen=True)
class MensagemDeEmail:
    destinatario: EnderecoDeEmail
    assunto: str
    corpo: str
    """Texto puro."""


class EnviadorDeEmail(Protocol):
    def enviar(self, mensagem: MensagemDeEmail) -> None:
        """Entrega a mensagem ao servidor de e-mail.

        Levanta `EnvioDeEmailIndisponivelError` sem servidor configurado e
        `FalhaNoEnvioDeEmailError` se ele recusar ou não responder.
        """
        ...
