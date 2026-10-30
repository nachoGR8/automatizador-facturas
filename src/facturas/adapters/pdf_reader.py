import io

import pdfplumber

from facturas.application.errors import UnreadableDocument


class PdfplumberReader:
    def read_text(self, pdf: bytes) -> str:
        try:
            with pdfplumber.open(io.BytesIO(pdf)) as document:
                return "\n".join(page.extract_text() or "" for page in document.pages)
        except Exception as error:  # pdfplumber lanza varios tipos de error con PDFs rotos
            raise UnreadableDocument from error
