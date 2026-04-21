from __future__ import annotations

from PySide6.QtCore import QSignalBlocker
from PySide6.QtGui import QUndoCommand


class WriterDocumentStateCommand(QUndoCommand):
    def __init__(self, window, text: str, before_html: str, after_html: str):
        super().__init__(text)
        self.window = window
        self.before_html = before_html
        self.after_html = after_html

    def _apply(self, html: str) -> None:
        blocker = QSignalBlocker(self.window.editor.document())
        _ = blocker
        self.window.apply_command_html(html)

    def redo(self) -> None:
        self._apply(self.after_html)

    def undo(self) -> None:
        self._apply(self.before_html)
