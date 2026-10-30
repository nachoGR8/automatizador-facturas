import pytest

from facturas.domain.nif import is_valid_nif


@pytest.mark.parametrize("nif", ["12345678Z", "12345678z", "X1234567L"])
def test_valid_dni_and_nie(nif):
    assert is_valid_nif(nif)


@pytest.mark.parametrize("nif", ["12345678A", "X1234567A", "", "hola", "1234"])
def test_invalid_dni_and_nie(nif):
    assert not is_valid_nif(nif)
