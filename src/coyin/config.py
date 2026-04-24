from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from coyin.paths import app_root


def _config_root() -> Path:
    return app_root() / "assets" / "config"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def _load(relative_path: str) -> Any:
    return _read_json(_config_root() / relative_path)


def theme_tokens(mode: str) -> dict[str, Any]:
    normalized = "dark" if mode == "dark" else "light"
    return dict(_load(f"themes/{normalized}.json"))


def shell_schema() -> dict[str, Any]:
    return dict(_load("shell_schema.json"))


def model_contracts() -> dict[str, Any]:
    payload = _load("model_contracts.json")
    return {key: dict(value) for key, value in payload.items()}


def task_contracts() -> dict[str, Any]:
    payload = _load("task_contracts.json")
    return {key: dict(value) for key, value in payload.items()}
