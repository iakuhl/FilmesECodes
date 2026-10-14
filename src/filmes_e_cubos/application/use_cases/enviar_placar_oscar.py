"""Caso de uso: enviar o placar da votação do Óscar a quem monta a cerimônia."""

from __future__ import annotations

from filmes_e_cubos.application.ports.categoria_oscar_repository import CategoriaOscarRepository
from filmes_e_cubos.application.ports.enviador_de_email import EnviadorDeEmail, MensagemDeEmail
from filmes_e_cubos.application.ports.filme_repository import FilmeRepository
from filmes_e_cubos.application.ports.membro_repository import MembroRepository
from filmes_e_cubos.application.ports.nomeacao_oscar_repository import NomeacaoOscarRepository
from filmes_e_cubos.application.ports.temporada_oscar_repository import TemporadaOscarRepository
from filmes_e_cubos.application.ports.turno_de_votacao_repository import (
    TurnoDeVotacaoRepository,
)
from filmes_e_cubos.application.ports.votacao_oscar_repository import VotacaoOscarRepository
from filmes_e_cubos.application.use_cases._placar_oscar import (
    CategoriaNoPlacar,
    NomeacaoNoPlacar,
    redigir_placar,
)
from filmes_e_cubos.domain.entities.categoria_oscar import CategoriaOscar
from filmes_e_cubos.domain.entities.turno_de_votacao import TurnoDeVotacao
from filmes_e_cubos.domain.entities.votacao_oscar import VotacaoOscar
from filmes_e_cubos.domain.exceptions.base import EntidadeNaoEncontradaError
from filmes_e_cubos.domain.exceptions.oscar import AcaoForaDaFaseError, VotacaoEmAndamentoError
from filmes_e_cubos.domain.value_objects.endereco_de_email import EnderecoDeEmail
from filmes_e_cubos.domain.value_objects.identificadores import (
    MembroId,
    NomeacaoOscarId,
    TemporadaOscarId,
)
from filmes_e_cubos.domain.value_objects.status import StatusTemporadaOscar


class EnviarPlacarOscar:
    """Envia o placar da votação por e-mail (decisão 27 de docs/PENDENCIAS.md).

    Ninguém vê o resultado no sistema: quem administra informa o endereço
    e o placar segue direto para lá. Só sai com a votação terminada — sem
    empate a desfazer (decisão 28) — e pode ser enviado de novo, ao mesmo
    ou a outro endereço, até a edição ser encerrada.
    """

    def __init__(
        self,
        temporada_repository: TemporadaOscarRepository,
        categoria_repository: CategoriaOscarRepository,
        nomeacao_repository: NomeacaoOscarRepository,
        filme_repository: FilmeRepository,
        membro_repository: MembroRepository,
        votacao_repository: VotacaoOscarRepository,
        turno_repository: TurnoDeVotacaoRepository,
        enviador: EnviadorDeEmail,
    ) -> None:
        self._temporadas = temporada_repository
        self._categorias = categoria_repository
        self._nomeacoes = nomeacao_repository
        self._filmes = filme_repository
        self._membros = membro_repository
        self._votacoes = votacao_repository
        self._turnos = turno_repository
        self._enviador = enviador

    def executar(self, *, temporada_id: TemporadaOscarId, destinatario: str) -> EnderecoDeEmail:
        temporada = self._temporadas.buscar_por_id(temporada_id)
        if temporada is None:
            raise EntidadeNaoEncontradaError(f"Temporada {temporada_id} não encontrada.")
        if temporada.status is StatusTemporadaOscar.ENCERRADA:
            raise AcaoForaDaFaseError(
                f"A edição {temporada.nome} está encerrada: o placar não é mais enviado."
            )
        votacao = self._votacoes.buscar_por_temporada(temporada.id)
        if votacao is None:
            raise AcaoForaDaFaseError(f"A edição {temporada.nome} ainda não foi à votação.")
        if not votacao.encerrada:
            raise VotacaoEmAndamentoError(
                f"A votação de {temporada.nome} ainda não terminou: o placar só sai quando "
                "todos tiverem confirmado e não restar empate a desfazer."
            )
        endereco = EnderecoDeEmail(destinatario)
        corpo = redigir_placar(
            edicao=temporada.nome,
            eleitores=self._nomes_dos_eleitores(votacao),
            categorias=[
                self._categoria_no_placar(categoria)
                for categoria in self._categorias.listar_por_temporada(temporada.id)
            ],
        )
        self._enviador.enviar(
            MensagemDeEmail(
                destinatario=endereco, assunto=f"Placar do {temporada.nome}", corpo=corpo
            )
        )
        return endereco

    def _nomes_dos_eleitores(self, votacao: VotacaoOscar) -> list[str]:
        return sorted((self._nome(membro_id) for membro_id in votacao.eleitores), key=str.casefold)

    def _categoria_no_placar(self, categoria: CategoriaOscar) -> CategoriaNoPlacar:
        turnos = [
            turno for turno in self._turnos.listar_por_categoria(categoria.id) if not turno.aberto
        ]
        return CategoriaNoPlacar(
            nome=categoria.nome,
            turnos=turnos,
            nomeacoes={
                nomeacao_id: self._nomeacao_no_placar(nomeacao_id)
                for nomeacao_id in _candidatas(turnos)
            },
        )

    def _nomeacao_no_placar(self, nomeacao_id: NomeacaoOscarId) -> NomeacaoNoPlacar:
        nomeacao = self._nomeacoes.buscar_por_id(nomeacao_id)
        if nomeacao is None:
            return NomeacaoNoPlacar(titulo="(nomeação removida)", indicado_por=None)
        filme = self._filmes.buscar_por_id(nomeacao.filme_id)
        indicador = nomeacao.indicado_por_membro_id
        return NomeacaoNoPlacar(
            titulo=filme.titulo if filme is not None else "(filme removido)",
            indicado_por=self._nome(indicador) if indicador is not None else None,
        )

    def _nome(self, membro_id: MembroId) -> str:
        membro = self._membros.buscar_por_id(membro_id)
        return membro.nome if membro is not None else "(ex-membro)"


def _candidatas(turnos: list[TurnoDeVotacao]) -> set[NomeacaoOscarId]:
    return {candidata for turno in turnos for candidata in turno.candidatas}
