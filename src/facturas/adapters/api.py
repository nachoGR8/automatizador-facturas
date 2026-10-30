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
