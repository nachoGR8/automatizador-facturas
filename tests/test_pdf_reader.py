import pytest

from benchmark.pdf_factory import make_pdf
from factories import INVOICE_LINES, make_fields
from facturas.adapters.pdf_reader import PdfplumberReader
from facturas.application.errors import UnreadableDocument
from facturas.domain.extraction import extract_fields


def test_reads_the_text_of_a_pdf():
    text = PdfplumberReader().read_text(make_pdf(INVOICE_LINES))

    assert "Factura nº: 2024/0042" in text
    assert "Total: 1.210,00" in text


def test_text_read_from_a_pdf_can_be_extracted_into_fields():
    text = PdfplumberReader().read_text(make_pdf(INVOICE_LINES))

    assert extract_fields(text) == make_fields()


def test_something_that_is_not_a_pdf_raises_unreadable_document():
    with pytest.raises(UnreadableDocument):
        PdfplumberReader().read_text(b"esto no es un pdf")
