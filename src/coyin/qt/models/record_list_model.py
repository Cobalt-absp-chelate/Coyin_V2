from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Property, QAbstractListModel, QModelIndex, QObject, Qt, Signal, Slot

from coyin.core.indexing import contract_for, roles_for_contract


class RecordListModel(QAbstractListModel):
    countChanged = Signal()

    def __init__(self, role_names: list[str] | None = None, contract_key: str | None = None, parent: QObject | None = None):
        super().__init__(parent)
        self._contract_key = contract_key or ""
        self._role_names = role_names or roles_for_contract(self._contract_key)
        self._records: list[dict] = []
        self._roles = {Qt.ItemDataRole.UserRole + index + 1: name.encode("utf-8") for index, name in enumerate(self._role_names)}
        self._role_ids = {name: role for role, name in ((role, value.decode("utf-8")) for role, value in self._roles.items())}

    @Property(int, notify=countChanged)
    def count(self) -> int:
        return len(self._records)

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
        old_count = len(self._records)
        new_records = [dict(record) for record in records]
        if new_records == self._records:
            return
        if self._apply_incremental_replace(new_records):
            return
        self.beginResetModel()
        self._records = new_records
        self.endResetModel()
        if len(self._records) != old_count:
            self.countChanged.emit()

    @Slot(int, result="QVariantMap")
    def record(self, row: int) -> dict | None:
        if 0 <= row < len(self._records):
            return self._records[row]
        return None

    def _apply_incremental_replace(self, new_records: list[dict]) -> bool:
        contract = self.contract
        primary_key = contract.primary_key if contract else ""
        if not primary_key or not self._records:
            return False

        old_ids = [record.get(primary_key) for record in self._records]
        new_ids = [record.get(primary_key) for record in new_records]
        if any(identifier is None for identifier in old_ids) or any(identifier is None for identifier in new_ids):
            return False

        if old_ids == new_ids:
            self._update_changed_rows(new_records)
            return True

        if self._apply_single_move(new_records, old_ids, new_ids):
            return True

        if self._apply_contiguous_insertion(new_records, old_ids, new_ids):
            return True

        if self._apply_contiguous_removal(new_records, old_ids, new_ids):
            return True

        shared = min(len(self._records), len(new_records))
        if old_ids[:shared] == new_ids[:shared]:
            self._update_changed_rows(new_records[:shared])
            if len(new_records) > len(self._records):
                self.beginInsertRows(QModelIndex(), len(self._records), len(new_records) - 1)
                self._records.extend(new_records[len(self._records) :])
                self.endInsertRows()
                return True
            if len(new_records) < len(self._records):
                self.beginRemoveRows(QModelIndex(), len(new_records), len(self._records) - 1)
                del self._records[len(new_records) :]
                self.endRemoveRows()
                return True
        return False

    def _apply_single_move(self, new_records: list[dict], old_ids: list, new_ids: list) -> bool:
        if len(old_ids) != len(new_ids) or sorted(old_ids) != sorted(new_ids):
            return False
        count = len(old_ids)
        for source in range(count):
            candidate_ids = list(old_ids)
            moved_id = candidate_ids.pop(source)
            candidate_records = list(self._records)
            moved_record = candidate_records.pop(source)
            for destination in range(count):
                probe_ids = list(candidate_ids)
                probe_ids.insert(destination, moved_id)
                if probe_ids != new_ids:
                    continue
                probe_records = list(candidate_records)
                probe_records.insert(destination, moved_record)
                destination_row = destination if destination < source else destination + 1
                self.beginMoveRows(QModelIndex(), source, source, QModelIndex(), destination_row)
                self._records = probe_records
                self.endMoveRows()
                self._update_changed_rows(new_records)
                return True
        return False

    def _apply_contiguous_insertion(self, new_records: list[dict], old_ids: list, new_ids: list) -> bool:
        delta = len(new_ids) - len(old_ids)
        if delta <= 0:
            return False
        for start in range(len(new_ids) - delta + 1):
            if old_ids == new_ids[:start] + new_ids[start + delta :]:
                self.beginInsertRows(QModelIndex(), start, start + delta - 1)
                self._records[start:start] = [dict(record) for record in new_records[start : start + delta]]
                self.endInsertRows()
                self.countChanged.emit()
                self._update_changed_rows(new_records)
                return True
        return False

    def _apply_contiguous_removal(self, new_records: list[dict], old_ids: list, new_ids: list) -> bool:
        delta = len(old_ids) - len(new_ids)
        if delta <= 0:
            return False
        for start in range(len(old_ids) - delta + 1):
            if new_ids == old_ids[:start] + old_ids[start + delta :]:
                self.beginRemoveRows(QModelIndex(), start, start + delta - 1)
                del self._records[start : start + delta]
                self.endRemoveRows()
                self.countChanged.emit()
                self._update_changed_rows(new_records)
                return True
        return False

    def _update_changed_rows(self, new_records: list[dict]) -> None:
        for row, new_record in enumerate(new_records):
            changed_roles = self._changed_roles(self._records[row], new_record)
            if not changed_roles:
                continue
            self._records[row] = dict(new_record)
            model_index = self.index(row, 0)
            self.dataChanged.emit(model_index, model_index, changed_roles)

    def _changed_roles(self, old_record: dict, new_record: dict) -> list[int]:
        changed = []
        for role_name in self._role_names:
            if old_record.get(role_name) != new_record.get(role_name):
                role_id = self._role_ids.get(role_name)
                if role_id is not None:
                    changed.append(role_id)
        return changed
