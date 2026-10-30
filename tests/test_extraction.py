import datetime
from decimal import Decimal

import pytest

from factories import INVOICE_TEXT, make_fields
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


@pytest.mark.parametrize(
    "line, expected",
    [
        ("Base imponible: 100,00 €", Decimal("100.00")),
        ("Base imponible: 12.345,67 €", Decimal("12345.67")),
        ("Base imponible:", None),
    ],
)
def test_base_in_spanish_number_format(line, expected):
    assert extract_fields(line).base == expected


def test_vat_percentage_is_not_confused_with_the_amount():
    assert extract_fields("IVA (21%): 210,00 €").vat == Decimal("210.00")


def test_total_is_the_amount_of_the_last_total_line():
    text = "Total IVA: 21,00 €\nTotal factura: 121,00 €"
    assert extract_fields(text).total == Decimal("121.00")


def test_full_invoice_is_extracted_completely():
    fields = extract_fields(INVOICE_TEXT)
    assert fields == make_fields()
    assert fields.confidence == 1


@pytest.mark.parametrize(
    "text",
    [
        "FACTURA\nSuministros Ribera S.L.",
        "FACTURA 2024-0003\nSuministros Ribera S.L.",
        "Factura nº: 2024/0042\nSuministros Ribera S.L.",
        "ALBARÁN 15\nSuministros Ribera S.L.",
    ],
)
def test_supplier_skips_the_document_title(text):
    assert extract_fields(text).supplier == "Suministros Ribera S.L."


def test_a_name_that_only_starts_like_the_title_is_still_a_supplier():
    assert extract_fields("Facturas Express S.L.").supplier == "Facturas Express S.L."


def test_supplier_is_missing_when_there_are_only_titles():
    assert extract_fields("FACTURA").supplier is None


@pytest.mark.parametrize(
    "line",
    [
        "Pinturas Benifaió S.L. · CIF B19487578",
        "Pinturas Benifaió S.L. | NIF B19487578",
        "Pinturas Benifaió S.L. CIF B19487578",
    ],
)
def test_supplier_does_not_include_the_tax_id_on_the_same_line(line):
    assert extract_fields(line).supplier == "Pinturas Benifaió S.L."


@pytest.mark.parametrize(
    "month, number",
    [
        ("enero", 1),
        ("febrero", 2),
        ("marzo", 3),
        ("abril", 4),
        ("mayo", 5),
        ("junio", 6),
        ("julio", 7),
        ("agosto", 8),
        ("septiembre", 9),
        ("octubre", 10),
        ("noviembre", 11),
        ("diciembre", 12),
    ],
)
def test_date_with_the_month_in_letters(month, number):
    assert extract_fields(f"Fecha: 5 de {month} de 2024").date == datetime.date(2024, number, 5)


def test_month_in_letters_ignores_upper_case():
    assert extract_fields("Fecha: 26 de MARZO de 2024").date == datetime.date(2024, 3, 26)


def test_unknown_month_gives_no_date():
    assert extract_fields("Fecha: 5 de foo de 2024").date is None


@pytest.mark.parametrize(
    "text",
    [
        "Fecha: 26 de marzo de 2024\nVencimiento: 15/04/2024",
        "Fecha: 26/03/2024\nVencimiento: 15 de abril de 2024",
    ],
)
def test_the_first_date_wins_whatever_its_format(text):
    assert extract_fields(text).date == datetime.date(2024, 3, 26)
