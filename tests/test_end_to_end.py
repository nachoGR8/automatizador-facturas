from fastapi.testclient import TestClient

from benchmark.pdf_factory import make_pdf
from factories import INVOICE_LINES
from facturas.main import build_app


def test_upload_get_and_export_with_the_real_adapters(tmp_path, monkeypatch):
    # Fichero en disco y no en memoria: TestClient usa varios hilos.
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    client = TestClient(build_app())
    pdf = make_pdf(INVOICE_LINES)

    created = client.post("/documents", files={"file": ("factura.pdf", pdf, "application/pdf")})
    assert created.status_code == 201
    assert created.json()["errors"] == []
    assert created.json()["confidence"] == 1.0

    fetched = client.get(f"/documents/{created.json()['id']}")
    assert fetched.json() == created.json()

    again = client.post("/documents", files={"file": ("factura.pdf", pdf, "application/pdf")})
    assert again.status_code == 409

    broken = client.post("/documents", files={"file": ("x.pdf", b"no es pdf", "application/pdf")})
    assert broken.status_code == 422

    exported = client.get("/export", params={"format": "xlsx"})
    assert exported.status_code == 200
    assert exported.content[:2] == b"PK"
