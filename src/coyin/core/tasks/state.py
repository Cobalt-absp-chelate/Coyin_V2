from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from functools import lru_cache
from typing import Any

from PySide6.QtCore import QObject, Signal

from coyin.core.common import now_iso
from coyin.native.bridge import load_task_contracts


class TaskPhase(StrEnum):
    IDLE = "idle"
    LOADING = "loading"
    REFRESHING = "refreshing"
    READY = "ready"
    EMPTY = "empty"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class TaskContract:
    task_id: str
    title: str
    hint: str = ""
    phase_summaries: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class TaskSnapshot:
    task_id: str = ""
    title: str = ""
    phase: str = TaskPhase.IDLE.value
    summary: str = ""
    detail: str = ""
    hint: str = ""
    active_label: str = ""
    item_count: int = 0
    can_retry: bool = False
    started_at: str = ""
    updated_at: str = ""
    last_success_at: str = ""
    last_error_at: str = ""
    meta: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "taskId": self.task_id,
            "title": self.title,
            "phase": self.phase,
            "summary": self.summary,
            "detail": self.detail,
            "hint": self.hint,
            "activeLabel": self.active_label,
            "itemCount": self.item_count,
            "canRetry": self.can_retry,
            "startedAt": self.started_at,
            "updatedAt": self.updated_at,
            "lastSuccessAt": self.last_success_at,
            "lastErrorAt": self.last_error_at,
            "loading": self.phase == TaskPhase.LOADING.value,
            "refreshing": self.phase == TaskPhase.REFRESHING.value,
            "busy": self.phase in {TaskPhase.LOADING.value, TaskPhase.REFRESHING.value},
            "idle": self.phase == TaskPhase.IDLE.value,
            "empty": self.phase == TaskPhase.EMPTY.value,
            "ready": self.phase == TaskPhase.READY.value,
            "error": self.phase == TaskPhase.ERROR.value,
            "meta": dict(self.meta),
        }


FALLBACK_TASK_CONTRACTS: dict[str, dict[str, object]] = {
    "search": {
        "title": "论文检索",
        "hint": "搜索与分析会逐步并入统一任务管线。",
        "phases": {
            "idle": "输入关键词后检索。",
            "loading": "正在检索论文来源…",
            "refreshing": "正在刷新检索结果…",
            "ready": "检索完成。",
            "empty": "未找到匹配结果。",
            "error": "检索失败。",
        },
    },
    "analysis": {
        "title": "结构化分析",
        "hint": "分析报告、导出和后续转写将继续沿用这一任务状态。",
        "phases": {
            "idle": "选择文档后开始分析。",
            "loading": "正在生成结构化分析…",
            "refreshing": "正在刷新分析报告…",
            "ready": "分析完成。",
            "empty": "当前没有可展示的分析结果。",
            "error": "分析失败。",
        },
    },
    "export": {
        "title": "导出任务",
        "hint": "写作导出、LaTeX 导出和其他外部产出将逐步进入统一导出管线。",
        "phases": {
            "idle": "等待导出。",
            "loading": "正在导出…",
            "refreshing": "正在刷新导出结果…",
            "ready": "导出完成。",
            "empty": "当前没有可导出的内容。",
            "error": "导出失败。",
        },
    },
    "latex_compile": {
        "title": "LaTeX 编译",
        "hint": "编译状态、错误摘要和导出路径都将继续复用这一任务状态。",
        "phases": {
            "idle": "模板已载入，准备编译。",
            "loading": "正在编译 LaTeX…",
            "refreshing": "正在重新编译 LaTeX…",
            "ready": "编译完成。",
            "empty": "当前没有编译结果。",
            "error": "编译失败。",
        },
    },
}


def _normalize_contract(task_id: str, payload: dict[str, object]) -> TaskContract:
    phases = payload.get("phases", {}) or {}
    return TaskContract(
        task_id=task_id,
        title=str(payload.get("title", task_id)),
        hint=str(payload.get("hint", "")),
        phase_summaries={str(key): str(value) for key, value in phases.items()},
    )


@lru_cache(maxsize=1)
def _task_contracts() -> dict[str, TaskContract]:
    payload = load_task_contracts() or FALLBACK_TASK_CONTRACTS
    return {task_id: _normalize_contract(task_id, contract) for task_id, contract in payload.items()}


def _contract_for(task_id: str) -> TaskContract:
    base_id = task_id.split("::", 1)[0]
    return _task_contracts().get(base_id, _normalize_contract(base_id, {"title": base_id, "phases": {}}))


class TaskBook:
    def __init__(self):
        self._snapshots: dict[str, TaskSnapshot] = {}

    def snapshot(self, task_id: str) -> TaskSnapshot:
        if task_id not in self._snapshots:
            contract = _contract_for(task_id)
            self._snapshots[task_id] = TaskSnapshot(
                task_id=task_id,
                title=contract.title,
                phase=TaskPhase.IDLE.value,
                summary=contract.phase_summaries.get(TaskPhase.IDLE.value, ""),
                hint=contract.hint,
                active_label=contract.title,
            )
        return self._snapshots[task_id]

    def idle(self, task_id: str, **overrides: Any) -> TaskSnapshot:
        return self._update(task_id, TaskPhase.IDLE.value, **overrides)

    def begin(self, task_id: str, refreshing: bool = False, **overrides: Any) -> TaskSnapshot:
        phase = TaskPhase.REFRESHING.value if refreshing else TaskPhase.LOADING.value
        return self._update(task_id, phase, **overrides)

    def resolve(self, task_id: str, **overrides: Any) -> TaskSnapshot:
        return self._update(task_id, TaskPhase.READY.value, **overrides)

    def empty(self, task_id: str, **overrides: Any) -> TaskSnapshot:
        return self._update(task_id, TaskPhase.EMPTY.value, **overrides)

    def fail(self, task_id: str, **overrides: Any) -> TaskSnapshot:
        overrides.setdefault("can_retry", True)
        return self._update(task_id, TaskPhase.ERROR.value, **overrides)

    def _update(self, task_id: str, phase: str, **overrides: Any) -> TaskSnapshot:
        previous = self.snapshot(task_id)
        contract = _contract_for(task_id)
        timestamp = now_iso()

        started_at = previous.started_at
        last_success_at = previous.last_success_at
        last_error_at = previous.last_error_at
        if phase in {TaskPhase.LOADING.value, TaskPhase.REFRESHING.value}:
            started_at = timestamp
        if phase in {TaskPhase.READY.value, TaskPhase.EMPTY.value}:
            last_success_at = timestamp
        if phase == TaskPhase.ERROR.value:
            last_error_at = timestamp

        snapshot = TaskSnapshot(
            task_id=task_id,
            title=str(overrides.get("title", contract.title)),
            phase=phase,
            summary=str(overrides.get("summary", contract.phase_summaries.get(phase, previous.summary))),
            detail=str(overrides.get("detail", "")),
            hint=str(overrides.get("hint", contract.hint)),
            active_label=str(overrides.get("active_label", contract.title)),
            item_count=int(overrides.get("item_count", previous.item_count if phase != TaskPhase.IDLE.value else 0)),
            can_retry=bool(overrides.get("can_retry", False)),
            started_at=started_at,
            updated_at=timestamp,
            last_success_at=last_success_at,
            last_error_at=last_error_at,
            meta=dict(overrides.get("meta", {})),
        )
        self._snapshots[task_id] = snapshot
        return snapshot


class TaskCenter(QObject):
    taskChanged = Signal(str)
    registryChanged = Signal()

    def __init__(self):
        super().__init__()
        self.book = TaskBook()
        self._registered: set[str] = set()

    def snapshot(self, task_id: str) -> TaskSnapshot:
        self._register(task_id)
        return self.book.snapshot(task_id)

    def begin(self, task_id: str, refreshing: bool = False, **overrides: Any) -> TaskSnapshot:
        self._register(task_id)
        snapshot = self.book.begin(task_id, refreshing=refreshing, **overrides)
        self.taskChanged.emit(task_id)
        return snapshot

    def resolve(self, task_id: str, **overrides: Any) -> TaskSnapshot:
        self._register(task_id)
        snapshot = self.book.resolve(task_id, **overrides)
        self.taskChanged.emit(task_id)
        return snapshot

    def empty(self, task_id: str, **overrides: Any) -> TaskSnapshot:
        self._register(task_id)
        snapshot = self.book.empty(task_id, **overrides)
        self.taskChanged.emit(task_id)
        return snapshot

    def fail(self, task_id: str, **overrides: Any) -> TaskSnapshot:
        self._register(task_id)
        snapshot = self.book.fail(task_id, **overrides)
        self.taskChanged.emit(task_id)
        return snapshot

    def idle(self, task_id: str, **overrides: Any) -> TaskSnapshot:
        self._register(task_id)
        snapshot = self.book.idle(task_id, **overrides)
        self.taskChanged.emit(task_id)
        return snapshot

    def registered_task_ids(self) -> list[str]:
        return sorted(self._registered)

    def _register(self, task_id: str) -> None:
        if task_id not in self._registered:
            self._registered.add(task_id)
            self.registryChanged.emit()
