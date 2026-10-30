class UnreadableDocument(Exception):
    """El fichero no es un PDF que se pueda leer."""


class DuplicateDocument(Exception):
    """Ya existe una factura con el mismo NIF y número."""

    def __init__(self, existing_id: str) -> None:
        super().__init__(f"Factura duplicada: {existing_id}")
        self.existing_id = existing_id


class DocumentNotFound(Exception):
    """No existe ningún documento con ese id."""


class UnsupportedFormat(Exception):
    """Formato de exportación desconocido."""
