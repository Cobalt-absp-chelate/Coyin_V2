from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import QAbstractListModel, QModelIndex, QObject, Qt

from coyin.core.indexing import contract_for, roles_for_contract


class RecordListModel(QAbstractListModel):
    def __init__(self, role_names: list[str] | None = None, contract_key: str | None = None, parent: QObject | None = None):
        super().__init__(parent)
        self._contract_key = contract_key or ""
        self._role_names = role_names or roles_for_contract(self._contract_key)
        self._records: list[dict] = []
        self._roles = {Qt.ItemDataRole.UserRole + index + 1: name.encode("utf-8") for index, name in enumerate(self._role_names)}

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._records)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._records)):
            return None
        record = self._records[index.row()]
        if role == Qt.ItemDataRole.DisplayRole and self._role_names:
            return record.get(self._role_names[0])
        key = self._roles.get(role)
        if key:
            return record.get(key.decode("utf-8"))
        return None

    def roleNames(self):
        return self._roles

    @property
    def contract(self):
        return contract_for(self._contract_key) if self._contract_key else None

    def replace(self, records: Iterable[dict]) -> None:
        new_records = [dict(record) for record in records]
        self.beginResetModel()
        self._records = new_records
        self.endResetModel()

    def record(self, row: int) -> dict | None:
        if 0 <= row < len(self._records):
            return self._records[row]
        return None
