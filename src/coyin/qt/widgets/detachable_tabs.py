from __future__ import annotations

import json

from PySide6.QtCore import QMimeData, QPoint, Qt, Signal
from PySide6.QtGui import QDrag, QMouseEvent, QPixmap
from PySide6.QtWidgets import QTabBar, QTabWidget


class DetachableTabBar(QTabBar):
    detach_requested = Signal(int, QPoint)
    import_requested = Signal(str)

    def __init__(self, owner):
        super().__init__(owner)
        self._drag_start = QPoint()
        self.setAcceptDrops(True)
        self.setMovable(True)
        self.setElideMode(Qt.TextElideMode.ElideRight)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            super().mouseMoveEvent(event)
            return
        if (event.pos() - self._drag_start).manhattanLength() < 16:
            super().mouseMoveEvent(event)
            return
        index = self.tabAt(self._drag_start)
        if index < 0:
            super().mouseMoveEvent(event)
            return
        mime = QMimeData()
        payload = {"title": self.tabText(index)}
        if widget := self.parentWidget().widget(index):
            payload["document_id"] = getattr(widget, "document_id", "")
        mime.setData("application/x-coyin-doc-tab", json.dumps(payload).encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime)
        pixmap = self.grab(self.tabRect(index))
        drag.setPixmap(pixmap if not pixmap.isNull() else QPixmap())
        if drag.exec(Qt.DropAction.MoveAction) == Qt.DropAction.IgnoreAction:
            self.detach_requested.emit(index, event.globalPosition().toPoint())

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasFormat("application/x-coyin-doc-tab"):
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        payload = json.loads(bytes(event.mimeData().data("application/x-coyin-doc-tab")).decode("utf-8"))
        document_id = payload.get("document_id", "")
        if document_id:
            self.import_requested.emit(document_id)
            event.acceptProposedAction()


class DetachableTabWidget(QTabWidget):
    detach_requested = Signal(int, QPoint)
    import_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        bar = DetachableTabBar(self)
        bar.detach_requested.connect(self.detach_requested.emit)
        bar.import_requested.connect(self.import_requested.emit)
        self.setTabBar(bar)
        self.setDocumentMode(True)
        self.setTabsClosable(True)
