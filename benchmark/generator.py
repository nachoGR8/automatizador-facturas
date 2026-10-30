"""Genera facturas sintéticas con su resultado esperado ("verdad") para medir la extracción.

Las tres plantillas imitan maquetaciones habituales y son distintas a propósito
(etiquetas, formato de fecha y de número, título arriba...). No están hechas a medida
del extractor: así la precisión medida enseña también sus límites.
"""

import dataclasses
import datetime
import random
import string
from collections.abc import Callable
from decimal import ROUND_HALF_UP, Decimal

from facturas.domain.document import InvoiceFields
from facturas.domain.extraction import SPANISH_MONTHS
from facturas.domain.nif import is_valid_nif

SUPPLIERS = [
    "Suministros Ribera S.L.",
    "Talleres Alzira S.L.",
    "Metalúrgica Carcaixent S.A.",
    "Distribuciones Algemesí S.L.",
    "Ferretería La Ribera S.L.",
    "Transportes Sueca S.L.",
    "Construcciones Alcúdia S.L.",
    "Electricidad Carlet S.L.",
    "Maquinaria Ribera Alta S.A.",
    "Agrícola Montroy S.L.",
    "Pinturas Benifaió S.L.",
    "Cerrajería Algemesí S.L.",
]
CLIENTS = [
    "Talleres Pérez e Hijos S.L.",
    "Juan García López",
    "Bar Restaurante El Puerto S.L.",
    "Carpintería Molina S.L.",
    "María Dolores Sanz Ortiz",
    "Gestoría Levante S.L.",
]
VAT_RATES = [21, 10, 4]


@dataclasses.dataclass
class SyntheticInvoice:
    template: str
    lines: list[str]
    expected: InvoiceFields


def format_amount(value: Decimal) -> str:
    """1210.5 -> '1.210,50' (formato español)."""
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _random_cif(rng: random.Random) -> str:
    letter = rng.choice("ABEH")
    digits = "".join(rng.choice(string.digits) for _ in range(7))
    control = next(c for c in string.digits if is_valid_nif(f"{letter}{digits}{c}"))
    return f"{letter}{digits}{control}"


def _random_dni(rng: random.Random) -> str:
    number = rng.randrange(10_000_000, 99_999_999)
    letter = next(c for c in string.ascii_uppercase if is_valid_nif(f"{number}{c}"))
    return f"{number}{letter}"


def _classic(invoice: InvoiceFields, client: str, client_nif: str, rate: int) -> list[str]:
    return [
        invoice.supplier,
        f"CIF: {invoice.nif}",
        f"Factura nº: {invoice.invoice_number}",
        f"Fecha: {invoice.date:%d/%m/%Y}",
        f"Cliente: {client} NIF {client_nif}",
        f"Base imponible: {format_amount(invoice.base)} €",
        f"IVA ({rate}%): {format_amount(invoice.vat)} €",
        f"Total: {format_amount(invoice.total)} €",
    ]


def _table(invoice: InvoiceFields, client: str, client_nif: str, rate: int) -> list[str]:
    return [
        invoice.supplier,
        "C/ Mayor 12, 46600 Alzira (Valencia)",
        f"NIF {invoice.nif}",
        "FACTURA",
        f"Nº factura: {invoice.invoice_number}",
        f"Fecha de emisión: {invoice.date:%d-%m-%Y}",
        "Datos del cliente",
        f"{client} - NIF: {client_nif}",
        f"Base imponible {format_amount(invoice.base)} EUR",
        f"IVA {rate}% {format_amount(invoice.vat)} EUR",
        f"TOTAL FACTURA {format_amount(invoice.total)} EUR",
    ]


def _title_first(invoice: InvoiceFields, client: str, client_nif: str, rate: int) -> list[str]:
    date = invoice.date
    return [
        f"FACTURA {invoice.invoice_number}",
        f"{invoice.supplier} · CIF {invoice.nif}",
        f"Fecha: {date.day} de {SPANISH_MONTHS[date.month - 1]} de {date.year}",
        f"Cliente: {client} ({client_nif})",
        f"Base imponible: {format_amount(invoice.base)} €",
        f"IVA {rate}%: {format_amount(invoice.vat)} €",
        f"Total a pagar: {format_amount(invoice.total)} €",
    ]


Render = Callable[[InvoiceFields, str, str, int], list[str]]

# nombre -> (formato del número de factura, función que dibuja las líneas)
TEMPLATES: dict[str, tuple[str, Render]] = {
    "clasica": ("{year}/{n:04d}", _classic),
    "tabla": ("F-{n:04d}", _table),
    "titulo": ("{year}-{n:04d}", _title_first),
}


def _generate_one(
    rng: random.Random, index: int, template: str, supplier_nifs: dict[str, str]
) -> SyntheticInvoice:
    number_format, render = TEMPLATES[template]
    date = datetime.date(2024, 1, 1) + datetime.timedelta(days=rng.randrange(366))
    base = Decimal(rng.randrange(2_000, 1_200_000)).scaleb(-2)
    rate = rng.choice(VAT_RATES)
    vat = (base * rate / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    supplier = rng.choice(SUPPLIERS)
    expected = InvoiceFields(
        supplier=supplier,
        nif=supplier_nifs[supplier],
        invoice_number=number_format.format(year=date.year, n=index + 1),
        date=date,
        base=base,
        vat=vat,
        total=base + vat,
    )
    client = rng.choice(CLIENTS)
    client_nif = rng.choice([_random_cif, _random_dni])(rng)
    return SyntheticInvoice(template, render(expected, client, client_nif, rate), expected)


def generate_invoices(count: int, seed: int = 42) -> list[SyntheticInvoice]:
    rng = random.Random(seed)
    supplier_nifs = {supplier: _random_cif(rng) for supplier in SUPPLIERS}
    templates = list(TEMPLATES)
    return [
        _generate_one(rng, index, templates[index % len(templates)], supplier_nifs)
        for index in range(count)
    ]
