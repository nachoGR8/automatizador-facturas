import pytest

from factories import make_document
from facturas.application.errors import UnsupportedFormat
from facturas.application.export_documents import ExportDocuments
from fakes import InMemoryDocumentRepository


class FakeExporter:
    media_type = "text/plain"
    extension = "txt"

    def export(self, documents):
        return ",".join(document.id for document in documents).encode()


def make_use_case():
    repository = InMemoryDocumentRepository()
    repository.add(make_document("a"))
    repository.add(make_document("b"))
    return ExportDocuments(repository, {"txt": FakeExporter()})


def test_exports_every_stored_document_with_the_chosen_exporter():
    exported = make_use_case().execute("txt")

    assert exported.content == b"a,b"
    assert exported.media_type == "text/plain"
    assert exported.filename == "facturas.txt"


def test_unknown_format_raises_unsupported_format():
    with pytest.raises(UnsupportedFormat):
        make_use_case().execute("pdf")
