"""Contrato do módulo de histórico: ler sessões passadas registradas fora do sistema.

O clube assistiu a filmes antes de o sistema existir, e esse histórico
está espalhado em planilhas, mensagens e anotações. O módulo de histórico
(decisão 3 de docs/PENDENCIAS.md) vai trazê-lo para dentro — mas como
casar os nomes com os membros e filmes cadastrados, a que rodadas as
sessões antigas pertencem e como elas convivem com a regra de não repetir
filmes ainda estão em aberto (questão 1 de PENDENCIAS.md).

Por isso, por ora, só existe o contrato da **leitura**: cada formato de
arquivo vira um adapter que implementa `LeitorDeHistorico` e entrega os
registros como vieram, com os nomes exatamente como aparecem na fonte —
sem interpretá-los nem consultar o banco. Conciliar os registros com os
cadastros e gravá-los serão casos de uso próprios, quando essas regras
forem decididas.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True, slots=True)
class NotaHistorica:
    """A avaliação de uma pessoa numa sessão passada, como a fonte a registrou."""

    membro: str
    nota: Decimal | None
    """`None` quando a pessoa cochilou (dorminhoco)."""
    comentario: str | None = None


@dataclass(frozen=True, slots=True)
class SessaoHistorica:
    """Uma sessão passada, com os nomes exatamente como aparecem na fonte."""

    origem: str
    """Onde o registro está na fonte (ex.: `"2023.csv, linha 12"`), para relatar problemas."""
    data_sessao: date
    titulo_do_filme: str
    ano_do_filme: int | None = None
    indicado_por: str | None = None
    """Quem indicou o filme; `None` numa sessão democracia ou quando a fonte não diz."""
    democracia: bool = False
    presentes: tuple[str, ...] = ()
    notas: tuple[NotaHistorica, ...] = ()


@dataclass(frozen=True, slots=True)
class ProblemaDeLeitura:
    """Um trecho da fonte que não pôde ser lido.

    O leitor relata o problema e segue adiante, para que quem importa veja
    de uma vez tudo o que precisa corrigir na fonte.
    """

    origem: str
    mensagem: str


@dataclass(frozen=True, slots=True)
class LeituraDeHistorico:
    """O resultado de ler uma fonte: as sessões lidas e os trechos que falharam."""

    sessoes: tuple[SessaoHistorica, ...]
    problemas: tuple[ProblemaDeLeitura, ...] = ()


class LeitorDeHistorico(Protocol):
    """Lê o histórico de sessões de um arquivo num formato específico.

    Haverá uma implementação por formato aceito (quais, ainda está em
    aberto). O conteúdo chega em bytes, para servir igualmente a um
    arquivo local (CLI) e a um envio pela web; o nome do arquivo ajuda a
    compor a `origem` de cada registro.
    """

    def ler(self, conteudo: bytes, *, nome_do_arquivo: str) -> LeituraDeHistorico: ...
