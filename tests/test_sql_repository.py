import pytest
from sqlalchemy import create_engine

from factories import make_document
from facturas.adapters.sql_repository import SqlDocumentRepository


@pytest.fixture
def repository():
    return SqlDocumentRepository(create_engine("sqlite://"))


def test_stored_document_is_returned_equal(repository):
    document = make_document("a", errors=["falta vat"])
    repository.add(document)

    assert repository.get("a") == document


def test_missing_fields_are_stored_as_none(repository):
    document = make_document("a", vat=None, date=None)
    repository.add(document)

    assert repository.get("a") == document


def test_unknown_id_returns_none(repository):
    assert repository.get("no-existe") is None


def test_list_all_returns_every_document(repository):
    repository.add(make_document("a", invoice_number="1"))
    repository.add(make_document("b", invoice_number="2"))

    assert {document.id for document in repository.list_all()} == {"a", "b"}


def test_find_by_invoice_matches_nif_and_invoice_number(repository):
    repository.add(make_document("a", invoice_number="1"))
    repository.add(make_document("b", invoice_number="2"))

    assert repository.find_by_invoice("B12345674", "2").id == "b"


def test_find_by_invoice_returns_none_when_nothing_matches(repository):
    repository.add(make_document("a"))

    assert repository.find_by_invoice("B12345674", "otra") is None
    assert repository.find_by_invoice("A58818501", "2024/0042") is None
