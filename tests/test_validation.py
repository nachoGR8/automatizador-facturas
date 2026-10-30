from decimal import Decimal

from factories import make_fields
from facturas.domain.document import InvoiceFields
from facturas.domain.validation import validate


def test_complete_and_correct_invoice_has_no_errors():
    assert validate(make_fields()) == []


def test_missing_field_is_reported_by_name():
    assert validate(make_fields(invoice_number=None)) == ["falta invoice_number"]


def test_every_missing_field_is_reported():
    errors = validate(InvoiceFields())
    assert len(errors) == 7
    assert "falta supplier" in errors
    assert "falta total" in errors


def test_invalid_nif_is_reported():
    assert validate(make_fields(nif="B12345679")) == ["NIF no válido"]


def test_total_must_be_base_plus_vat():
    errors = validate(make_fields(total=Decimal("1300.00")))
    assert errors == ["base + IVA no coincide con el total"]


def test_one_cent_of_difference_is_tolerated():
    assert validate(make_fields(total=Decimal("1210.01"))) == []


def test_totals_are_not_checked_when_an_amount_is_missing():
    assert validate(make_fields(vat=None)) == ["falta vat"]
