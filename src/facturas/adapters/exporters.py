import csv
import dataclasses
import io

from openpyxl import Workbook

from facturas.domain.document import Document

# Única definición de las columnas: la usan el CSV y el XLSX.
EXPORT_COLUMNS = [
    "id",
    "supplier",
    "nif",
    "invoice_number",
    "date",
    "base",
    "vat",
    "total",
    "confidence",
    "errors",
]


def to_row(document: Document) -> list:
    values = {
        "id": document.id,
        **dataclasses.asdict(document.fields),
        "confidence": document.confidence,
        "errors": "; ".join(document.errors),
    }
    return ["" if values[column] is None else values[column] for column in EXPORT_COLUMNS]


class CsvExporter:
    media_type = "text/csv"
    extension = "csv"

    def export(self, documents: list[Document]) -> bytes:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(EXPORT_COLUMNS)
        writer.writerows(to_row(document) for document in documents)
        return buffer.getvalue().encode("utf-8")


class XlsxExporter:
    media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    extension = "xlsx"

    def export(self, documents: list[Document]) -> bytes:
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(EXPORT_COLUMNS)
        for document in documents:
            sheet.append(to_row(document))
        buffer = io.BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()
