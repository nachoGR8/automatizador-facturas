import datetime
from decimal import Decimal

from facturas.domain.document import InvoiceFields


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
