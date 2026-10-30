import dataclasses
import datetime
from decimal import Decimal

from sqlalchemy import JSON, Engine, String, TypeDecorator, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from facturas.domain.document import Document, InvoiceFields


class Money(TypeDecorator):
    """Guarda los importes como texto: SQLite no tiene decimales exactos."""

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return None if value is None else str(value)

    def process_result_value(self, value, dialect):
        return None if value is None else Decimal(value)


class OrmBase(DeclarativeBase):
    pass


class DocumentRow(OrmBase):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(primary_key=True)
    supplier: Mapped[str | None]
    nif: Mapped[str | None]
    invoice_number: Mapped[str | None]
    date: Mapped[datetime.date | None]
    base: Mapped[Decimal | None] = mapped_column(Money)
    vat: Mapped[Decimal | None] = mapped_column(Money)
    total: Mapped[Decimal | None] = mapped_column(Money)
    errors: Mapped[list[str]] = mapped_column(JSON)


def _to_row(document: Document) -> DocumentRow:
    return DocumentRow(id=document.id, errors=document.errors, **dataclasses.asdict(document.fields))


def _to_document(row: DocumentRow) -> Document:
    values = {field.name: getattr(row, field.name) for field in dataclasses.fields(InvoiceFields)}
    return Document(id=row.id, fields=InvoiceFields(**values), errors=row.errors)


class SqlDocumentRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        OrmBase.metadata.create_all(engine)

    def add(self, document: Document) -> None:
        with Session(self._engine) as session:
            session.add(_to_row(document))
            session.commit()

    def get(self, document_id: str) -> Document | None:
        with Session(self._engine) as session:
            row = session.get(DocumentRow, document_id)
            return None if row is None else _to_document(row)

    def list_all(self) -> list[Document]:
        with Session(self._engine) as session:
            return [_to_document(row) for row in session.scalars(select(DocumentRow))]

    def find_by_invoice(self, nif: str, invoice_number: str) -> Document | None:
        query = select(DocumentRow).where(
            DocumentRow.nif == nif, DocumentRow.invoice_number == invoice_number
        )
        with Session(self._engine) as session:
            row = session.scalars(query).first()
            return None if row is None else _to_document(row)
