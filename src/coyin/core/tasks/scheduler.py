from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import threading
import time
from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal


class TaskCancelledError(RuntimeError):
    pass


class TaskToken:
    def __init__(self):
        self._cancelled = threading.Event()

    @property
    def cancelled(self) -> bool:
        return self._cancelled.is_set()

    def cancel(self) -> None:
        self._cancelled.set()

    def throw_if_cancelled(self) -> None:
        if self.cancelled:
            raise TaskCancelledError("任务已取消")


@dataclass(slots=True)
class TaskRequest:
    task_id: str
    lane: str = "general"
    priority: str = "background"
    policy: str = "enqueue"
    max_concurrency: int = 2
    timeout_ms: int = 0
    cancellable: bool = True
    exclusive: bool = False
    consumer_id: str = ""


@dataclass(slots=True)
class ScheduledTaskState:
    task_id: str
    consumer_id: str
    lane: str
    status: str
    priority: str
    queued: bool = False
    running: bool = False
    revision: int = 0
    message: str = ""
    last_duration_ms: float = 0.0
    run_count: int = 0


class _SchedulerSignals(QObject):
    finished = Signal(str, int, object)
    failed = Signal(str, int, str)


class _ScheduledRunnable(QRunnable):
    def __init__(self, task_id: str, revision: int, fn: Callable[[], Any]):
        super().__init__()
        self.task_id = task_id
        self.revision = revision
        self.fn = fn
        self.signals = _SchedulerSignals()

    def run(self) -> None:
        try:
            self.signals.finished.emit(self.task_id, self.revision, self.fn())
        except Exception as exc:  # pragma: no cover - thread boundary
            self.signals.failed.emit(self.task_id, self.revision, str(exc))


@dataclass(slots=True)
class _TaskEntry:
    request: TaskRequest
    revision: int
    fn: Callable[[], Any]
    on_success: Callable[[Any], None]
    on_error: Callable[[str], None]
    on_started: Callable[[], None] | None = None
    on_finished: Callable[[], None] | None = None
    token: TaskToken | None = None
    dropped: bool = False
    expired: bool = False
    started_at: float = 0.0


class WorkSchedulerCore(QObject):
    taskQueued = Signal(str)
    taskStarted = Signal(str)
    taskCancelled = Signal(str)
    taskFinished = Signal(str)
    taskFailed = Signal(str, str)
    taskStateChanged = Signal()

    def __init__(self):
        super().__init__()
        self.pool = QThreadPool.globalInstance()
        self._queues: dict[str, deque[_TaskEntry]] = {}
        self._running: dict[str, _TaskEntry] = {}
        self._running_by_lane: dict[str, set[str]] = {}
        self._revisions: dict[str, int] = {}
        self._timeouts: dict[str, QTimer] = {}
        self._states: dict[str, ScheduledTaskState] = {}
        self._run_counts: dict[str, int] = {}

    def submit(
        self,
        request: TaskRequest,
        fn: Callable[[], Any],
        on_success: Callable[[Any], None],
        on_error: Callable[[str], None],
        on_started: Callable[[], None] | None = None,
        on_finished: Callable[[], None] | None = None,
    ) -> int:
        if request.policy not in {"enqueue", "replace", "drop"}:
            request.policy = "enqueue"

        if request.policy == "drop" and self._is_known(request.task_id):
            return self._revisions.get(request.task_id, 0)

        revision = self._revisions.get(request.task_id, 0) + 1
        self._revisions[request.task_id] = revision
        entry = _TaskEntry(
            request=request,
            revision=revision,
            fn=fn,
            on_success=on_success,
            on_error=on_error,
            on_started=on_started,
            on_finished=on_finished,
            token=TaskToken() if request.cancellable else None,
        )

        if request.policy == "replace":
            self.cancel(request.task_id, keep_running=True)

        queue = self._queues.setdefault(request.lane, deque())
        queue.append(entry)
        self._set_state(
            request.task_id,
            ScheduledTaskState(
                task_id=request.task_id,
                consumer_id=request.consumer_id,
                lane=request.lane,
                status="queued",
                priority=request.priority,
                queued=True,
                revision=revision,
            ),
        )
        self.taskQueued.emit(request.task_id)
        self._pump(request.lane)
        return revision

    def cancel(self, task_id: str, keep_running: bool = False) -> None:
        cancelled = False
        for lane, queue in self._queues.items():
            pending = deque()
            while queue:
                entry = queue.popleft()
                if entry.request.task_id == task_id:
                    entry.dropped = True
                    entry.token and entry.token.cancel()
                    cancelled = True
                else:
                    pending.append(entry)
            self._queues[lane] = pending

        if task_id in self._running:
            self._running[task_id].token and self._running[task_id].token.cancel()
            if not keep_running or self._running[task_id].request.cancellable:
                self._running[task_id].dropped = True
                cancelled = True

        if cancelled:
            state = self._states.get(task_id)
            if state:
                state.status = "cancelled"
                state.queued = False
                state.running = False
            self.taskCancelled.emit(task_id)
            self.taskStateChanged.emit()

    def cancel_consumer(self, consumer_id: str) -> None:
        if not consumer_id:
            return
        task_ids = [
            task_id
            for task_id, state in self._states.items()
            if state.consumer_id == consumer_id and (state.queued or state.running)
        ]
        for task_id in task_ids:
            self.cancel(task_id)

    def states(self) -> list[dict[str, Any]]:
        return [
            {
                "task_id": state.task_id,
                "consumer_id": state.consumer_id,
                "lane": state.lane,
                "status": state.status,
                "priority": state.priority,
                "queued": state.queued,
                "running": state.running,
                "revision": state.revision,
                "message": state.message,
                "last_duration_ms": state.last_duration_ms,
                "run_count": state.run_count,
            }
            for state in sorted(self._states.values(), key=lambda item: (item.lane, item.task_id))
        ]

    def _is_known(self, task_id: str) -> bool:
        if task_id in self._running:
            return True
        return any(entry.request.task_id == task_id for queue in self._queues.values() for entry in queue)

    def _pump(self, lane: str) -> None:
        queue = self._queues.setdefault(lane, deque())
        while queue:
            next_entry = queue[0]
            if not self._can_start(next_entry):
                return
            queue.popleft()
            if next_entry.dropped:
                continue
            self._start(next_entry)

    def _can_start(self, entry: _TaskEntry) -> bool:
        lane_running = self._running_by_lane.setdefault(entry.request.lane, set())
        if len(lane_running) >= max(1, entry.request.max_concurrency):
            return False
        if entry.request.exclusive and self._running:
            return False
        if not entry.request.exclusive:
            for running in self._running.values():
                if running.request.exclusive:
                    return False
        return True

    def _start(self, entry: _TaskEntry) -> None:
        task_id = entry.request.task_id
        runnable = _ScheduledRunnable(task_id, entry.revision, lambda: entry.fn(entry.token))
        runnable.signals.finished.connect(self._handle_finished)
        runnable.signals.failed.connect(self._handle_failed)

        self._running[task_id] = entry
        self._running_by_lane.setdefault(entry.request.lane, set()).add(task_id)
        entry.started_at = time.perf_counter()
        self._set_state(
            task_id,
            ScheduledTaskState(
                task_id=task_id,
                consumer_id=entry.request.consumer_id,
                lane=entry.request.lane,
                status="running",
                priority=entry.request.priority,
                queued=False,
                running=True,
                revision=entry.revision,
                run_count=self._run_counts.get(task_id, 0),
            ),
        )
        if entry.request.timeout_ms > 0:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda task=task_id, revision=entry.revision: self._expire(task, revision))
            timer.start(entry.request.timeout_ms)
            self._timeouts[task_id] = timer
        if entry.on_started:
            entry.on_started()
        self.taskStarted.emit(task_id)
        self.pool.start(runnable)

    def _expire(self, task_id: str, revision: int) -> None:
        entry = self._running.get(task_id)
        if not entry or entry.revision != revision:
            return
        entry.expired = True
        entry.dropped = True
        self._finish_entry(task_id)
        entry.on_error("任务超时")
        if entry.on_finished:
            entry.on_finished()
        self.taskFailed.emit(task_id, "任务超时")

    def _handle_finished(self, task_id: str, revision: int, result: object) -> None:
        entry = self._running.get(task_id)
        if not entry or entry.revision != revision:
            return
        expired = entry.expired
        dropped = entry.dropped or self._revisions.get(task_id, revision) != revision
        self._finish_entry(task_id)
        if not expired and not dropped:
            entry.on_success(result)
        if entry.on_finished:
            entry.on_finished()
        if dropped and entry.request.cancellable:
            self.taskCancelled.emit(task_id)
        else:
            self.taskFinished.emit(task_id)

    def _handle_failed(self, task_id: str, revision: int, message: str) -> None:
        entry = self._running.get(task_id)
        if not entry or entry.revision != revision:
            return
        dropped = entry.dropped or self._revisions.get(task_id, revision) != revision
        self._finish_entry(task_id)
        if not dropped:
            entry.on_error(message)
            self.taskFailed.emit(task_id, message)
        elif entry.request.cancellable:
            self.taskCancelled.emit(task_id)
        if entry.on_finished:
            entry.on_finished()

    def _finish_entry(self, task_id: str) -> None:
        entry = self._running.pop(task_id, None)
        if not entry:
            return
        lane_running = self._running_by_lane.setdefault(entry.request.lane, set())
        lane_running.discard(task_id)
        timer = self._timeouts.pop(task_id, None)
        if timer:
            timer.stop()
            timer.deleteLater()
        duration_ms = max(0.0, (time.perf_counter() - entry.started_at) * 1000.0) if entry.started_at else 0.0
        self._run_counts[task_id] = self._run_counts.get(task_id, 0) + 1
        self._set_state(
            task_id,
            ScheduledTaskState(
                task_id=task_id,
                consumer_id=entry.request.consumer_id,
                lane=entry.request.lane,
                status="idle",
                priority=entry.request.priority,
                queued=False,
                running=False,
                revision=entry.revision,
                last_duration_ms=duration_ms,
                run_count=self._run_counts[task_id],
            ),
        )
        self._pump(entry.request.lane)
        for lane in list(self._queues.keys()):
            self._pump(lane)

    def _set_state(self, task_id: str, state: ScheduledTaskState) -> None:
        self._states[task_id] = state
        self.taskStateChanged.emit()
