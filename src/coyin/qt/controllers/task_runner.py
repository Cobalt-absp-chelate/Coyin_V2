from __future__ import annotations

from typing import Any, Callable

from coyin.core.tasks import TaskRequest, WorkSchedulerCore


class TaskRunner:
    def __init__(self, scheduler: WorkSchedulerCore):
        self.scheduler = scheduler

    def submit(
        self,
        fn: Callable[..., Any],
        on_success: Callable[[Any], None],
        on_error: Callable[[str], None],
        *args: Any,
        request: TaskRequest | None = None,
        on_started: Callable[[], None] | None = None,
        on_finished: Callable[[], None] | None = None,
        **kwargs: Any,
    ) -> None:
        task_request = request or TaskRequest(task_id="background", lane="general")
        self.scheduler.submit(
            task_request,
            lambda: fn(*args, **kwargs),
            on_success,
            on_error,
            on_started=on_started,
            on_finished=on_finished,
        )
