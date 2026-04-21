from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from coyin.core.common import dataclass_to_dict, read_json, write_json
from coyin.core.documents.models import AnnotationRecord


class AnnotationStore(QObject):
    changed = Signal(str)

    def __init__(self, storage_file: Path):
        super().__init__()
        self.storage_file = storage_file
        self._records = self._load()

    def _load(self) -> list[AnnotationRecord]:
        payload = read_json(self.storage_file, [])
        return [AnnotationRecord(**item) for item in payload]

    def _persist(self) -> None:
        write_json(self.storage_file, dataclass_to_dict(self._records))

    def add(self, record: AnnotationRecord) -> None:
        self._records.append(record)
        self._persist()
        self.changed.emit(record.document_id)

    def remove(self, annotation_id: str) -> None:
        document_id = ""
        kept: list[AnnotationRecord] = []
        for item in self._records:
            if item.annotation_id == annotation_id:
                document_id = item.document_id
                continue
            kept.append(item)
        self._records = kept
        self._persist()
        if document_id:
            self.changed.emit(document_id)

    def list_for_document(self, document_id: str) -> list[AnnotationRecord]:
        return [item for item in self._records if item.document_id == document_id]

    def count_for_document(self, document_id: str) -> int:
        return len(self.list_for_document(document_id))
