"""Envio de e-mail por SMTP, configurado por variáveis de ambiente.

Qualquer serviço que fale SMTP serve (Gmail com senha de app, Brevo,
Resend, o servidor do próprio domínio...). Sem servidor configurado, o
envio é recusado com uma mensagem que diz o que definir — o resto do
sistema funciona normalmente.

| Variável | Padrão | O que é |
|---|---|---|
| `FILMES_E_CUBOS_SMTP_SERVIDOR` | — | Servidor SMTP; sem ele, o envio fica desligado. |
| `FILMES_E_CUBOS_SMTP_PORTA` | 587 | Porta. |
| `FILMES_E_CUBOS_SMTP_SEGURANCA` | `starttls` | `starttls`, `ssl` (porta 465) ou `nenhuma`. |
| `FILMES_E_CUBOS_SMTP_USUARIO` | — | Usuário, se o servidor pedir login. |
| `FILMES_E_CUBOS_SMTP_SENHA` | — | Senha desse usuário. |
| `FILMES_E_CUBOS_SMTP_REMETENTE` | o usuário | Endereço que aparece como remetente. |
"""

from __future__ import annotations

import os
import smtplib
from collections.abc import Mapping
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Final, Literal

from filmes_e_cubos.application.ports.enviador_de_email import EnviadorDeEmail, MensagemDeEmail
from filmes_e_cubos.domain.exceptions.email import (
    EnvioDeEmailIndisponivelError,
    FalhaNoEnvioDeEmailError,
)

PREFIXO: Final = "FILMES_E_CUBOS_SMTP_"

Seguranca = Literal["starttls", "ssl", "nenhuma"]

_SEGURANCAS: Final[tuple[Seguranca, ...]] = ("starttls", "ssl", "nenhuma")
_ESPERA_EM_SEGUNDOS: Final = 20


@dataclass(frozen=True)
class ConfiguracaoSmtp:
    servidor: str
    porta: int = 587
    seguranca: Seguranca = "starttls"
    usuario: str | None = None
    senha: str | None = None
    remetente: str | None = None

    @classmethod
    def do_ambiente(cls, ambiente: Mapping[str, str]) -> ConfiguracaoSmtp | None:
        """A configuração das variáveis `FILMES_E_CUBOS_SMTP_*`; `None` sem servidor."""
        servidor = ambiente.get(f"{PREFIXO}SERVIDOR", "").strip()
        if not servidor:
            return None
        seguranca = ambiente.get(f"{PREFIXO}SEGURANCA", "starttls").strip().lower()
        if seguranca not in _SEGURANCAS:
            raise ValueError(
                f"{PREFIXO}SEGURANCA deve ser starttls, ssl ou nenhuma; recebido: {seguranca!r}."
            )
        usuario = ambiente.get(f"{PREFIXO}USUARIO") or None
        return cls(
            servidor=servidor,
            porta=int(ambiente.get(f"{PREFIXO}PORTA") or (465 if seguranca == "ssl" else 587)),
            seguranca=seguranca,
            usuario=usuario,
            senha=ambiente.get(f"{PREFIXO}SENHA") or None,
            remetente=ambiente.get(f"{PREFIXO}REMETENTE") or usuario,
        )


class EnviadorSmtp:
    """Implementação de `EnviadorDeEmail` sobre o `smtplib` da biblioteca padrão."""

    def __init__(self, configuracao: ConfiguracaoSmtp) -> None:
        self._configuracao = configuracao

    def enviar(self, mensagem: MensagemDeEmail) -> None:
        configuracao = self._configuracao
        email = EmailMessage()
        email["From"] = configuracao.remetente or f"filmes-e-cubos@{configuracao.servidor}"
        email["To"] = str(mensagem.destinatario)
        email["Subject"] = mensagem.assunto
        email.set_content(mensagem.corpo)
        classe = smtplib.SMTP_SSL if configuracao.seguranca == "ssl" else smtplib.SMTP
        try:
            with classe(
                configuracao.servidor, configuracao.porta, timeout=_ESPERA_EM_SEGUNDOS
            ) as conexao:
                if configuracao.seguranca == "starttls":
                    conexao.starttls()
                if configuracao.usuario:
                    conexao.login(configuracao.usuario, configuracao.senha or "")
                conexao.send_message(email)
        except (smtplib.SMTPException, OSError) as erro:
            raise FalhaNoEnvioDeEmailError(
                f"O servidor de e-mail recusou a mensagem ou não respondeu: {erro}"
            ) from erro


class EnvioDesligado:
    """O `EnviadorDeEmail` de quando não há servidor configurado: recusa explicando."""

    def enviar(self, mensagem: MensagemDeEmail) -> None:
        raise EnvioDeEmailIndisponivelError(
            f"O envio de e-mail não está configurado: defina {PREFIXO}SERVIDOR (e, se o "
            "servidor pedir, usuário e senha) nas variáveis de ambiente."
        )


def enviador_do_ambiente(ambiente: Mapping[str, str] | None = None) -> EnviadorDeEmail:
    configuracao = ConfiguracaoSmtp.do_ambiente(os.environ if ambiente is None else ambiente)
    return EnvioDesligado() if configuracao is None else EnviadorSmtp(configuracao)
