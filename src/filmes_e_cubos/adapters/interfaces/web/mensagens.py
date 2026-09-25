"""Avisos exibidos na próxima página ("flash") e o tratamento de erros de negócio.

Toda ação da web segue o padrão *Post/Redirect/Get*: o formulário faz um
POST, a ação roda, e a resposta redireciona para uma página comum. O
resultado da ação — sucesso ou o motivo da recusa — viaja até essa
página como um aviso guardado na sessão (um cookie assinado) e é
consumido na primeira página que o exibir.

As mensagens do domínio identificam as entidades pelo id, o que é ótimo
num log e ruim numa tela. Para os erros que uma pessoa encontra no uso
normal, `MENSAGENS_AMIGAVEIS` traz um texto próprio para a web; os demais
exibem a mensagem do domínio como veio.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Final, Literal

from starlette.requests import Request

from filmes_e_cubos.domain.exceptions.avaliacao import (
    AvaliacaoDuplicadaError,
    MembroAusenteNaSessaoError,
)
from filmes_e_cubos.domain.exceptions.base import DomainError
from filmes_e_cubos.domain.exceptions.indicacao import (
    FilmeRepetidoNoClubeError,
    IndicacaoDuplicadaError,
    TransicaoDeStatusInvalidaError,
)
from filmes_e_cubos.domain.exceptions.membro import MembroInativoError
from filmes_e_cubos.domain.exceptions.oscar import (
    CategoriaJaApuradaError,
    FilmeNaoAssistidoError,
    FilmeNaoAssistidoNoAnoDaTemporadaError,
    NomeacaoInvalidaError,
    VencedorDemocraciaNaoInformadoError,
)
from filmes_e_cubos.domain.exceptions.rodada import (
    RodadaJaAbertaError,
    RodadaJaEncerradaError,
    RodadaLotadaError,
    RodadaNaoEncerravelError,
)
from filmes_e_cubos.domain.exceptions.sorteio import NenhumaIndicacaoElegivelError

TipoDeAviso = Literal["sucesso", "erro"]

_CHAVE_NA_SESSAO: Final = "avisos"

MENSAGENS_AMIGAVEIS: Final[dict[type[DomainError], str]] = {
    AvaliacaoDuplicadaError: "Esse membro já avaliou esta sessão.",
    CategoriaJaApuradaError: "Essa categoria já foi apurada.",
    FilmeNaoAssistidoError: "Esse filme ainda não foi assistido pelo clube.",
    FilmeNaoAssistidoNoAnoDaTemporadaError: (
        "Só concorrem filmes assistidos pelo clube no ano desta edição."
    ),
    FilmeRepetidoNoClubeError: (
        "Esse filme já passou pelo clube: foi assistido ou já está indicado."
    ),
    IndicacaoDuplicadaError: "Esse membro já indicou um filme nesta rodada.",
    MembroAusenteNaSessaoError: "Só quem esteve na sessão pode avaliá-la.",
    MembroInativoError: "Esse membro está desativado.",
    NenhumaIndicacaoElegivelError: "Não há indicações pendentes para sortear.",
    NomeacaoInvalidaError: "Escolha uma das nomeações desta categoria.",
    RodadaJaAbertaError: "O clube já tem uma rodada aberta.",
    RodadaJaEncerradaError: "Essa rodada já foi encerrada.",
    RodadaLotadaError: "A rodada já tem todas as indicações que o clube permite.",
    RodadaNaoEncerravelError: (
        "A rodada só pode ser encerrada quando todas as indicações tiverem sido assistidas."
    ),
    TransicaoDeStatusInvalidaError: "Essa indicação já foi assistida.",
    VencedorDemocraciaNaoInformadoError: (
        "O filme vencedor veio de uma sessão democracia: escolha quem leva o troféu."
    ),
}


@dataclass(frozen=True)
class Aviso:
    tipo: TipoDeAviso
    texto: str


class FormularioInvalidoError(Exception):
    """Um campo de formulário que nem chega a ser uma pergunta para o domínio.

    Ex.: "abc" no campo de ano. Vira aviso de erro exatamente como um erro
    de regra de negócio.
    """


def avisar(request: Request, tipo: TipoDeAviso, texto: str) -> None:
    """Guarda um aviso para a próxima página exibida."""
    avisos = list(request.session.get(_CHAVE_NA_SESSAO, []))
    avisos.append([tipo, texto])
    request.session[_CHAVE_NA_SESSAO] = avisos


def consumir_avisos(request: Request) -> list[Aviso]:
    """Os avisos pendentes, que deixam de estar pendentes ao serem lidos."""
    return [Aviso(tipo, texto) for tipo, texto in request.session.pop(_CHAVE_NA_SESSAO, [])]


def mensagem_para_pessoas(erro: DomainError) -> str:
    """O texto a exibir para um erro de regra de negócio."""
    for tipo in type(erro).__mro__:
        if tipo in MENSAGENS_AMIGAVEIS:
            return MENSAGENS_AMIGAVEIS[tipo]
    return str(erro)


@contextmanager
def recusas_viram_avisos(request: Request) -> Iterator[None]:
    """Transforma a recusa de uma ação (regra de negócio ou campo inválido) em aviso.

    Uso típico numa rota de formulário:

        with recusas_viram_avisos(request):
            contexto.abrir_nova_rodada.executar(clube_id=clube.id)
            avisar(request, "sucesso", "Rodada aberta.")
        return redirecionar(...)

    Se a ação for recusada, o aviso de sucesso nunca é registrado, a
    recusa vira um aviso de erro e o redirecionamento acontece igual.
    """
    try:
        yield
    except DomainError as erro:
        avisar(request, "erro", mensagem_para_pessoas(erro))
    except FormularioInvalidoError as erro:
        avisar(request, "erro", str(erro))
