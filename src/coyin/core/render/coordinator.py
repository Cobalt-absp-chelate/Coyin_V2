from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal


@dataclass(slots=True)
class ViewportState:
    zoom: float = 1.0
    fit_mode: str = "width"
    page_mode: str = "continuous"
    current_page: int = 0
    scroll_ratio: float = 0.0
    split_mode: str = "single"


class RenderCoordinator(QObject):
    changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._states: dict[str, ViewportState] = {}

    def state_for(self, session_key: str) -> ViewportState:
        return self._states.setdefault(session_key, ViewportState())

    def update(self, session_key: str, **patch) -> ViewportState:
        state = self.state_for(session_key)
        for key, value in patch.items():
            setattr(state, key, value)
        self.changed.emit(session_key)
        return state

    def clone(self, source_key: str, target_key: str) -> ViewportState:
        source = self.state_for(source_key)
        cloned = ViewportState(
            zoom=source.zoom,
            fit_mode=source.fit_mode,
            page_mode=source.page_mode,
            current_page=source.current_page,
            scroll_ratio=source.scroll_ratio,
            split_mode=source.split_mode,
        )
        self._states[target_key] = cloned
        self.changed.emit(target_key)
        return cloned
