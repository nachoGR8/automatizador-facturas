# Automatizador de facturas — diseño v1

Fecha: 2026-10-30

## Objetivo

API con FastAPI que recibe una factura en PDF, extrae sus datos con reglas (regex + pdfplumber),
los valida y permite consultarlos y exportarlos a CSV/XLSX. Es el paso 1 a 4 del documento
"Proyecto CV: Automatizador de facturas con Python y FastAPI".

Restricciones de trabajo: KISS (código de nivel junior), arquitectura hexagonal, TDD, DRY, SOLID.

## Alcance de la v1

Incluido:

1. `POST /documents`: sube un PDF y devuelve el id y los datos extraídos.
2. Extracción de campos con regex y puntuación de confianza.
3. Validaciones: NIF/CIF/NIE, base + IVA = total, campos obligatorios, duplicados.
4. `GET /documents/{id}` y `GET /export?format=csv|xlsx`.

Fuera de alcance (pasos posteriores): líneas de factura, OCR, LLM local, cola asíncrona, n8n,
panel de revisión, lote de 30-50 facturas con métrica de precisión, Alembic, mypy.

## Campos extraídos

| Campo | Tipo | Cómo se obtiene |
|---|---|---|
| `supplier` | str | Primera línea no vacía del texto |
| `nif` | str | Primer NIF/CIF/NIE con formato válido del texto (se asume que es el del proveedor) |
| `invoice_number` | str | Valor que sigue a "Factura" / "Nº factura" / "Factura nº" |
| `date` | date | Primera fecha `dd/mm/yyyy` o `dd-mm-yyyy` |
| `base` | Decimal | Último importe de la última línea que empieza por "Base imponible" |
| `vat` | Decimal | Último importe de la última línea que empieza por "IVA" |
| `total` | Decimal | Último importe de la última línea que empieza por "Total" |

Importes en formato español (`1.234,56`, siempre con coma y dos decimales, así que el "21%" de
"IVA (21%)" no cuenta como importe) convertidos a `Decimal`.

**Confianza** = campos encontrados / 7, redondeado a 2 decimales (valor entre 0 y 1). Es una
propiedad de `InvoiceFields` (`fields.confidence`).

## Validaciones

`validate(fields) -> list[str]` devuelve mensajes de error; lista vacía significa factura correcta.

- Cada campo no encontrado añade `"falta <campo>"`.
- NIF presente pero con letra/dígito de control incorrecto: `"NIF no válido"`.
- Si hay base, IVA y total: `abs(base + vat - total) <= 0.01`, si no `"base + IVA no coincide con el total"`.
- Duplicado (NIF + nº de factura ya guardados): no es un error de validación, lo decide el caso de uso (ver abajo).

## Arquitectura hexagonal

```
src/facturas/
  domain/           lógica pura, sin FastAPI / SQLAlchemy / pdfplumber
    document.py       InvoiceFields (campos + confidence) y Document (id + fields + errors)
    nif.py            is_valid_nif
    validation.py     validate
    extraction.py     extract_fields(text) -> InvoiceFields
  application/
    ports.py          Protocols de un método: PdfReader, DocumentRepository, Exporter
    upload_document.py
    get_document.py
    export_documents.py
  adapters/
    api.py            rutas FastAPI y schemas Pydantic
    pdf_reader.py     PdfReader con pdfplumber
    sql_repository.py DocumentRepository con SQLAlchemy 2 + SQLite
    exporters.py      CsvExporter y XlsxExporter
  main.py           único sitio que conecta adaptadores con casos de uso
tests/
```

Regla de dependencias: `domain` no importa nada del proyecto; `application` solo importa `domain`;
`adapters` importan `application` y `domain`; `main.py` importa todo.

### Puertos

- `PdfReader.read_text(pdf: bytes) -> str`
- `DocumentRepository`: `add(document)`, `get(id) -> Document | None`, `list_all() -> list[Document]`,
  `find_by_invoice(nif, invoice_number) -> Document | None`
- `Exporter`: atributos `media_type` y `extension`, y `export(documents) -> bytes`

### Casos de uso

`UploadDocument.execute(pdf: bytes) -> Document`:
1. `text = reader.read_text(pdf)`; si falla, el adaptador lanza `UnreadableDocument`.
2. `fields = extract_fields(text)`.
3. `errors = validate(fields)`.
4. Si `nif` e `invoice_number` existen y `repo.find_by_invoice(...)` devuelve algo,
   lanza `DuplicateDocument(existing_id)`.
5. Crea `Document` con id nuevo (uuid4), `repo.add(...)`, lo devuelve.

`GetDocument.execute(id) -> Document`: lanza `DocumentNotFound` si no existe.

`ExportDocuments.execute(file_format) -> ExportedFile`: elige el `Exporter` de un diccionario
`{"csv": CsvExporter(), "xlsx": XlsxExporter()}` y exporta `repo.list_all()`. Si el formato no
está en el diccionario lanza `UnsupportedFormat` (el diccionario es la única fuente de verdad de
los formatos). `ExportedFile` lleva `content`, `media_type` y `filename` (`facturas.<extension>`).

## API

| Ruta | Respuesta |
|---|---|
| `POST /documents` (multipart, campo `file`) | 201 con `{id, supplier, nif, invoice_number, date, base, vat, total, confidence, errors}` |
| | 422 si el PDF no se puede leer (`UnreadableDocument`) |
| | 409 con `{existing_id}` si es duplicada (`DuplicateDocument`) |
| `GET /documents/{id}` | 200 con el mismo JSON, 404 si no existe |
| `GET /export?format=csv\|xlsx` | 200 con el fichero adjunto, 422 si el formato no es válido |

Una factura con errores de validación se guarda igualmente y los errores van en la respuesta,
para que la gestoría la revise.

## Persistencia

SQLAlchemy 2 con una tabla `documents`. Los errores se guardan en una columna JSON y los importes
como texto (tipo `Money`), porque SQLite no tiene decimales exactos y así no se pierde precisión.
`DATABASE_URL` por defecto `sqlite:///facturas.db`; cambiar a PostgreSQL es cambiar esa URL.
Las tablas se crean con `create_all` al arrancar (sin Alembic en la v1).

## Exportación

Las columnas del export se definen una sola vez (`EXPORT_COLUMNS` y una función `to_row(document)`)
y las usan `CsvExporter` y `XlsxExporter` (openpyxl).

## Estrategia de tests (TDD)

Orden de desarrollo, cada paso con rojo → verde → refactor:

1. `nif` → 2. `validation` → 3. `extraction` → 4. casos de uso con repositorio falso en memoria →
5. adaptadores (`pdf_reader` con PDFs sintéticos generados en el test, `sql_repository` con
`sqlite://`, `exporters`) → 6. API con `TestClient` y casos de uso conectados a fakes.

Herramientas: `pytest`, `ruff`. Los PDFs de prueba se generan con `reportlab` (dependencia de desarrollo).
Los tests están en una carpeta plana `tests/`, con `factories.py` (datos de prueba) y `fakes.py`
(repositorio en memoria y lector de PDF falso) compartidos para no repetir código.

## Principios

- **S**: cada módulo tiene una sola razón de cambio.
- **O**: nuevo formato de export = una clase y una entrada en el diccionario.
- **L**: los fakes de test sustituyen a los adaptadores reales sin tocar los casos de uso.
- **I**: puertos de un solo método o muy pocos.
- **D**: los casos de uso dependen de puertos; `main.py` es el único que conoce las implementaciones.
- **DRY**: una función `validate`, una definición de columnas de export, un único `Document`.
- **KISS**: sin DI container, sin Alembic, sin mypy, procesamiento síncrono.

## Limitaciones conocidas

- Se asume que el primer NIF del texto es el del proveedor.
- Una sola tasa de IVA por factura (se usa la última línea que empieza por "IVA").
- Las reglas de extracción están pensadas para facturas con etiquetas en español
  ("Base imponible", "IVA", "Total"); otras plantillas necesitarán nuevas reglas.
