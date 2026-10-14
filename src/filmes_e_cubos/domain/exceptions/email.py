"""Exceções do envio de e-mail — o caminho do placar até quem monta a cerimônia."""

from filmes_e_cubos.domain.exceptions.base import DomainError


class EnderecoDeEmailInvalidoError(DomainError):
    """Levantada quando o destinatário nem tem a forma de um endereço de e-mail."""


class EnvioDeEmailIndisponivelError(DomainError):
    """Levantada ao enviar um e-mail sem o servidor de e-mail configurado."""


class FalhaNoEnvioDeEmailError(DomainError):
    """Levantada quando o servidor de e-mail recusa a mensagem ou não responde."""
