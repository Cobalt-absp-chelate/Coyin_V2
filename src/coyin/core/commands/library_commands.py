from __future__ import annotations

from typing import Iterable

from PySide6.QtGui import QUndoCommand

from coyin.core.documents.models import DocumentDescriptor
from coyin.core.workspace.service import WorkspaceService


class ImportDocumentsCommand(QUndoCommand):
    def __init__(self, workspace: WorkspaceService, documents: Iterable[DocumentDescriptor]):
        super().__init__("导入文档")
        self.workspace = workspace
        self.documents = list(documents)

    def redo(self) -> None:
        self.workspace.add_documents(self.documents)

    def undo(self) -> None:
        current_ids = {item.document_id for item in self.documents}
        self.workspace.remove_documents(current_ids)
