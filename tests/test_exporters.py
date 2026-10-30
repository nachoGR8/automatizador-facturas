import csv
import datetime
import io

from openpyxl import load_workbook

from factories import make_document
from facturas.adapters.exporters import EXPORT_COLUMNS, CsvExporter, XlsxExporter


def read_csv(content: bytes) -> list[list[str]]:
    return list(csv.reader(io.StringIO(content.decode("utf-8"))))


def read_xlsx(content: bytes) -> list[list]:
    sheet = load_workbook(io.BytesIO(content)).active
    return [[cell.value for cell in row] for row in sheet.iter_rows()]


def test_csv_has_a_header_and_one_row_per_document():
    content = CsvExporter().export([make_document("a"), make_document("b")])

    rows = read_csv(content)

    assert rows[0] == EXPORT_COLUMNS
    assert rows[1] == [
        "a",
        "Suministros Ribera S.L.",
        "B12345674",
        "2024/0042",
        "2024-03-15",
        "1000.00",
        "210.00",
        "1210.00",
        "1.0",
        "",
    ]
    assert rows[2][0] == "b"


def test_csv_joins_errors_and_leaves_missing_values_empty():
    document = make_document(errors=["falta vat", "NIF no válido"], vat=None)

    row = read_csv(CsvExporter().export([document]))[1]

    assert row[EXPORT_COLUMNS.index("vat")] == ""
    assert row[EXPORT_COLUMNS.index("errors")] == "falta vat; NIF no válido"


def test_csv_media_type_and_extension():
    assert CsvExporter().media_type == "text/csv"
    assert CsvExporter().extension == "csv"


def test_xlsx_has_the_same_header_and_rows():
    content = XlsxExporter().export([make_document("a")])

    rows = read_xlsx(content)

    assert rows[0] == EXPORT_COLUMNS
    assert rows[1][EXPORT_COLUMNS.index("id")] == "a"
    assert rows[1][EXPORT_COLUMNS.index("nif")] == "B12345674"
    assert float(rows[1][EXPORT_COLUMNS.index("total")]) == 1210.0
    assert rows[1][EXPORT_COLUMNS.index("date")].date() == datetime.date(2024, 3, 15)


def test_xlsx_media_type_and_extension():
    assert XlsxExporter().extension == "xlsx"
    assert XlsxExporter().media_type.endswith("spreadsheetml.sheet")
