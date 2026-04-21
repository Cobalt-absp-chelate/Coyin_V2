from __future__ import annotations

from PySide6.QtGui import QUndoCommand


class TogglePluginCommand(QUndoCommand):
    def __init__(self, plugin_manager, plugin_id: str, enabled: bool):
        super().__init__("切换插件状态")
        self.plugin_manager = plugin_manager
        self.plugin_id = plugin_id
        self.target_enabled = enabled
        self.previous_enabled = plugin_manager.is_enabled(plugin_id)
        self.last_message = ""

    def _apply(self, enabled: bool) -> None:
        if enabled:
            ok, message = self.plugin_manager.enable(self.plugin_id)
            self.last_message = message
            if not ok:
                raise RuntimeError(message)
        else:
            self.plugin_manager.disable(self.plugin_id)
            self.last_message = ""

    def redo(self) -> None:
        self._apply(self.target_enabled)

    def undo(self) -> None:
        self._apply(self.previous_enabled)
