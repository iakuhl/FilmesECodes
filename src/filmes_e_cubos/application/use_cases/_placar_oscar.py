"""O placar da votação do Óscar em texto — o corpo do e-mail para quem monta a cerimônia.

Só a pontuação de cada nomeação, nunca as cédulas (decisão 27 de
docs/PENDENCIAS.md). Cada categoria traz o placar de todos os seus
turnos, em ordem de pontos, e assinala o empate absoluto e a vitória de
um filme democracia, em que o grupo escolhe quem leva o troféu
(interpretação 15).
"""

from __future__ import annotations

from dataclasses import dataclass

from filmes_e_cubos.domain.entities.turno_de_votacao import TurnoDeVotacao
from filmes_e_cubos.domain.value_objects.identificadores import NomeacaoOscarId
from filmes_e_cubos.domain.value_objects.status import ModoDeVotacao


@dataclass(frozen=True)
class NomeacaoNoPlacar:
    titulo: str
    indicado_por: str | None
    """Nome de quem indicou o filme; `None` numa sessão democracia."""


@dataclass(frozen=True)
class CategoriaNoPlacar:
    nome: str
    turnos: list[TurnoDeVotacao]
    """Do 1º ao último, todos apurados."""
    nomeacoes: dict[NomeacaoOscarId, NomeacaoNoPlacar]


def redigir_placar(
    *, edicao: str, eleitores: list[str], categorias: list[CategoriaNoPlacar]
) -> str:
    linhas = [
        f"{edicao} — placar da votação",
        "",
        "Este é o placar para montar a cerimônia: os pontos de cada nomeação, turno a turno.",
        "As cédulas são secretas e não vêm aqui.",
        f"Eleitores ({len(eleitores)}): {', '.join(eleitores)}.",
    ]
    for categoria in categorias:
        linhas += ["", categoria.nome.upper()]
        for turno, seguinte in zip(categoria.turnos, [*categoria.turnos[1:], None], strict=True):
            linhas.append(_cabecalho(turno))
            linhas += [
                f"  {_pontos(pontos)}  {_nomeacao(categoria, nomeacao)}"
                for nomeacao, pontos in _em_ordem_de_pontos(turno)
            ]
            if seguinte is not None:
                linhas.append(f"  Empate no topo: as empatadas foram ao {seguinte.numero}º turno.")
        linhas += _desfecho(categoria)
    return "\n".join(linhas) + "\n"


def _cabecalho(turno: TurnoDeVotacao) -> str:
    if turno.modo is ModoDeVotacao.DUPLA:
        return f"{turno.numero}º turno — 1ª opção vale 2 pontos; 2ª opção, 1"
    return (
        f"{turno.numero}º turno — classificação: o 1º lugar vale "
        f"{len(turno.candidatas)} pontos; o último, 1"
    )


def _em_ordem_de_pontos(turno: TurnoDeVotacao) -> list[tuple[NomeacaoOscarId, int]]:
    """Do mais ao menos votado; nos empates, a ordem da cédula (a ordenação é estável)."""
    pares = zip(turno.candidatas, turno.pontuacao or (), strict=True)
    return sorted(pares, key=lambda par: -par[1])


def _pontos(pontos: int) -> str:
    return f"{pontos:>3} {'ponto ' if pontos == 1 else 'pontos'}"


def _nomeacao(categoria: CategoriaNoPlacar, nomeacao_id: NomeacaoOscarId) -> str:
    nomeacao = categoria.nomeacoes[nomeacao_id]
    autoria = (
        f"indicado por {nomeacao.indicado_por}" if nomeacao.indicado_por else "sessão democracia"
    )
    return f"{nomeacao.titulo} — {autoria}"


def _desfecho(categoria: CategoriaNoPlacar) -> list[str]:
    if not categoria.turnos:
        return ["  (Categoria sem votação.)"]
    ultimo = categoria.turnos[-1]
    if ultimo.empate_absoluto:
        return [
            "  Empate absoluto: nenhuma nomeação vence, e o troféu vai para um membro "
            "escolhido pelo grupo."
        ]
    if categoria.nomeacoes[ultimo.lideres[0]].indicado_por is None:
        return [
            "  A mais votada veio de uma sessão democracia: o grupo escolhe quem leva o troféu."
        ]
    return []
