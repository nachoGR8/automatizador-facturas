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
