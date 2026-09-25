"""Testes do contrato do módulo de histórico, por meio do leitor de exemplo."""

from __future__ import annotations

from datetime import date

from filmes_e_cubos.application.ports.leitor_de_historico import LeitorDeHistorico
from tests.application.fakes.leitor_de_historico_fake import LeitorDeHistoricoFake


def test_leitor_entrega_os_registros_como_vieram_e_relata_linhas_ruins() -> None:
    leitor: LeitorDeHistorico = LeitorDeHistoricoFake()
    conteudo = b"2023-03-04;Parasita;Iano\nsem data\n2023-03-11;Arrival;\n"

    leitura = leitor.ler(conteudo, nome_do_arquivo="2023.txt")

    assert [(s.data_sessao, s.titulo_do_filme, s.indicado_por) for s in leitura.sessoes] == [
        (date(2023, 3, 4), "Parasita", "Iano"),
        (date(2023, 3, 11), "Arrival", None),
    ]
    assert leitura.sessoes[1].democracia is True
    assert [problema.origem for problema in leitura.problemas] == ["2023.txt, linha 2"]
