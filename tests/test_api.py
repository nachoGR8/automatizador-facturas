import pytest
from fastapi.testclient import TestClient

from factories import INVOICE_TEXT
from facturas.adapters.api import create_app
from facturas.adapters.exporters import CsvExporter, XlsxExporter
from facturas.application.errors import UnreadableDocument
from facturas.application.export_documents import ExportDocuments
from facturas.application.get_document import GetDocument
from facturas.application.upload_document import UploadDocument
from fakes import FakePdfReader, InMemoryDocumentRepository


def make_client(reader=None) -> TestClient:
    repository = InMemoryDocumentRepository()
    reader = reader or FakePdfReader(INVOICE_TEXT)
    app = create_app(
        upload_document=UploadDocument(reader, repository),
        get_document=GetDocument(repository),
        export_documents=ExportDocuments(
            repository, {"csv": CsvExporter(), "xlsx": XlsxExporter()}
        ),
    )
    return TestClient(app)


def upload(client: TestClient):
    return client.post("/documents", files={"file": ("factura.pdf", b"pdf", "application/pdf")})


@pytest.fixture
def client():
    return make_client()


def test_upload_returns_201_with_the_extracted_data(client):
    response = upload(client)

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["supplier"] == "Suministros Ribera S.L."
    assert body["nif"] == "B12345674"
    assert body["invoice_number"] == "2024/0042"
    assert body["date"] == "2024-03-15"
    assert body["base"] == "1000.00"
    assert body["vat"] == "210.00"
    assert body["total"] == "1210.00"
    assert body["confidence"] == 1.0
    assert body["errors"] == []


def test_upload_of_a_duplicate_returns_409_with_the_existing_id(client):
    first = upload(client).json()["id"]

    response = upload(client)

    assert response.status_code == 409
    assert response.json() == {"existing_id": first}


def test_upload_of_an_unreadable_pdf_returns_422():
    client = make_client(FakePdfReader(error=UnreadableDocument()))

    response = upload(client)

    assert response.status_code == 422


def test_get_document_returns_the_stored_document(client):
    created = upload(client).json()

    response = client.get(f"/documents/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_unknown_document_returns_404(client):
    assert client.get("/documents/no-existe").status_code == 404


def test_export_csv_downloads_a_file_with_the_documents(client):
    upload(client)

    response = client.get("/export", params={"format": "csv"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == 'attachment; filename="facturas.csv"'
    assert "B12345674" in response.text


def test_export_xlsx_downloads_a_file(client):
    upload(client)

    response = client.get("/export", params={"format": "xlsx"})

    assert response.status_code == 200
    assert response.headers["content-disposition"] == 'attachment; filename="facturas.xlsx"'
    assert response.content[:2] == b"PK"  # un .xlsx es un zip


def test_export_with_an_unknown_format_returns_422(client):
    assert client.get("/export", params={"format": "pdf"}).status_code == 422
