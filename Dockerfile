FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir .

# La base de datos SQLite vive en /data para poder montarla como volumen
ENV DATABASE_URL=sqlite:////data/facturas.db
VOLUME /data

EXPOSE 8000

CMD ["uvicorn", "facturas.main:build_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
