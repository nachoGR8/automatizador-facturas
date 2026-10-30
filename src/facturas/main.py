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
