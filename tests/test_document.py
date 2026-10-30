import datetime
from decimal import Decimal

from facturas.domain.document import Document, InvoiceFields


def test_confidence_is_zero_when_nothing_was_found():
    assert InvoiceFields().confidence == 0


def test_confidence_is_one_when_everything_was_found():
    fields = InvoiceFields(
        supplier="Suministros Ribera S.L.",
        nif="B12345674",
        invoice_number="2024/0042",
        date=datetime.date(2024, 3, 15),
        base=Decimal("1000.00"),
        vat=Decimal("210.00"),
        total=Decimal("1210.00"),
    )
    assert fields.confidence == 1


def test_confidence_is_found_fields_divided_by_seven():
    fields = InvoiceFields(supplier="Acme", nif="B12345674", total=Decimal("10.00"))
    assert fields.confidence == 0.43


def test_document_confidence_comes_from_its_fields():
    document = Document(id="1", fields=InvoiceFields(supplier="Acme"))
    assert document.confidence == 0.14
