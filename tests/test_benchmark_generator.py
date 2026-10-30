from decimal import Decimal

import pytest

from benchmark.generator import TEMPLATES, format_amount, generate_invoices
from facturas.domain.extraction import extract_fields
from facturas.domain.validation import validate


@pytest.mark.parametrize(
    "value, expected",
    [
        (Decimal("1210.00"), "1.210,00"),
        (Decimal("5.5"), "5,50"),
        (Decimal("0.99"), "0,99"),
        (Decimal("1234567.89"), "1.234.567,89"),
    ],
)
def test_format_amount_uses_the_spanish_format(value, expected):
    assert format_amount(value) == expected


def test_generates_the_requested_number_of_invoices():
    assert len(generate_invoices(7)) == 7


def test_the_same_seed_gives_the_same_invoices():
    assert generate_invoices(10, seed=1) == generate_invoices(10, seed=1)


def test_a_different_seed_gives_different_invoices():
    assert generate_invoices(10, seed=1) != generate_invoices(10, seed=2)


def test_expected_fields_are_complete_and_pass_validation():
    for invoice in generate_invoices(30):
        assert invoice.expected.confidence == 1
        assert validate(invoice.expected) == []


def test_nif_and_invoice_number_pairs_are_unique():
    invoices = generate_invoices(50)

    pairs = {(invoice.expected.nif, invoice.expected.invoice_number) for invoice in invoices}

    assert len(pairs) == 50


def test_every_template_is_used():
    assert {invoice.template for invoice in generate_invoices(30)} == set(TEMPLATES)


def test_the_text_contains_the_expected_values():
    for invoice in generate_invoices(30):
        text = "\n".join(invoice.lines)
        assert invoice.expected.supplier in text
        assert invoice.expected.nif in text
        assert invoice.expected.invoice_number in text
        assert format_amount(invoice.expected.total) in text


def test_the_classic_template_can_be_extracted_perfectly():
    classic = [invoice for invoice in generate_invoices(30) if invoice.template == "clasica"]

    for invoice in classic:
        assert extract_fields("\n".join(invoice.lines)) == invoice.expected
