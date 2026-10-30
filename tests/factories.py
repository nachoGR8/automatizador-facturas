import datetime
from decimal import Decimal

from facturas.domain.document import Document, InvoiceFields

INVOICE_LINES = [
    "Suministros Ribera S.L.",
    "CIF: B12345674",
    "Factura nº: 2024/0042",
    "Fecha: 15/03/2024",
    "Cliente: Talleres Pérez NIF 12345678Z",
    "Base imponible: 1.000,00 €",
    "IVA (21%): 210,00 €",
    "Total: 1.210,00 €",
]
INVOICE_TEXT = "\n".join(INVOICE_LINES)


def make_fields(**changes) -> InvoiceFields:
    """Factura completa y correcta; cada test cambia solo lo que le interesa."""
    values = {
        "supplier": "Suministros Ribera S.L.",
        "nif": "B12345674",
        "invoice_number": "2024/0042",
        "date": datetime.date(2024, 3, 15),
        "base": Decimal("1000.00"),
        "vat": Decimal("210.00"),
        "total": Decimal("1210.00"),
    }
    values.update(changes)
    return InvoiceFields(**values)


def make_document(document_id="doc-1", errors=None, **changes) -> Document:
    return Document(id=document_id, fields=make_fields(**changes), errors=errors or [])
