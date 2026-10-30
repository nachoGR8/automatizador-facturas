# Automatizador de facturas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** API FastAPI que recibe una factura en PDF, extrae y valida sus datos y permite consultarlos y exportarlos a CSV/XLSX.

**Architecture:** Hexagonal mínima. `domain` (lógica pura) ← `application` (casos de uso + puertos) ← `adapters` (FastAPI, pdfplumber, SQLAlchemy, CSV/XLSX). `main.py` es el único sitio que conecta adaptadores con casos de uso. Spec: `docs/superpowers/specs/2026-10-30-automatizador-facturas-design.md`.

**Tech Stack:** Python 3.11+ (probado en 3.14), FastAPI, pdfplumber, SQLAlchemy 2 + SQLite, openpyxl, pytest, ruff. reportlab y httpx solo para tests.

---

## Reglas para todo el plan

- Todos los comandos se ejecutan desde la raíz del proyecto: `C:/Users/nacho/Desktop/Proyectos Github/automatizador-facturas` (Git Bash).
- Python del proyecto: `.venv/Scripts/python`. Tests: `.venv/Scripts/python -m pytest`.
- **TDD estricto:** primero el test, verlo fallar por la razón correcta, luego el mínimo código, verlo pasar, commit.
- Cada commit termina con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` (por eso los comandos llevan dos `-m`).
- Regla de dependencias: `domain` no importa nada del proyecto; `application` solo importa `domain`; `adapters` importan `application` y `domain`; `main.py` importa todo.
- Los tests viven planos en `tests/` (sin subcarpetas, sin `__init__.py`), por eso pueden hacer `from factories import ...`.

## Estructura de ficheros

```
pyproject.toml
.gitignore
README.md
samples/factura_ejemplo.pdf
src/facturas/
  __init__.py
  main.py                      Task 13
  domain/
    __init__.py
    document.py                Task 1   InvoiceFields, Document
    nif.py                     Task 2   is_valid_nif
    validation.py              Task 3   validate
    extraction.py              Task 4-5 extract_fields
  application/
    __init__.py
    errors.py                  Task 6
    ports.py                   Task 6
    upload_document.py         Task 7
    get_document.py            Task 8
    export_documents.py        Task 10
  adapters/
    __init__.py
    exporters.py               Task 9
    pdf_reader.py              Task 11
    sql_repository.py          Task 12
    api.py                     Task 13
tests/
  factories.py                 datos de prueba compartidos
  pdf_factory.py               make_pdf (reportlab)
  fakes.py                     FakePdfReader, InMemoryDocumentRepository
  test_document.py  test_nif.py  test_validation.py  test_extraction.py
  test_upload_document.py  test_get_document.py  test_export_documents.py
  test_exporters.py  test_pdf_reader.py  test_sql_repository.py
  test_api.py  test_end_to_end.py
```

---

### Task 0: Esqueleto del proyecto

**Files:**
- Create: `pyproject.toml`, `.gitignore`
- Create: `src/facturas/__init__.py`, `src/facturas/domain/__init__.py`, `src/facturas/application/__init__.py`, `src/facturas/adapters/__init__.py`

- [ ] **Step 1: Crear `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "automatizador-facturas"
version = "0.1.0"
description = "API que extrae y valida datos de facturas en PDF"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115",
    "uvicorn>=0.30",
    "python-multipart>=0.0.9",
    "pdfplumber>=0.11",
    "sqlalchemy>=2.0",
    "openpyxl>=3.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "httpx>=0.27",
    "reportlab>=4",
    "ruff>=0.5",
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ruff]
line-length = 100
src = ["src", "tests"]

[tool.ruff.lint]
select = ["E", "F", "I"]
```

- [ ] **Step 2: Crear `.gitignore`**

```
.venv/
__pycache__/
*.egg-info/
.pytest_cache/
.ruff_cache/
facturas.db
```

- [ ] **Step 3: Crear los paquetes vacíos**

Run:
```bash
mkdir -p src/facturas/domain src/facturas/application src/facturas/adapters tests samples
touch src/facturas/__init__.py src/facturas/domain/__init__.py src/facturas/application/__init__.py src/facturas/adapters/__init__.py
```
Expected: sin salida.

- [ ] **Step 4: Crear el entorno virtual e instalar**

Run:
```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
```
Expected: termina con `Successfully installed ... automatizador-facturas-0.1.0 ...`.

- [ ] **Step 5: Comprobar que el paquete se importa**

Run: `.venv/Scripts/python -c "import facturas; print('ok')"`
Expected: `ok`

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .gitignore src docs
git commit -m "chore: project skeleton, dependencies and implementation plan" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 1: Modelo de dominio (`InvoiceFields` y `Document`)

**Files:**
- Create: `src/facturas/domain/document.py`
- Test: `tests/test_document.py`

- [ ] **Step 1: Escribir el test que falla**

`tests/test_document.py`:
```python
import datetime
from decimal import Decimal

from facturas.domain.document import Document, InvoiceFields


def test_confidence_is_zero_when_nothing_was_found():
    assert InvoiceFields().confidence == 0


def test_confidence_is_one_when_everything_was_found():
    fields = InvoiceFields(
        supplier="Suministros Ribera S.L.",
        nif="B12345674",
        invoice_number="2024/0042",
        date=datetime.date(2024, 3, 15),
        base=Decimal("1000.00"),
        vat=Decimal("210.00"),
        total=Decimal("1210.00"),
    )
    assert fields.confidence == 1


def test_confidence_is_found_fields_divided_by_seven():
    fields = InvoiceFields(supplier="Acme", nif="B12345674", total=Decimal("10.00"))
    assert fields.confidence == 0.43


def test_document_confidence_comes_from_its_fields():
    document = Document(id="1", fields=InvoiceFields(supplier="Acme"))
    assert document.confidence == 0.14
```

- [ ] **Step 2: Ejecutar y ver que falla**

Run: `.venv/Scripts/python -m pytest tests/test_document.py -v`
Expected: error de colección `ModuleNotFoundError: No module named 'facturas.domain.document'`.

- [ ] **Step 3: Implementación mínima**

`src/facturas/domain/document.py`:
```python
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
```

- [ ] **Step 4: Ejecutar y ver que pasa**

Run: `.venv/Scripts/python -m pytest tests/test_document.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/facturas/domain/document.py tests/test_document.py
git commit -m "feat(domain): add InvoiceFields and Document with confidence" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2a: Validación de NIF y NIE

**Files:**
- Create: `src/facturas/domain/nif.py`
- Test: `tests/test_nif.py`

- [ ] **Step 1: Escribir el test que falla**

`tests/test_nif.py`:
```python
import pytest

from facturas.domain.nif import is_valid_nif


@pytest.mark.parametrize("nif", ["12345678Z", "12345678z", "X1234567L"])
def test_valid_dni_and_nie(nif):
    assert is_valid_nif(nif)


@pytest.mark.parametrize("nif", ["12345678A", "X1234567A", "", "hola", "1234"])
def test_invalid_dni_and_nie(nif):
    assert not is_valid_nif(nif)
```

- [ ] **Step 2: Ejecutar y ver que falla**

Run: `.venv/Scripts/python -m pytest tests/test_nif.py -v`
Expected: error de colección `ModuleNotFoundError: No module named 'facturas.domain.nif'`.

- [ ] **Step 3: Implementación mínima (solo DNI y NIE)**

`src/facturas/domain/nif.py`:
```python
import re

_CONTROL_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
_DNI = re.compile(r"^\d{8}[A-Z]$")
_NIE = re.compile(r"^[XYZ]\d{7}[A-Z]$")


def _control_letter(number: int) -> str:
    return _CONTROL_LETTERS[number % 23]


def is_valid_nif(nif: str) -> bool:
    nif = nif.upper().replace(" ", "").replace("-", "")
    if _DNI.match(nif):
        return _control_letter(int(nif[:8])) == nif[8]
    if _NIE.match(nif):
        # X, Y, Z se sustituyen por 0, 1, 2 antes de calcular la letra
        number = int(str("XYZ".index(nif[0])) + nif[1:8])
        return _control_letter(number) == nif[8]
    return False
```

- [ ] **Step 4: Ejecutar y ver que pasa**

Run: `.venv/Scripts/python -m pytest tests/test_nif.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add src/facturas/domain/nif.py tests/test_nif.py
git commit -m "feat(domain): validate DNI and NIE control letter" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2b: Validación de CIF

**Files:**
- Modify: `src/facturas/domain/nif.py`
- Modify: `tests/test_nif.py`

- [ ] **Step 1: Añadir el test que falla**

Añadir al final de `tests/test_nif.py`:
```python


@pytest.mark.parametrize("cif", ["A58818501", "B12345674", "B1234567D", "b-12345674"])
def test_valid_cif(cif):
    assert is_valid_nif(cif)


@pytest.mark.parametrize("cif", ["A58818502", "B1234567A", "B12345679"])
def test_invalid_cif(cif):
    assert not is_valid_nif(cif)
```

- [ ] **Step 2: Ejecutar y ver que falla**

Run: `.venv/Scripts/python -m pytest tests/test_nif.py -v`
Expected: `test_valid_cif` FAIL (los 4 casos), `test_invalid_cif` PASS (porque hoy todo CIF da False).

- [ ] **Step 3: Implementación mínima**

En `src/facturas/domain/nif.py`, añadir la expresión `_CIF` junto a las otras dos:
```python
_CIF = re.compile(r"^[ABCDEFGHJNPQRSUVW]\d{7}[0-9A-J]$")
```

Añadir estas dos funciones después de `_control_letter`:
```python
def _double_digit_sum(digit: int) -> int:
    doubled = digit * 2
    return doubled // 10 + doubled % 10


def _cif_control_is_valid(cif: str) -> bool:
    digits = [int(char) for char in cif[1:8]]
    odd_positions = sum(_double_digit_sum(digit) for digit in digits[0::2])
    even_positions = sum(digits[1::2])
    control_digit = (10 - (odd_positions + even_positions) % 10) % 10
    # El control puede ser el dígito o su letra equivalente (J, A, B, ... I)
    return cif[8] in (str(control_digit), "JABCDEFGHI"[control_digit])
```

Y en `is_valid_nif`, justo antes del `return False` final:
```python
    if _CIF.match(nif):
        return _cif_control_is_valid(nif)
```

- [ ] **Step 4: Ejecutar y ver que pasa**

Run: `.venv/Scripts/python -m pytest tests/test_nif.py -v`
Expected: 15 passed.

- [ ] **Step 5: Commit**

```bash
git add src/facturas/domain/nif.py tests/test_nif.py
git commit -m "feat(domain): validate CIF control digit" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Validaciones de la factura

**Files:**
- Create: `tests/factories.py`
- Create: `src/facturas/domain/validation.py`
- Test: `tests/test_validation.py`

- [ ] **Step 1: Crear los datos de prueba compartidos**

`tests/factories.py`:
```python
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
```

- [ ] **Step 2: Escribir el test que falla**

`tests/test_validation.py`:
```python
from decimal import Decimal

from factories import make_fields
from facturas.domain.document import InvoiceFields
from facturas.domain.validation import validate


def test_complete_and_correct_invoice_has_no_errors():
    assert validate(make_fields()) == []


def test_missing_field_is_reported_by_name():
    assert validate(make_fields(invoice_number=None)) == ["falta invoice_number"]


def test_every_missing_field_is_reported():
    errors = validate(InvoiceFields())
    assert len(errors) == 7
    assert "falta supplier" in errors
    assert "falta total" in errors


def test_invalid_nif_is_reported():
    assert validate(make_fields(nif="B12345679")) == ["NIF no válido"]


def test_total_must_be_base_plus_vat():
    errors = validate(make_fields(total=Decimal("1300.00")))
    assert errors == ["base + IVA no coincide con el total"]


def test_one_cent_of_difference_is_tolerated():
    assert validate(make_fields(total=Decimal("1210.01"))) == []


def test_totals_are_not_checked_when_an_amount_is_missing():
    assert validate(make_fields(vat=None)) == ["falta vat"]
```

- [ ] **Step 3: Ejecutar y ver que falla**

Run: `.venv/Scripts/python -m pytest tests/test_validation.py -v`
Expected: error de colección `ModuleNotFoundError: No module named 'facturas.domain.validation'`.

- [ ] **Step 4: Implementación mínima**

`src/facturas/domain/validation.py`:
```python
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
```

- [ ] **Step 5: Ejecutar y ver que pasa**

Run: `.venv/Scripts/python -m pytest tests/test_validation.py -v`
Expected: 7 passed.

- [ ] **Step 6: Commit**

```bash
git add src/facturas/domain/validation.py tests/factories.py tests/test_validation.py
git commit -m "feat(domain): validate missing fields, NIF and base + VAT = total" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Extracción de proveedor, NIF, nº de factura y fecha

**Files:**
- Modify: `tests/factories.py`
- Create: `src/facturas/domain/extraction.py`
- Test: `tests/test_extraction.py`

- [ ] **Step 1: Añadir el texto de factura de ejemplo a `tests/factories.py`**

Añadir después de los imports (y antes de `make_fields`):
```python
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
```

- [ ] **Step 2: Escribir el test que falla**

`tests/test_extraction.py`:
```python
import datetime

import pytest

from factories import INVOICE_TEXT
from facturas.domain.document import InvoiceFields
from facturas.domain.extraction import extract_fields


def test_empty_text_gives_no_fields():
    assert extract_fields("") == InvoiceFields()


def test_supplier_is_the_first_non_empty_line():
    assert extract_fields("\n  \nSuministros Ribera S.L.\nCIF: B12345674").supplier == (
        "Suministros Ribera S.L."
    )


def test_nif_is_the_first_one_found():
    # El texto tiene el CIF del proveedor y después el NIF del cliente
    assert extract_fields(INVOICE_TEXT).nif == "B12345674"


def test_nif_is_missing_when_the_text_has_none():
    assert extract_fields("Suministros Ribera S.L.").nif is None


@pytest.mark.parametrize(
    "line, expected",
    [
        ("Factura nº: 2024/0042", "2024/0042"),
        ("Nº factura: F-0042", "F-0042"),
        ("FACTURA Nº F-0042", "F-0042"),
        ("Factura 2024-77", "2024-77"),
        ("N.º de factura: 15", "15"),
    ],
)
def test_invoice_number_variants(line, expected):
    assert extract_fields(line).invoice_number == expected


def test_invoice_number_is_not_taken_from_the_title_line():
    assert extract_fields("FACTURA\nFecha: 15/03/2024").invoice_number is None


@pytest.mark.parametrize(
    "line, expected",
    [
        ("Fecha: 15/03/2024", datetime.date(2024, 3, 15)),
        ("Fecha 5-1-2024", datetime.date(2024, 1, 5)),
        ("Fecha: 31/02/2024", None),
        ("sin fecha", None),
    ],
)
def test_date_variants(line, expected):
    assert extract_fields(line).date == expected
```

- [ ] **Step 3: Ejecutar y ver que falla**

Run: `.venv/Scripts/python -m pytest tests/test_extraction.py -v`
Expected: error de colección `ModuleNotFoundError: No module named 'facturas.domain.extraction'`.

- [ ] **Step 4: Implementación mínima**

`src/facturas/domain/extraction.py`:
```python
import datetime
import re

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


def extract_fields(text: str) -> InvoiceFields:
    return InvoiceFields(
        supplier=_find_supplier(text),
        nif=_find_nif(text),
        invoice_number=_find_invoice_number(text),
        date=_find_date(text),
    )
```

- [ ] **Step 5: Ejecutar y ver que pasa**

Run: `.venv/Scripts/python -m pytest tests/test_extraction.py -v`
Expected: 14 passed.

- [ ] **Step 6: Commit**

```bash
git add src/facturas/domain/extraction.py tests/factories.py tests/test_extraction.py
git commit -m "feat(domain): extract supplier, NIF, invoice number and date" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Extracción de importes

**Files:**
- Modify: `src/facturas/domain/extraction.py`
- Modify: `tests/test_extraction.py`

- [ ] **Step 1: Añadir el test que falla**

Añadir `from decimal import Decimal` a los imports de `tests/test_extraction.py` (justo debajo de `import datetime`) y `make_fields` al import de factories (`from factories import INVOICE_TEXT, make_fields`). Después, añadir al final:
```python


@pytest.mark.parametrize(
    "line, expected",
    [
        ("Base imponible: 100,00 €", Decimal("100.00")),
        ("Base imponible: 12.345,67 €", Decimal("12345.67")),
        ("Base imponible:", None),
    ],
)
def test_base_in_spanish_number_format(line, expected):
    assert extract_fields(line).base == expected


def test_vat_percentage_is_not_confused_with_the_amount():
    assert extract_fields("IVA (21%): 210,00 €").vat == Decimal("210.00")


def test_total_is_the_amount_of_the_last_total_line():
    text = "Total IVA: 21,00 €\nTotal factura: 121,00 €"
    assert extract_fields(text).total == Decimal("121.00")


def test_full_invoice_is_extracted_completely():
    fields = extract_fields(INVOICE_TEXT)
    assert fields == make_fields()
    assert fields.confidence == 1
```

- [ ] **Step 2: Ejecutar y ver que falla**

Run: `.venv/Scripts/python -m pytest tests/test_extraction.py -v`
Expected: 5 de los 6 casos nuevos FAIL (`base`, `vat` y `total` son `None`); el caso `Base imponible:` → `None` ya pasa. Los 14 anteriores PASS.

- [ ] **Step 3: Implementación mínima**

En `src/facturas/domain/extraction.py`: añadir `from decimal import Decimal` bajo `import re`, añadir la expresión de importes junto a `_DATE`:
```python
# Importe español: siempre con coma y dos decimales ("1.234,56"). Así "21%" no cuenta.
_AMOUNT = re.compile(r"\d[\d.]*,\d{2}")
```

Añadir esta función antes de `extract_fields`:
```python
def _find_amount(text: str, label: str) -> Decimal | None:
    """Último importe de la última línea que empieza por `label`."""
    found = None
    for line in text.splitlines():
        if re.match(rf"\s*{label}\b", line, re.IGNORECASE):
            amounts = _AMOUNT.findall(line)
            if amounts:
                found = Decimal(amounts[-1].replace(".", "").replace(",", "."))
    return found
```

Y completar `extract_fields` con las tres líneas nuevas:
```python
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
```

- [ ] **Step 4: Ejecutar y ver que pasa**

Run: `.venv/Scripts/python -m pytest tests/test_extraction.py -v`
Expected: 20 passed.

- [ ] **Step 5: Ejecutar toda la suite (no hay regresiones)**

Run: `.venv/Scripts/python -m pytest -q`
Expected: todos los tests pasan.

- [ ] **Step 6: Commit**

```bash
git add src/facturas/domain/extraction.py tests/test_extraction.py
git commit -m "feat(domain): extract base, VAT and total amounts" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Errores y puertos de la capa de aplicación

Estos dos ficheros solo declaran excepciones y contratos (no tienen lógica), así que no llevan test propio: los cubren los tests de los casos de uso (Tasks 7-10).

**Files:**
- Create: `src/facturas/application/errors.py`
- Create: `src/facturas/application/ports.py`

- [ ] **Step 1: Crear `errors.py`**

`src/facturas/application/errors.py`:
```python
class UnreadableDocument(Exception):
    """El fichero no es un PDF que se pueda leer."""


class DuplicateDocument(Exception):
    """Ya existe una factura con el mismo NIF y número."""

    def __init__(self, existing_id: str) -> None:
        super().__init__(f"Factura duplicada: {existing_id}")
        self.existing_id = existing_id


class DocumentNotFound(Exception):
    """No existe ningún documento con ese id."""


class UnsupportedFormat(Exception):
    """Formato de exportación desconocido."""
```

- [ ] **Step 2: Crear `ports.py`**

`src/facturas/application/ports.py`:
```python
from typing import Protocol

from facturas.domain.document import Document


class PdfReader(Protocol):
    def read_text(self, pdf: bytes) -> str: ...


class DocumentRepository(Protocol):
    def add(self, document: Document) -> None: ...

    def get(self, document_id: str) -> Document | None: ...

    def list_all(self) -> list[Document]: ...

    def find_by_invoice(self, nif: str, invoice_number: str) -> Document | None: ...


class Exporter(Protocol):
    media_type: str
    extension: str

    def export(self, documents: list[Document]) -> bytes: ...
```

- [ ] **Step 3: Comprobar que se importan**

Run: `.venv/Scripts/python -c "import facturas.application.errors, facturas.application.ports; print('ok')"`
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add src/facturas/application/errors.py src/facturas/application/ports.py
git commit -m "feat(application): add errors and ports" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Caso de uso `UploadDocument`

**Files:**
- Modify: `tests/factories.py`
- Create: `tests/fakes.py`
- Create: `src/facturas/application/upload_document.py`
- Test: `tests/test_upload_document.py`

- [ ] **Step 1: Añadir `make_document` a `tests/factories.py`**

Cambiar el import de dominio a:
```python
from facturas.domain.document import Document, InvoiceFields
```
y añadir al final del fichero:
```python


def make_document(document_id="doc-1", errors=None, **changes) -> Document:
    return Document(id=document_id, fields=make_fields(**changes), errors=errors or [])
```

- [ ] **Step 2: Crear los dobles de test**

`tests/fakes.py`:
```python
from facturas.domain.document import Document


class FakePdfReader:
    """Devuelve un texto fijo (o lanza un error) sin leer ningún PDF."""

    def __init__(self, text: str = "", error: Exception | None = None) -> None:
        self._text = text
        self._error = error

    def read_text(self, pdf: bytes) -> str:
        if self._error is not None:
            raise self._error
        return self._text


class InMemoryDocumentRepository:
    def __init__(self) -> None:
        self._documents: dict[str, Document] = {}

    def add(self, document: Document) -> None:
        self._documents[document.id] = document

    def get(self, document_id: str) -> Document | None:
        return self._documents.get(document_id)

    def list_all(self) -> list[Document]:
        return list(self._documents.values())

    def find_by_invoice(self, nif: str, invoice_number: str) -> Document | None:
        for document in self._documents.values():
            if document.fields.nif == nif and document.fields.invoice_number == invoice_number:
                return document
        return None
```

- [ ] **Step 3: Escribir el test que falla**

`tests/test_upload_document.py`:
```python
import pytest

from factories import INVOICE_TEXT
from facturas.application.errors import DuplicateDocument, UnreadableDocument
from facturas.application.upload_document import UploadDocument
from fakes import FakePdfReader, InMemoryDocumentRepository


def make_use_case(text=INVOICE_TEXT, error=None):
    repository = InMemoryDocumentRepository()
    return UploadDocument(FakePdfReader(text, error), repository), repository


def test_valid_invoice_is_saved_and_returned():
    use_case, repository = make_use_case()

    document = use_case.execute(b"pdf")

    assert document.fields.nif == "B12345674"
    assert document.errors == []
    assert document.confidence == 1
    assert repository.get(document.id) == document


def test_invoice_with_validation_errors_is_still_saved():
    use_case, repository = make_use_case(INVOICE_TEXT.replace("1.210,00", "1.300,00"))

    document = use_case.execute(b"pdf")

    assert document.errors == ["base + IVA no coincide con el total"]
    assert repository.get(document.id) == document


def test_duplicate_invoice_is_rejected_with_the_existing_id():
    use_case, repository = make_use_case()
    first = use_case.execute(b"pdf")

    with pytest.raises(DuplicateDocument) as error:
        use_case.execute(b"pdf")

    assert error.value.existing_id == first.id
    assert len(repository.list_all()) == 1


def test_invoices_without_nif_or_number_are_never_duplicates():
    use_case, repository = make_use_case("Suministros Ribera S.L.\nTotal: 10,00 €")

    use_case.execute(b"pdf")
    use_case.execute(b"pdf")

    assert len(repository.list_all()) == 2


def test_unreadable_pdf_error_is_propagated_and_nothing_is_saved():
    use_case, repository = make_use_case(error=UnreadableDocument())

    with pytest.raises(UnreadableDocument):
        use_case.execute(b"no es un pdf")

    assert repository.list_all() == []
```

- [ ] **Step 4: Ejecutar y ver que falla**

Run: `.venv/Scripts/python -m pytest tests/test_upload_document.py -v`
Expected: error de colección `ModuleNotFoundError: No module named 'facturas.application.upload_document'`.

- [ ] **Step 5: Implementación mínima**

`src/facturas/application/upload_document.py`:
```python
import uuid

from facturas.application.errors import DuplicateDocument
from facturas.application.ports import DocumentRepository, PdfReader
from facturas.domain.document import Document, InvoiceFields
from facturas.domain.extraction import extract_fields
from facturas.domain.validation import validate


class UploadDocument:
    def __init__(self, reader: PdfReader, repository: DocumentRepository) -> None:
        self._reader = reader
        self._repository = repository

    def execute(self, pdf: bytes) -> Document:
        text = self._reader.read_text(pdf)
        fields = extract_fields(text)
        self._reject_if_duplicate(fields)
        document = Document(id=str(uuid.uuid4()), fields=fields, errors=validate(fields))
        self._repository.add(document)
        return document

    def _reject_if_duplicate(self, fields: InvoiceFields) -> None:
        if fields.nif is None or fields.invoice_number is None:
            return
        existing = self._repository.find_by_invoice(fields.nif, fields.invoice_number)
        if existing is not None:
            raise DuplicateDocument(existing.id)
```

- [ ] **Step 6: Ejecutar y ver que pasa**

Run: `.venv/Scripts/python -m pytest tests/test_upload_document.py -v`
Expected: 5 passed.

- [ ] **Step 7: Commit**

```bash
git add src/facturas/application/upload_document.py tests/factories.py tests/fakes.py tests/test_upload_document.py
git commit -m "feat(application): upload document use case" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Caso de uso `GetDocument`

**Files:**
- Create: `src/facturas/application/get_document.py`
- Test: `tests/test_get_document.py`

- [ ] **Step 1: Escribir el test que falla**

`tests/test_get_document.py`:
```python
import pytest

from factories import make_document
from facturas.application.errors import DocumentNotFound
from facturas.application.get_document import GetDocument
from fakes import InMemoryDocumentRepository


def test_returns_the_stored_document():
    repository = InMemoryDocumentRepository()
    document = make_document("abc")
    repository.add(document)

    assert GetDocument(repository).execute("abc") == document


def test_unknown_id_raises_document_not_found():
    with pytest.raises(DocumentNotFound):
        GetDocument(InMemoryDocumentRepository()).execute("no-existe")
```

- [ ] **Step 2: Ejecutar y ver que falla**

Run: `.venv/Scripts/python -m pytest tests/test_get_document.py -v`
Expected: error de colección `ModuleNotFoundError: No module named 'facturas.application.get_document'`.

- [ ] **Step 3: Implementación mínima**

`src/facturas/application/get_document.py`:
```python
from facturas.application.errors import DocumentNotFound
from facturas.application.ports import DocumentRepository
from facturas.domain.document import Document


class GetDocument:
    def __init__(self, repository: DocumentRepository) -> None:
        self._repository = repository

    def execute(self, document_id: str) -> Document:
        document = self._repository.get(document_id)
        if document is None:
            raise DocumentNotFound(document_id)
        return document
```

- [ ] **Step 4: Ejecutar y ver que pasa**

Run: `.venv/Scripts/python -m pytest tests/test_get_document.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/facturas/application/get_document.py tests/test_get_document.py
git commit -m "feat(application): get document use case" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Exportadores CSV y XLSX

**Files:**
- Create: `src/facturas/adapters/exporters.py`
- Test: `tests/test_exporters.py`

- [ ] **Step 1: Escribir el test que falla**

`tests/test_exporters.py`:
```python
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
```

- [ ] **Step 2: Ejecutar y ver que falla**

Run: `.venv/Scripts/python -m pytest tests/test_exporters.py -v`
Expected: error de colección `ModuleNotFoundError: No module named 'facturas.adapters.exporters'`.

- [ ] **Step 3: Implementación mínima**

`src/facturas/adapters/exporters.py`:
```python
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
```

- [ ] **Step 4: Ejecutar y ver que pasa**

Run: `.venv/Scripts/python -m pytest tests/test_exporters.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add src/facturas/adapters/exporters.py tests/test_exporters.py
git commit -m "feat(adapters): CSV and XLSX exporters" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 10: Caso de uso `ExportDocuments`

**Files:**
- Create: `src/facturas/application/export_documents.py`
- Test: `tests/test_export_documents.py`

- [ ] **Step 1: Escribir el test que falla**

`tests/test_export_documents.py`:
```python
import pytest

from factories import make_document
from facturas.application.errors import UnsupportedFormat
from facturas.application.export_documents import ExportDocuments
from fakes import InMemoryDocumentRepository


class FakeExporter:
    media_type = "text/plain"
    extension = "txt"

    def export(self, documents):
        return ",".join(document.id for document in documents).encode()


def make_use_case():
    repository = InMemoryDocumentRepository()
    repository.add(make_document("a"))
    repository.add(make_document("b"))
    return ExportDocuments(repository, {"txt": FakeExporter()})


def test_exports_every_stored_document_with_the_chosen_exporter():
    exported = make_use_case().execute("txt")

    assert exported.content == b"a,b"
    assert exported.media_type == "text/plain"
    assert exported.filename == "facturas.txt"


def test_unknown_format_raises_unsupported_format():
    with pytest.raises(UnsupportedFormat):
        make_use_case().execute("pdf")
```

- [ ] **Step 2: Ejecutar y ver que falla**

Run: `.venv/Scripts/python -m pytest tests/test_export_documents.py -v`
Expected: error de colección `ModuleNotFoundError: No module named 'facturas.application.export_documents'`.

- [ ] **Step 3: Implementación mínima**

`src/facturas/application/export_documents.py`:
```python
import dataclasses

from facturas.application.errors import UnsupportedFormat
from facturas.application.ports import DocumentRepository, Exporter


@dataclasses.dataclass
class ExportedFile:
    content: bytes
    media_type: str
    filename: str


class ExportDocuments:
    def __init__(self, repository: DocumentRepository, exporters: dict[str, Exporter]) -> None:
        self._repository = repository
        self._exporters = exporters

    def execute(self, file_format: str) -> ExportedFile:
        exporter = self._exporters.get(file_format)
        if exporter is None:
            raise UnsupportedFormat(file_format)
        content = exporter.export(self._repository.list_all())
        return ExportedFile(content, exporter.media_type, f"facturas.{exporter.extension}")
```

- [ ] **Step 4: Ejecutar y ver que pasa**

Run: `.venv/Scripts/python -m pytest tests/test_export_documents.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/facturas/application/export_documents.py tests/test_export_documents.py
git commit -m "feat(application): export documents use case" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 11: Lector de PDF con pdfplumber

**Files:**
- Create: `tests/pdf_factory.py`
- Create: `src/facturas/adapters/pdf_reader.py`
- Test: `tests/test_pdf_reader.py`

- [ ] **Step 1: Crear el generador de PDFs de prueba**

`tests/pdf_factory.py`:
```python
import io

from reportlab.pdfgen import canvas


def make_pdf(lines: list[str]) -> bytes:
    """PDF de una página con una línea de texto por elemento de `lines`."""
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    y = 800
    for line in lines:
        pdf.drawString(50, y, line)
        y -= 20
    pdf.save()
    return buffer.getvalue()
```

- [ ] **Step 2: Escribir el test que falla**

`tests/test_pdf_reader.py`:
```python
import pytest

from factories import INVOICE_LINES, make_fields
from facturas.adapters.pdf_reader import PdfplumberReader
from facturas.application.errors import UnreadableDocument
from facturas.domain.extraction import extract_fields
from pdf_factory import make_pdf


def test_reads_the_text_of_a_pdf():
    text = PdfplumberReader().read_text(make_pdf(INVOICE_LINES))

    assert "Factura nº: 2024/0042" in text
    assert "Total: 1.210,00" in text


def test_text_read_from_a_pdf_can_be_extracted_into_fields():
    text = PdfplumberReader().read_text(make_pdf(INVOICE_LINES))

    assert extract_fields(text) == make_fields()


def test_something_that_is_not_a_pdf_raises_unreadable_document():
    with pytest.raises(UnreadableDocument):
        PdfplumberReader().read_text(b"esto no es un pdf")
```

- [ ] **Step 3: Ejecutar y ver que falla**

Run: `.venv/Scripts/python -m pytest tests/test_pdf_reader.py -v`
Expected: error de colección `ModuleNotFoundError: No module named 'facturas.adapters.pdf_reader'`.

- [ ] **Step 4: Implementación mínima**

`src/facturas/adapters/pdf_reader.py`:
```python
import io

import pdfplumber

from facturas.application.errors import UnreadableDocument


class PdfplumberReader:
    def read_text(self, pdf: bytes) -> str:
        try:
            with pdfplumber.open(io.BytesIO(pdf)) as document:
                return "\n".join(page.extract_text() or "" for page in document.pages)
        except Exception as error:  # pdfplumber lanza varios tipos de error con PDFs rotos
            raise UnreadableDocument from error
```

- [ ] **Step 5: Ejecutar y ver que pasa**

Run: `.venv/Scripts/python -m pytest tests/test_pdf_reader.py -v`
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add src/facturas/adapters/pdf_reader.py tests/pdf_factory.py tests/test_pdf_reader.py
git commit -m "feat(adapters): read PDF text with pdfplumber" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 12: Repositorio SQL (SQLAlchemy + SQLite)

**Files:**
- Create: `src/facturas/adapters/sql_repository.py`
- Test: `tests/test_sql_repository.py`

- [ ] **Step 1: Escribir el test que falla**

`tests/test_sql_repository.py`:
```python
import pytest
from sqlalchemy import create_engine

from factories import make_document
from facturas.adapters.sql_repository import SqlDocumentRepository


@pytest.fixture
def repository():
    return SqlDocumentRepository(create_engine("sqlite://"))


def test_stored_document_is_returned_equal(repository):
    document = make_document("a", errors=["falta vat"])
    repository.add(document)

    assert repository.get("a") == document


def test_missing_fields_are_stored_as_none(repository):
    document = make_document("a", vat=None, date=None)
    repository.add(document)

    assert repository.get("a") == document


def test_unknown_id_returns_none(repository):
    assert repository.get("no-existe") is None


def test_list_all_returns_every_document(repository):
    repository.add(make_document("a", invoice_number="1"))
    repository.add(make_document("b", invoice_number="2"))

    assert {document.id for document in repository.list_all()} == {"a", "b"}


def test_find_by_invoice_matches_nif_and_invoice_number(repository):
    repository.add(make_document("a", invoice_number="1"))
    repository.add(make_document("b", invoice_number="2"))

    assert repository.find_by_invoice("B12345674", "2").id == "b"


def test_find_by_invoice_returns_none_when_nothing_matches(repository):
    repository.add(make_document("a"))

    assert repository.find_by_invoice("B12345674", "otra") is None
    assert repository.find_by_invoice("A58818501", "2024/0042") is None
```

- [ ] **Step 2: Ejecutar y ver que falla**

Run: `.venv/Scripts/python -m pytest tests/test_sql_repository.py -v`
Expected: error de colección `ModuleNotFoundError: No module named 'facturas.adapters.sql_repository'`.

- [ ] **Step 3: Implementación mínima**

`src/facturas/adapters/sql_repository.py`:
```python
import dataclasses
import datetime
from decimal import Decimal

from sqlalchemy import JSON, Engine, String, TypeDecorator, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from facturas.domain.document import Document, InvoiceFields


class Money(TypeDecorator):
    """Guarda los importes como texto: SQLite no tiene decimales exactos."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return None if value is None else str(value)

    def process_result_value(self, value, dialect):
        return None if value is None else Decimal(value)


class OrmBase(DeclarativeBase):
    pass


class DocumentRow(OrmBase):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(primary_key=True)
    supplier: Mapped[str | None]
    nif: Mapped[str | None]
    invoice_number: Mapped[str | None]
    date: Mapped[datetime.date | None]
    base: Mapped[Decimal | None] = mapped_column(Money)
    vat: Mapped[Decimal | None] = mapped_column(Money)
    total: Mapped[Decimal | None] = mapped_column(Money)
    errors: Mapped[list[str]] = mapped_column(JSON)


def _to_row(document: Document) -> DocumentRow:
    return DocumentRow(id=document.id, errors=document.errors, **dataclasses.asdict(document.fields))


def _to_document(row: DocumentRow) -> Document:
    values = {field.name: getattr(row, field.name) for field in dataclasses.fields(InvoiceFields)}
    return Document(id=row.id, fields=InvoiceFields(**values), errors=row.errors)


class SqlDocumentRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        OrmBase.metadata.create_all(engine)

    def add(self, document: Document) -> None:
        with Session(self._engine) as session:
            session.add(_to_row(document))
            session.commit()

    def get(self, document_id: str) -> Document | None:
        with Session(self._engine) as session:
            row = session.get(DocumentRow, document_id)
            return None if row is None else _to_document(row)

    def list_all(self) -> list[Document]:
        with Session(self._engine) as session:
            return [_to_document(row) for row in session.scalars(select(DocumentRow))]

    def find_by_invoice(self, nif: str, invoice_number: str) -> Document | None:
        query = select(DocumentRow).where(
            DocumentRow.nif == nif, DocumentRow.invoice_number == invoice_number
        )
        with Session(self._engine) as session:
            row = session.scalars(query).first()
            return None if row is None else _to_document(row)
```

- [ ] **Step 4: Ejecutar y ver que pasa**

Run: `.venv/Scripts/python -m pytest tests/test_sql_repository.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add src/facturas/adapters/sql_repository.py tests/test_sql_repository.py
git commit -m "feat(adapters): SQLAlchemy document repository" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 13: API FastAPI y conexión final (`main.py`)

**Files:**
- Create: `src/facturas/adapters/api.py`
- Create: `src/facturas/main.py`
- Test: `tests/test_api.py`
- Test: `tests/test_end_to_end.py`

- [ ] **Step 1: Escribir el test de la API que falla**

`tests/test_api.py`:
```python
import pytest
from fastapi.testclient import TestClient

from factories import INVOICE_TEXT
from facturas.adapters.api import create_app
from facturas.adapters.exporters import CsvExporter, XlsxExporter
from facturas.application.errors import UnreadableDocument
from facturas.application.export_documents import ExportDocuments
from facturas.application.get_document import GetDocument
from facturas.application.upload_document import UploadDocument
from fakes import FakePdfReader, InMemoryDocumentRepository


def make_client(reader=None) -> TestClient:
    repository = InMemoryDocumentRepository()
    reader = reader or FakePdfReader(INVOICE_TEXT)
    app = create_app(
        upload_document=UploadDocument(reader, repository),
        get_document=GetDocument(repository),
        export_documents=ExportDocuments(
            repository, {"csv": CsvExporter(), "xlsx": XlsxExporter()}
        ),
    )
    return TestClient(app)


def upload(client: TestClient):
    return client.post("/documents", files={"file": ("factura.pdf", b"pdf", "application/pdf")})


@pytest.fixture
def client():
    return make_client()


def test_upload_returns_201_with_the_extracted_data(client):
    response = upload(client)

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["supplier"] == "Suministros Ribera S.L."
    assert body["nif"] == "B12345674"
    assert body["invoice_number"] == "2024/0042"
    assert body["date"] == "2024-03-15"
    assert body["base"] == "1000.00"
    assert body["vat"] == "210.00"
    assert body["total"] == "1210.00"
    assert body["confidence"] == 1.0
    assert body["errors"] == []


def test_upload_of_a_duplicate_returns_409_with_the_existing_id(client):
    first = upload(client).json()["id"]

    response = upload(client)

    assert response.status_code == 409
    assert response.json() == {"existing_id": first}


def test_upload_of_an_unreadable_pdf_returns_422():
    client = make_client(FakePdfReader(error=UnreadableDocument()))

    response = upload(client)

    assert response.status_code == 422


def test_get_document_returns_the_stored_document(client):
    created = upload(client).json()

    response = client.get(f"/documents/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_unknown_document_returns_404(client):
    assert client.get("/documents/no-existe").status_code == 404


def test_export_csv_downloads_a_file_with_the_documents(client):
    upload(client)

    response = client.get("/export", params={"format": "csv"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == 'attachment; filename="facturas.csv"'
    assert "B12345674" in response.text


def test_export_xlsx_downloads_a_file(client):
    upload(client)

    response = client.get("/export", params={"format": "xlsx"})

    assert response.status_code == 200
    assert response.headers["content-disposition"] == 'attachment; filename="facturas.xlsx"'
    assert response.content[:2] == b"PK"  # un .xlsx es un zip


def test_export_with_an_unknown_format_returns_422(client):
    assert client.get("/export", params={"format": "pdf"}).status_code == 422
```

- [ ] **Step 2: Ejecutar y ver que falla**

Run: `.venv/Scripts/python -m pytest tests/test_api.py -v`
Expected: error de colección `ModuleNotFoundError: No module named 'facturas.adapters.api'`.

- [ ] **Step 3: Implementación mínima de la API**

`src/facturas/adapters/api.py`:
```python
import dataclasses
import datetime
from decimal import Decimal

from fastapi import FastAPI, Request, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from facturas.application.errors import (
    DocumentNotFound,
    DuplicateDocument,
    UnreadableDocument,
    UnsupportedFormat,
)
from facturas.application.export_documents import ExportDocuments
from facturas.application.get_document import GetDocument
from facturas.application.upload_document import UploadDocument
from facturas.domain.document import Document


class DocumentResponse(BaseModel):
    id: str
    supplier: str | None
    nif: str | None
    invoice_number: str | None
    date: datetime.date | None
    base: Decimal | None
    vat: Decimal | None
    total: Decimal | None
    confidence: float
    errors: list[str]

    @classmethod
    def from_document(cls, document: Document) -> "DocumentResponse":
        return cls(
            id=document.id,
            confidence=document.confidence,
            errors=document.errors,
            **dataclasses.asdict(document.fields),
        )


def create_app(
    upload_document: UploadDocument,
    get_document: GetDocument,
    export_documents: ExportDocuments,
) -> FastAPI:
    app = FastAPI(title="Automatizador de facturas")

    @app.exception_handler(UnreadableDocument)
    def on_unreadable(request: Request, error: UnreadableDocument) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": "El PDF no se puede leer"})

    @app.exception_handler(DuplicateDocument)
    def on_duplicate(request: Request, error: DuplicateDocument) -> JSONResponse:
        return JSONResponse(status_code=409, content={"existing_id": error.existing_id})

    @app.exception_handler(DocumentNotFound)
    def on_not_found(request: Request, error: DocumentNotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Documento no encontrado"})

    @app.exception_handler(UnsupportedFormat)
    def on_unsupported_format(request: Request, error: UnsupportedFormat) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": "Formato no soportado"})

    @app.post("/documents", status_code=201, response_model=DocumentResponse)
    def upload(file: UploadFile) -> DocumentResponse:
        document = upload_document.execute(file.file.read())
        return DocumentResponse.from_document(document)

    @app.get("/documents/{document_id}", response_model=DocumentResponse)
    def get(document_id: str) -> DocumentResponse:
        return DocumentResponse.from_document(get_document.execute(document_id))

    @app.get("/export")
    def export(format: str) -> Response:
        exported = export_documents.execute(format)
        return Response(
            content=exported.content,
            media_type=exported.media_type,
            headers={"Content-Disposition": f'attachment; filename="{exported.filename}"'},
        )

    return app
```

- [ ] **Step 4: Ejecutar y ver que pasa**

Run: `.venv/Scripts/python -m pytest tests/test_api.py -v`
Expected: 8 passed. (Puede aparecer un `StarletteDeprecationWarning` sobre `httpx`: es solo un aviso.)

- [ ] **Step 5: Escribir el test de punta a punta que falla**

`tests/test_end_to_end.py`:
```python
from fastapi.testclient import TestClient

from factories import INVOICE_LINES
from facturas.main import build_app
from pdf_factory import make_pdf


def test_upload_get_and_export_with_the_real_adapters(tmp_path, monkeypatch):
    # Fichero en disco y no en memoria: TestClient usa varios hilos.
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    client = TestClient(build_app())
    pdf = make_pdf(INVOICE_LINES)

    created = client.post("/documents", files={"file": ("factura.pdf", pdf, "application/pdf")})
    assert created.status_code == 201
    assert created.json()["errors"] == []
    assert created.json()["confidence"] == 1.0

    fetched = client.get(f"/documents/{created.json()['id']}")
    assert fetched.json() == created.json()

    again = client.post("/documents", files={"file": ("factura.pdf", pdf, "application/pdf")})
    assert again.status_code == 409

    broken = client.post("/documents", files={"file": ("x.pdf", b"no es pdf", "application/pdf")})
    assert broken.status_code == 422

    exported = client.get("/export", params={"format": "xlsx"})
    assert exported.status_code == 200
    assert exported.content[:2] == b"PK"
```

- [ ] **Step 6: Ejecutar y ver que falla**

Run: `.venv/Scripts/python -m pytest tests/test_end_to_end.py -v`
Expected: error de colección `ModuleNotFoundError: No module named 'facturas.main'`.

- [ ] **Step 7: Implementar `main.py`**

`src/facturas/main.py`:
```python
import os

from fastapi import FastAPI
from sqlalchemy import create_engine

from facturas.adapters.api import create_app
from facturas.adapters.exporters import CsvExporter, XlsxExporter
from facturas.adapters.pdf_reader import PdfplumberReader
from facturas.adapters.sql_repository import SqlDocumentRepository
from facturas.application.export_documents import ExportDocuments
from facturas.application.get_document import GetDocument
from facturas.application.upload_document import UploadDocument


def build_app() -> FastAPI:
    """Único sitio donde se eligen los adaptadores concretos."""
    engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///facturas.db"))
    repository = SqlDocumentRepository(engine)
    return create_app(
        upload_document=UploadDocument(PdfplumberReader(), repository),
        get_document=GetDocument(repository),
        export_documents=ExportDocuments(
            repository, {"csv": CsvExporter(), "xlsx": XlsxExporter()}
        ),
    )
```

- [ ] **Step 8: Ejecutar toda la suite**

Run: `.venv/Scripts/python -m pytest -q`
Expected: 78 passed.

- [ ] **Step 9: Commit**

```bash
git add src/facturas/adapters/api.py src/facturas/main.py tests/test_api.py tests/test_end_to_end.py
git commit -m "feat: FastAPI endpoints and wiring of the real adapters" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 14: Factura de ejemplo y README

**Files:**
- Create: `samples/factura_ejemplo.pdf`
- Create: `README.md`

- [ ] **Step 1: Generar la factura de ejemplo con el mismo generador de los tests**

Run:
```bash
.venv/Scripts/python -c "import sys; sys.path.insert(0, 'tests'); from factories import INVOICE_LINES; from pdf_factory import make_pdf; open('samples/factura_ejemplo.pdf', 'wb').write(make_pdf(INVOICE_LINES))"
```
Expected: sin salida; existe `samples/factura_ejemplo.pdf`.

- [ ] **Step 2: Crear `README.md`**

````markdown
# Automatizador de facturas

API con FastAPI que lee facturas en PDF, extrae sus datos con reglas (regex + pdfplumber),
los valida y los exporta a CSV o Excel.

## Qué hace

- `POST /documents`: sube un PDF y devuelve el id, los datos extraídos, la confianza (0 a 1) y los errores de validación.
- `GET /documents/{id}`: consulta una factura ya procesada.
- `GET /export?format=csv|xlsx`: descarga todas las facturas.

Campos extraídos: proveedor, NIF/CIF, nº de factura, fecha, base imponible, IVA y total.
Validaciones: NIF/CIF/NIE correcto, base + IVA = total, campos obligatorios y duplicados
(mismo NIF y nº de factura → `409`).

## Arquitectura (hexagonal)

```
adapters (FastAPI, pdfplumber, SQLAlchemy, CSV/XLSX)
        │  dependen de
application (casos de uso + puertos)
        │  dependen de
domain (reglas puras: extracción, NIF, validación)
```

`src/facturas/main.py` es el único sitio que conecta los adaptadores con los casos de uso.

## Arrancar

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"
.venv/Scripts/python -m uvicorn facturas.main:build_app --factory
```

Abre http://127.0.0.1:8000/docs, sube `samples/factura_ejemplo.pdf` en `POST /documents` y mira el JSON.
Por defecto usa SQLite (`facturas.db`); cambia la base de datos con la variable `DATABASE_URL`.

## Tests

```bash
.venv/Scripts/python -m pytest
.venv/Scripts/python -m ruff check .
```

## Limitaciones de la v1

- Facturas en PDF con texto (no escaneadas) y etiquetas en español: "Base imponible", "IVA", "Total".
- Se asume que el primer NIF del texto es el del proveedor.
- Una sola tasa de IVA por factura. No se extraen las líneas de factura.
````

- [ ] **Step 3: Commit**

```bash
git add README.md samples/factura_ejemplo.pdf
git commit -m "docs: README and sample invoice" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 15: Calidad final y demo real

**Files:**
- Modify: cualquier fichero que `ruff` reformatee

- [ ] **Step 1: Formatear y revisar con ruff**

Run:
```bash
.venv/Scripts/python -m ruff format .
.venv/Scripts/python -m ruff check --fix .
```
Expected: `ruff check` termina con `All checks passed!`. Si queda algún error que `--fix` no arregla, corregirlo a mano.

- [ ] **Step 2: Toda la suite otra vez**

Run: `.venv/Scripts/python -m pytest -q`
Expected: todos los tests pasan, sin errores.

- [ ] **Step 3: Demo real contra el servidor**

Run (en segundo plano): `.venv/Scripts/python -m uvicorn facturas.main:build_app --factory --port 8000`

Después, en otra terminal:
```bash
curl -s -F "file=@samples/factura_ejemplo.pdf;type=application/pdf" http://127.0.0.1:8000/documents
curl -s -o facturas.csv "http://127.0.0.1:8000/export?format=csv" && cat facturas.csv
```
Expected: el primer comando devuelve un JSON con `"nif":"B12345674"`, `"total":"1210.00"`, `"confidence":1.0` y `"errors":[]`; el segundo imprime la cabecera y una fila con esa factura. Repetir el primer comando devuelve `{"existing_id":"..."}` (409). Parar el servidor y borrar `facturas.db` y `facturas.csv`.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: format with ruff" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

## Cobertura del spec

| Spec | Task |
|---|---|
| Campos y confianza (`InvoiceFields.confidence`) | 1, 4, 5 |
| NIF/CIF/NIE | 2a, 2b |
| Validaciones (faltan campos, NIF, base + IVA = total) | 3 |
| Reglas de extracción | 4, 5 |
| Puertos y errores | 6 |
| `UploadDocument` (duplicados, guardar con errores) | 7 |
| `GetDocument` | 8 |
| Exportación CSV/XLSX con columnas únicas | 9 |
| `ExportDocuments` y `UnsupportedFormat` | 10 |
| `PdfReader` con pdfplumber | 11 |
| Persistencia SQLAlchemy + SQLite, `Money` | 12 |
| API (201/409/422/404, export) y `DATABASE_URL` | 13 |
| README, factura de ejemplo, ruff | 14, 15 |
