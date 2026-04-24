from __future__ import annotations

import inspect
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
        signature = inspect.signature(fn)
        accepts_task_token = "task_token" in signature.parameters or any(
            parameter.kind == inspect.Parameter.VAR_KEYWORD for parameter in signature.parameters.values()
        )

        def run_with_token(task_token=None):
            if accepts_task_token:
                return fn(*args, task_token=task_token, **kwargs)
            return fn(*args, **kwargs)

        self.scheduler.submit(
            task_request,
            run_with_token,
            on_success,
            on_error,
            on_started=on_started,
            on_finished=on_finished,
        )
