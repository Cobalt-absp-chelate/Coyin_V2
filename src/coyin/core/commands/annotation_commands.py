from __future__ import annotations

from PySide6.QtGui import QUndoCommand

from coyin.core.annotations.store import AnnotationStore
from coyin.core.documents.models import AnnotationRecord


class AddAnnotationCommand(QUndoCommand):
    def __init__(self, store: AnnotationStore, record: AnnotationRecord):
        super().__init__("添加标注")
        self.store = store
        self.record = record

    def redo(self) -> None:
        self.store.add(self.record)

    def undo(self) -> None:
        self.store.remove(self.record.annotation_id)
