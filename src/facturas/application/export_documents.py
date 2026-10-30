import dataclasses

from facturas.application.errors import UnsupportedFormat
from facturas.application.ports import DocumentRepository, Exporter


@dataclasses.dataclass
class ExportedFile:
    content: bytes
    media_type: str
    filename: str


class ExportDocuments:
    def __init__(self, repository: DocumentRepository, exporters: dict[str, Exporter]) -> None:
        self._repository = repository
        self._exporters = exporters

    def execute(self, file_format: str) -> ExportedFile:
        exporter = self._exporters.get(file_format)
        if exporter is None:
            raise UnsupportedFormat(file_format)
        content = exporter.export(self._repository.list_all())
        return ExportedFile(content, exporter.media_type, f"facturas.{exporter.extension}")
