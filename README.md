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
| Tiempo | 0,7-0,8 s (unos 7-8 ms por factura, en el equipo de desarrollo con Windows y Python 3.14) |
| Precisión por campo | 100 % |
| Facturas con los 7 campos correctos | 100 % |

| Plantilla | Campos correctos |
|---|---|
| `clasica` ("Factura nº", "Base imponible", "Total") | 7 de 7 |
| `tabla` (dirección, "FACTURA" como título aparte, EUR) | 7 de 7 |
| `titulo` ("FACTURA 2024-0003" en la primera línea, fecha con el mes en letra) | 7 de 7 |

Cómo leer estas cifras:

- **El 100 % no es la precisión real.** Las facturas son sintéticas y las he escrito yo. La primera
  medición dio un 90,6 % y enseñó dos fallos (el proveedor cuando el título va arriba y las fechas
  con el mes en letra); los arreglé después con ese mismo conjunto. Mide que el extractor lee estas
  3 plantillas, no que generalice. Con facturas reales la cifra será menor.
- Casos que todavía fallan (comprobados a mano): "Subtotal" en vez de "Base imponible", "Importe
  total" en vez de "Total", fechas con puntos (15.03.2024) o con el año de 2 cifras, importes sin
  decimales, números de factura con espacios, un bloque del cliente antes del CIF del proveedor y
  una línea como "ORIGINAL" encima del nombre.
- Para una cifra fiable hace falta probar con facturas reales anonimizadas.

## Limitaciones de la v1

- Facturas en PDF con texto (no escaneadas) y etiquetas en español: "Base imponible", "IVA", "Total".
- Se asume que el primer NIF del texto es el del proveedor.
- Una sola tasa de IVA por factura. No se extraen las líneas de factura.
