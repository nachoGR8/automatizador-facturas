import datetime
import re
from decimal import Decimal

from facturas.domain.document import InvoiceFields

# NIE (X1234567L), DNI (12345678Z) o CIF (B12345674). Solo comprueba el formato;
# la letra/dígito de control lo valida `validate`.
_NIF = re.compile(r"\b(?:[XYZ]\d{7}[A-Z]|\d{8}[A-Z]|[ABCDEFGHJNPQRSUVW]\d{7}[0-9A-J])\b")

# "Factura nº: X", "Nº factura: X", "Factura X". El valor debe llevar algún dígito
# para no confundir una línea de título ("FACTURA") con el número.
_INVOICE_NUMBER = re.compile(
    r"factura\s*(?:n\s*[ºo°.]+|n[úu]m(?:ero)?\.?)?\s*[:#]?\s*"
    r"((?=[A-Za-z0-9/-]*\d)[A-Za-z0-9/-]+)",
    re.IGNORECASE,
)

_DATE = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b")

# Importe español: siempre con coma y dos decimales ("1.234,56"). Así "21%" no cuenta.
_AMOUNT = re.compile(r"\d[\d.]*,\d{2}")


def _find_supplier(text: str) -> str | None:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return None


def _find_nif(text: str) -> str | None:
    match = _NIF.search(text)
    return match.group(0) if match else None


def _find_invoice_number(text: str) -> str | None:
    match = _INVOICE_NUMBER.search(text)
    return match.group(1) if match else None


def _find_date(text: str) -> datetime.date | None:
    match = _DATE.search(text)
    if match is None:
        return None
    day, month, year = (int(group) for group in match.groups())
    try:
        return datetime.date(year, month, day)
    except ValueError:  # por ejemplo 31/02/2024
        return None


def _find_amount(text: str, label: str) -> Decimal | None:
    """Último importe de la última línea que empieza por `label`."""
    found = None
    for line in text.splitlines():
        if re.match(rf"\s*{label}\b", line, re.IGNORECASE):
            amounts = _AMOUNT.findall(line)
            if amounts:
                found = Decimal(amounts[-1].replace(".", "").replace(",", "."))
    return found


def extract_fields(text: str) -> InvoiceFields:
    return InvoiceFields(
        supplier=_find_supplier(text),
        nif=_find_nif(text),
        invoice_number=_find_invoice_number(text),
        date=_find_date(text),
        base=_find_amount(text, "base imponible"),
        vat=_find_amount(text, "iva"),
        total=_find_amount(text, "total"),
    )
