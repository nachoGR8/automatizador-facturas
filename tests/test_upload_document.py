import pytest

from factories import INVOICE_TEXT
from facturas.application.errors import DuplicateDocument, UnreadableDocument
from facturas.application.upload_document import UploadDocument
from fakes import FakePdfReader, InMemoryDocumentRepository


def make_use_case(text=INVOICE_TEXT, error=None):
    repository = InMemoryDocumentRepository()
    return UploadDocument(FakePdfReader(text, error), repository), repository


def test_valid_invoice_is_saved_and_returned():
    use_case, repository = make_use_case()

    document = use_case.execute(b"pdf")

    assert document.fields.nif == "B12345674"
    assert document.errors == []
    assert document.confidence == 1
    assert repository.get(document.id) == document


def test_invoice_with_validation_errors_is_still_saved():
    use_case, repository = make_use_case(INVOICE_TEXT.replace("1.210,00", "1.300,00"))

    document = use_case.execute(b"pdf")

    assert document.errors == ["base + IVA no coincide con el total"]
    assert repository.get(document.id) == document


def test_duplicate_invoice_is_rejected_with_the_existing_id():
    use_case, repository = make_use_case()
    first = use_case.execute(b"pdf")

    with pytest.raises(DuplicateDocument) as error:
        use_case.execute(b"pdf")

    assert error.value.existing_id == first.id
    assert len(repository.list_all()) == 1


def test_invoices_without_nif_or_number_are_never_duplicates():
    use_case, repository = make_use_case("Suministros Ribera S.L.\nTotal: 10,00 €")

    use_case.execute(b"pdf")
    use_case.execute(b"pdf")

    assert len(repository.list_all()) == 2


def test_unreadable_pdf_error_is_propagated_and_nothing_is_saved():
    use_case, repository = make_use_case(error=UnreadableDocument())

    with pytest.raises(UnreadableDocument):
        use_case.execute(b"no es un pdf")

    assert repository.list_all() == []
