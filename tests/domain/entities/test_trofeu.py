"""Testes da entidade Trofeu."""

from datetime import date
from uuid import uuid4

from filmes_e_cubos.domain.entities.trofeu import Trofeu
from filmes_e_cubos.domain.value_objects.identificadores import (
    CategoriaOscarId,
    MembroId,
    NomeacaoOscarId,
)


def test_emitir_trofeu_aponta_para_o_membro_vencedor() -> None:
    membro_vencedor_id = MembroId(uuid4())

    trofeu = Trofeu.emitir(
        categoria_id=CategoriaOscarId(uuid4()),
        nomeacao_vencedora_id=NomeacaoOscarId(uuid4()),
        membro_vencedor_id=membro_vencedor_id,
        data_apuracao=date(2024, 12, 20),
    )

    assert trofeu.membro_vencedor_id == membro_vencedor_id
    assert trofeu.data_apuracao == date(2024, 12, 20)
