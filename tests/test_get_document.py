import pytest

from factories import make_document
from facturas.application.errors import DocumentNotFound
from facturas.application.get_document import GetDocument
from fakes import InMemoryDocumentRepository


def test_returns_the_stored_document():
    repository = InMemoryDocumentRepository()
    document = make_document("abc")
    repository.add(document)

    assert GetDocument(repository).execute("abc") == document


def test_unknown_id_raises_document_not_found():
    with pytest.raises(DocumentNotFound):
        GetDocument(InMemoryDocumentRepository()).execute("no-existe")
