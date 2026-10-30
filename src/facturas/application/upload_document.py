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
