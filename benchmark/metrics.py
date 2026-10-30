import dataclasses

from facturas.domain.document import InvoiceFields

FIELD_NAMES = [field.name for field in dataclasses.fields(InvoiceFields)]


@dataclasses.dataclass
class Report:
    invoices: int
    field_accuracy: dict[str, float]  # de 0 a 1, por campo
    fully_correct: int  # facturas con todos los campos bien

    @property
    def overall_accuracy(self) -> float:
        return sum(self.field_accuracy.values()) / len(self.field_accuracy)


def build_report(expected: list[InvoiceFields], actual: list[InvoiceFields]) -> Report:
    pairs = list(zip(expected, actual, strict=True))
    field_accuracy = {
        name: sum(getattr(want, name) == getattr(got, name) for want, got in pairs) / len(pairs)
        for name in FIELD_NAMES
    }
    fully_correct = sum(want == got for want, got in pairs)
    return Report(len(pairs), field_accuracy, fully_correct)
