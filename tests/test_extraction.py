import datetime

import pytest

from factories import INVOICE_TEXT
from facturas.domain.document import InvoiceFields
from facturas.domain.extraction import extract_fields


def test_empty_text_gives_no_fields():
    assert extract_fields("") == InvoiceFields()


def test_supplier_is_the_first_non_empty_line():
    assert extract_fields("\n  \nSuministros Ribera S.L.\nCIF: B12345674").supplier == (
        "Suministros Ribera S.L."
    )


def test_nif_is_the_first_one_found():
    # El texto tiene el CIF del proveedor y después el NIF del cliente
    assert extract_fields(INVOICE_TEXT).nif == "B12345674"


def test_nif_is_missing_when_the_text_has_none():
    assert extract_fields("Suministros Ribera S.L.").nif is None


@pytest.mark.parametrize(
    "line, expected",
    [
        ("Factura nº: 2024/0042", "2024/0042"),
        ("Nº factura: F-0042", "F-0042"),
        ("FACTURA Nº F-0042", "F-0042"),
        ("Factura 2024-77", "2024-77"),
        ("N.º de factura: 15", "15"),
    ],
)
def test_invoice_number_variants(line, expected):
    assert extract_fields(line).invoice_number == expected


def test_invoice_number_is_not_taken_from_the_title_line():
    assert extract_fields("FACTURA\nFecha: 15/03/2024").invoice_number is None


@pytest.mark.parametrize(
    "line, expected",
    [
        ("Fecha: 15/03/2024", datetime.date(2024, 3, 15)),
        ("Fecha 5-1-2024", datetime.date(2024, 1, 5)),
        ("Fecha: 31/02/2024", None),
        ("sin fecha", None),
    ],
)
def test_date_variants(line, expected):
    assert extract_fields(line).date == expected
