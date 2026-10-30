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
