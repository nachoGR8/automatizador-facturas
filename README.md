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

## Con Docker

```bash
docker compose up --build
```

La API queda en http://127.0.0.1:8000/docs. La base de datos SQLite se guarda en el volumen
`facturas-data`, así que los datos sobreviven a reinicios (`docker compose down -v` los borra).

## Tests

```bash
.venv/Scripts/python -m pytest
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m ruff format --check .
```

El pipeline de GitHub Actions (`.github/workflows/ci.yml`) ejecuta lo mismo en cada push a `main`
y en cada pull request, y además comprueba que la imagen de Docker se construye.

## Métricas (facturas sintéticas)

```bash
.venv/Scripts/python -m benchmark.run --count 100
```

Genera facturas PDF sintéticas con 3 plantillas de maquetación distinta, las procesa con los
adaptadores reales (pdfplumber, extracción, validación y SQLite) y compara cada campo con el valor
con el que se generó la factura. El tiempo no incluye crear los PDF.

| Lote de 100 facturas (semilla 42) | Resultado |
|---|---|
| Tiempo | 0,7 s (unos 7 ms por factura, en el equipo de desarrollo con Windows y Python 3.14) |
| Precisión por campo | 90,6 % |
| Facturas con los 7 campos correctos | 67 % |

| Plantilla | Campos correctos |
|---|---|
| `clasica` ("Factura nº", "Base imponible", "Total") | 7 de 7 |
| `tabla` (dirección, "FACTURA" como título aparte, EUR) | 7 de 7 |
| `titulo` ("FACTURA 2024-0003" en la primera línea, fecha con el mes en letra) | 5 de 7 |

Cómo leer estas cifras:

- Las facturas son sintéticas y las he escrito yo. No miden la precisión sobre facturas reales,
  que será menor: las etiquetas que usan ("Base imponible", "IVA", "Total") son las que el extractor
  ya conoce. Para una cifra fiable hace falta probar con facturas reales anonimizadas.
- Los dos fallos que sí se ven son reales: el proveedor se toma de la primera línea (falla si es
  el título de la factura) y no se entienden fechas con el mes escrito ("26 de marzo de 2024").

## Limitaciones de la v1

- Facturas en PDF con texto (no escaneadas) y etiquetas en español: "Base imponible", "IVA", "Total".
- Se asume que el primer NIF del texto es el del proveedor.
- Una sola tasa de IVA por factura. No se extraen las líneas de factura.
