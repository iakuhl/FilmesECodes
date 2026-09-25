"""Implementação de exemplo de `LeitorDeHistorico`, para testes.

Lê um formato mínimo, uma sessão por linha: `AAAA-MM-DD;Título;Indicador`
(indicador vazio = sessão democracia). Serve de referência de como um
leitor real deve se comportar: relatar a linha ruim e seguir adiante.
"""

from __future__ import annotations

from datetime import date

from filmes_e_cubos.application.ports.leitor_de_historico import (
    LeituraDeHistorico,
    ProblemaDeLeitura,
    SessaoHistorica,
)


class LeitorDeHistoricoFake:
    def ler(self, conteudo: bytes, *, nome_do_arquivo: str) -> LeituraDeHistorico:
        sessoes: list[SessaoHistorica] = []
        problemas: list[ProblemaDeLeitura] = []
        for numero, linha in enumerate(conteudo.decode("utf-8").splitlines(), start=1):
            origem = f"{nome_do_arquivo}, linha {numero}"
            campos = linha.split(";")
            try:
                data_sessao = date.fromisoformat(campos[0])
                titulo, indicador = campos[1], campos[2]
            except (ValueError, IndexError):
                problemas.append(
                    ProblemaDeLeitura(origem=origem, mensagem=f"Linha ilegível: {linha!r}")
                )
                continue
            sessoes.append(
                SessaoHistorica(
                    origem=origem,
                    data_sessao=data_sessao,
                    titulo_do_filme=titulo,
                    indicado_por=indicador or None,
                    democracia=not indicador,
                )
            )
        return LeituraDeHistorico(sessoes=tuple(sessoes), problemas=tuple(problemas))
