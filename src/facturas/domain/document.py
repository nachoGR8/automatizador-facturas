import dataclasses
import datetime
from decimal import Decimal


@dataclasses.dataclass
class InvoiceFields:
    """Datos que se extraen de una factura. None significa 'no encontrado'."""

    supplier: str | None = None
    nif: str | None = None
    invoice_number: str | None = None
    date: datetime.date | None = None
    base: Decimal | None = None
    vat: Decimal | None = None
    total: Decimal | None = None

    @property
    def confidence(self) -> float:
        values = [getattr(self, field.name) for field in dataclasses.fields(self)]
        found = sum(value is not None for value in values)
        return round(found / len(values), 2)


@dataclasses.dataclass
class Document:
    id: str
    fields: InvoiceFields
    errors: list[str] = dataclasses.field(default_factory=list)

    @property
    def confidence(self) -> float:
        return self.fields.confidence
