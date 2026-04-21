from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QUndoCommand, QUndoStack


class CompositeCommand(QUndoCommand):
    def __init__(self, text: str, commands: list[QUndoCommand]):
        super().__init__(text)
        self.commands = list(commands)

    def redo(self) -> None:
        for command in self.commands:
            command.redo()

    def undo(self) -> None:
        for command in reversed(self.commands):
            command.undo()


class CommandBus(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self._stack = QUndoStack(self)
        self._stack.indexChanged.connect(lambda _index: self.changed.emit())

    def execute(self, command: QUndoCommand) -> None:
        self._stack.push(command)
        self.changed.emit()

    def execute_transaction(self, text: str, commands: list[QUndoCommand]) -> None:
        self.execute(CompositeCommand(text, commands))

    def undo(self) -> None:
        self._stack.undo()

    def redo(self) -> None:
        self._stack.redo()

    def can_undo(self) -> bool:
        return self._stack.canUndo()

    def can_redo(self) -> bool:
        return self._stack.canRedo()

    @property
    def stack(self) -> QUndoStack:
        return self._stack
