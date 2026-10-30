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
