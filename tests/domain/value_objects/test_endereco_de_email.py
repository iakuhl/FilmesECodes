"""Testes do value object EnderecoDeEmail."""

import pytest

from filmes_e_cubos.domain.exceptions.email import EnderecoDeEmailInvalidoError
from filmes_e_cubos.domain.value_objects.endereco_de_email import EnderecoDeEmail


def test_endereco_valido_perde_os_espacos_das_pontas() -> None:
    assert str(EnderecoDeEmail("  cerimonia@clube.com.br ")) == "cerimonia@clube.com.br"


@pytest.mark.parametrize("texto", ["", "cerimonia", "cerimonia@", "@clube.com", "a b@c.d", "a@b"])
def test_o_que_nao_tem_forma_de_endereco_e_recusado(texto: str) -> None:
    with pytest.raises(EnderecoDeEmailInvalidoError):
        EnderecoDeEmail(texto)
