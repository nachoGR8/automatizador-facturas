"""Mide tiempo y precisión del extractor sobre facturas sintéticas.

Uso: python -m benchmark.run --count 50
"""

import argparse
import dataclasses
import time

from sqlalchemy import create_engine

from benchmark.generator import generate_invoices
from benchmark.metrics import Report, build_report
from benchmark.pdf_factory import make_pdf
from facturas.adapters.pdf_reader import PdfplumberReader
from facturas.adapters.sql_repository import SqlDocumentRepository
from facturas.application.upload_document import UploadDocument


@dataclasses.dataclass
class Result:
    report: Report
    seconds: float


def run(count: int, seed: int = 42) -> Result:
    invoices = generate_invoices(count, seed)
    pdfs = [make_pdf(invoice.lines) for invoice in invoices]  # fuera del cronómetro

    repository = SqlDocumentRepository(create_engine("sqlite://"))
    upload_document = UploadDocument(PdfplumberReader(), repository)

    start = time.perf_counter()
    documents = [upload_document.execute(pdf) for pdf in pdfs]
    seconds = time.perf_counter() - start

    report = build_report(
        [invoice.expected for invoice in invoices], [document.fields for document in documents]
    )
    return Result(report, seconds)


def format_report(result: Result) -> str:
    report = result.report
    milliseconds = result.seconds / report.invoices * 1000
    lines = [
        f"Facturas procesadas: {report.invoices}",
        f"Tiempo del lote: {result.seconds:.2f} s ({milliseconds:.0f} ms por factura)",
        "Precisión por campo:",
    ]
    lines += [f"  {name:<16}{accuracy:>7.1%}" for name, accuracy in report.field_accuracy.items()]
    lines += [
        f"Precisión global: {report.overall_accuracy:.1%}",
        f"Facturas con los 7 campos correctos: {report.fully_correct}/{report.invoices} "
        f"({report.fully_correct / report.invoices:.1%})",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mide tiempo y precisión con facturas sintéticas")
    parser.add_argument("--count", type=int, default=50, help="número de facturas")
    parser.add_argument("--seed", type=int, default=42, help="semilla del generador")
    args = parser.parse_args()
    print(format_report(run(args.count, args.seed)))


if __name__ == "__main__":
    main()
