"""Testes do envio por SMTP contra um servidor SMTP de verdade, mínimo, local."""

from __future__ import annotations

import socket
import socketserver
import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from email import message_from_bytes, policy

import pytest

from filmes_e_cubos.adapters.servicos.enviador_smtp import (
    ConfiguracaoSmtp,
    EnviadorSmtp,
    EnvioDesligado,
    enviador_do_ambiente,
)
from filmes_e_cubos.application.ports.enviador_de_email import MensagemDeEmail
from filmes_e_cubos.domain.exceptions.email import (
    EnvioDeEmailIndisponivelError,
    FalhaNoEnvioDeEmailError,
)
from filmes_e_cubos.domain.value_objects.endereco_de_email import EnderecoDeEmail

MENSAGEM = MensagemDeEmail(
    destinatario=EnderecoDeEmail("cerimonia@clube.com"),
    assunto="Placar do Óscar 2026",
    corpo="MELHOR VEÍCULO\n  4 pontos  Parasita\n",
)


@dataclass
class CaixaDeEntrada:
    remetentes: list[str] = field(default_factory=list)
    destinatarios: list[str] = field(default_factory=list)
    mensagens: list[bytes] = field(default_factory=list)


class _ConversaSmtp(socketserver.StreamRequestHandler):
    """O lado do servidor de uma conversa SMTP (RFC 5321), só o que o cliente usa."""

    caixa: CaixaDeEntrada

    def handle(self) -> None:
        self._responder("220 teste ESMTP")
        while linha := self.rfile.readline().decode().strip():
            comando = linha.split(" ", 1)[0].upper()
            if comando in ("EHLO", "HELO"):
                self._responder("250 teste")
            elif comando == "MAIL":
                self.caixa.remetentes.append(linha)
                self._responder("250 OK")
            elif comando == "RCPT":
                self.caixa.destinatarios.append(linha)
                self._responder("250 OK")
            elif comando == "DATA":
                self._responder("354 Termine com <CRLF>.<CRLF>")
                corpo = b""
                while (parte := self.rfile.readline()) != b".\r\n":
                    corpo += parte
                self.caixa.mensagens.append(corpo)
                self._responder("250 OK")
            elif comando == "QUIT":
                self._responder("221 Tchau")
                return
            else:
                self._responder("250 OK")

    def _responder(self, texto: str) -> None:
        self.wfile.write(f"{texto}\r\n".encode())


@pytest.fixture
def servidor_smtp() -> Iterator[tuple[int, CaixaDeEntrada]]:
    caixa = CaixaDeEntrada()
    conversa = type("Conversa", (_ConversaSmtp,), {"caixa": caixa})
    with socketserver.ThreadingTCPServer(("127.0.0.1", 0), conversa) as servidor:
        threading.Thread(target=servidor.serve_forever, daemon=True).start()
        yield servidor.server_address[1], caixa
        servidor.shutdown()


def test_mensagem_chega_ao_servidor(servidor_smtp: tuple[int, CaixaDeEntrada]) -> None:
    porta, caixa = servidor_smtp
    configuracao = ConfiguracaoSmtp(
        servidor="127.0.0.1", porta=porta, seguranca="nenhuma", remetente="clube@filmes.com"
    )

    EnviadorSmtp(configuracao).enviar(MENSAGEM)

    [recebida] = caixa.mensagens
    email = message_from_bytes(recebida, policy=policy.default)
    assert email["To"] == "cerimonia@clube.com"
    assert email["From"] == "clube@filmes.com"
    assert email["Subject"] == "Placar do Óscar 2026"
    assert "4 pontos  Parasita" in email.get_content()
    assert "cerimonia@clube.com" in caixa.destinatarios[0]


def test_servidor_fora_do_ar_vira_falha_no_envio() -> None:
    with socket.socket() as livre:
        livre.bind(("127.0.0.1", 0))
        porta = livre.getsockname()[1]
    configuracao = ConfiguracaoSmtp(servidor="127.0.0.1", porta=porta, seguranca="nenhuma")

    with pytest.raises(FalhaNoEnvioDeEmailError):
        EnviadorSmtp(configuracao).enviar(MENSAGEM)


def test_sem_servidor_configurado_o_envio_fica_desligado() -> None:
    enviador = enviador_do_ambiente({})

    assert isinstance(enviador, EnvioDesligado)
    with pytest.raises(EnvioDeEmailIndisponivelError, match="FILMES_E_CUBOS_SMTP_SERVIDOR"):
        enviador.enviar(MENSAGEM)


def test_configuracao_vem_do_ambiente() -> None:
    configuracao = ConfiguracaoSmtp.do_ambiente(
        {
            "FILMES_E_CUBOS_SMTP_SERVIDOR": "smtp.exemplo.com",
            "FILMES_E_CUBOS_SMTP_SEGURANCA": "ssl",
            "FILMES_E_CUBOS_SMTP_USUARIO": "clube@exemplo.com",
            "FILMES_E_CUBOS_SMTP_SENHA": "segredo",
        }
    )

    assert configuracao == ConfiguracaoSmtp(
        servidor="smtp.exemplo.com",
        porta=465,
        seguranca="ssl",
        usuario="clube@exemplo.com",
        senha="segredo",
        remetente="clube@exemplo.com",
    )
    assert isinstance(enviador_do_ambiente({"FILMES_E_CUBOS_SMTP_SERVIDOR": "x"}), EnviadorSmtp)


def test_seguranca_desconhecida_e_recusada() -> None:
    with pytest.raises(ValueError, match="SEGURANCA"):
        ConfiguracaoSmtp.do_ambiente(
            {"FILMES_E_CUBOS_SMTP_SERVIDOR": "x", "FILMES_E_CUBOS_SMTP_SEGURANCA": "tls"}
        )
