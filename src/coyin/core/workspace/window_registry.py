from __future__ import annotations

from collections import defaultdict

from PySide6.QtCore import QObject, Signal


class WindowRegistry(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self._windows: dict[str, object] = {}
        self._types: dict[str, str] = {}
        self._documents_by_window: dict[str, set[str]] = defaultdict(set)
        self._window_counter = 0

    def register(self, window_type: str, window: object) -> str:
        self._window_counter += 1
        window_id = f"{window_type}_{self._window_counter}"
        self._windows[window_id] = window
        self._types[window_id] = window_type
        self.changed.emit()
        return window_id

    def unregister(self, window_id: str) -> None:
        self._windows.pop(window_id, None)
        self._types.pop(window_id, None)
        self._documents_by_window.pop(window_id, None)
        self.changed.emit()

    def attach_document(self, window_id: str, document_id: str) -> None:
        self._documents_by_window[window_id].add(document_id)
        self.changed.emit()

    def detach_document(self, window_id: str, document_id: str) -> None:
        if window_id in self._documents_by_window:
            self._documents_by_window[window_id].discard(document_id)
            self.changed.emit()

    def windows_for_document(self, document_id: str) -> list[object]:
        return [
            self._windows[window_id]
            for window_id, document_ids in self._documents_by_window.items()
            if document_id in document_ids and window_id in self._windows
        ]

    def list_windows(self, window_type: str | None = None) -> list[object]:
        if not window_type:
            return list(self._windows.values())
        return [self._windows[key] for key, value in self._types.items() if value == window_type]
