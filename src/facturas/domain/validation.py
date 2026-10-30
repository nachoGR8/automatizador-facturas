import dataclasses
from decimal import Decimal

from facturas.domain.document import InvoiceFields
from facturas.domain.nif import is_valid_nif

TOLERANCE = Decimal("0.01")


def validate(fields: InvoiceFields) -> list[str]:
    """Devuelve los errores de la factura; lista vacía si está correcta."""
    values = dataclasses.asdict(fields)
    errors = [f"falta {name}" for name, value in values.items() if value is None]

    if fields.nif is not None and not is_valid_nif(fields.nif):
        errors.append("NIF no válido")

    amounts = (fields.base, fields.vat, fields.total)
    if all(amount is not None for amount in amounts):
        if abs(fields.base + fields.vat - fields.total) > TOLERANCE:
            errors.append("base + IVA no coincide con el total")

    return errors
