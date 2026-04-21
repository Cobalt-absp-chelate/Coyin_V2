from __future__ import annotations

import ctypes
import json
from functools import lru_cache
from pathlib import Path


def _load_json(raw: str | None):
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _candidate_paths() -> list[Path]:
    root = Path(__file__).resolve().parents[3]
    return [
        root / "native" / "build" / "Release" / "coyin_native.dll",
        root / "native" / "build" / "Debug" / "coyin_native.dll",
        root / "native" / "build" / "coyin_native.dll",
        root / "native" / "build" / "libcoyin_native.dll",
    ]


@lru_cache(maxsize=1)
def _library():
    for path in _candidate_paths():
        if path.exists():
            library = ctypes.CDLL(str(path))
            if hasattr(library, "coyin_theme_json"):
                library.coyin_theme_json.argtypes = [ctypes.c_wchar_p]
                library.coyin_theme_json.restype = ctypes.c_wchar_p
            if hasattr(library, "coyin_shell_schema_json"):
                library.coyin_shell_schema_json.restype = ctypes.c_wchar_p
            if hasattr(library, "coyin_model_schema_json"):
                library.coyin_model_schema_json.restype = ctypes.c_wchar_p
            if hasattr(library, "coyin_model_contracts_json"):
                library.coyin_model_contracts_json.restype = ctypes.c_wchar_p
            if hasattr(library, "coyin_task_contracts_json"):
                library.coyin_task_contracts_json.restype = ctypes.c_wchar_p
            if hasattr(library, "coyin_library_order_ids"):
                library.coyin_library_order_ids.argtypes = [ctypes.c_wchar_p]
                library.coyin_library_order_ids.restype = ctypes.c_wchar_p
            if hasattr(library, "coyin_search_order_ids"):
                library.coyin_search_order_ids.argtypes = [ctypes.c_wchar_p]
                library.coyin_search_order_ids.restype = ctypes.c_wchar_p
            if hasattr(library, "coyin_analysis_order_ids"):
                library.coyin_analysis_order_ids.argtypes = [ctypes.c_wchar_p]
                library.coyin_analysis_order_ids.restype = ctypes.c_wchar_p
            return library
    return None


def native_available() -> bool:
    return _library() is not None


def load_theme(mode: str) -> dict | None:
    library = _library()
    if not library or not hasattr(library, "coyin_theme_json"):
        return None
    raw = library.coyin_theme_json(mode)
    return _load_json(raw)


def load_shell_schema() -> dict | None:
    library = _library()
    if not library or not hasattr(library, "coyin_shell_schema_json"):
        return None
    raw = library.coyin_shell_schema_json()
    return _load_json(raw)


def load_model_schema() -> dict | None:
    library = _library()
    if not library or not hasattr(library, "coyin_model_schema_json"):
        return None
    raw = library.coyin_model_schema_json()
    return _load_json(raw)


def load_model_contracts() -> dict | None:
    library = _library()
    if not library or not hasattr(library, "coyin_model_contracts_json"):
        return None
    raw = library.coyin_model_contracts_json()
    return _load_json(raw)


def load_task_contracts() -> dict | None:
    library = _library()
    if not library or not hasattr(library, "coyin_task_contracts_json"):
        return None
    raw = library.coyin_task_contracts_json()
    return _load_json(raw)


def _ordered_ids(function_name: str, payload: str) -> list[str] | None:
    library = _library()
    if not library or not hasattr(library, function_name):
        return None
    raw = getattr(library, function_name)(payload)
    if not raw:
        return None
    return [line.strip() for line in str(raw).splitlines() if line.strip()]


def native_library_order_ids(payload: str) -> list[str] | None:
    return _ordered_ids("coyin_library_order_ids", payload)


def native_search_order_ids(payload: str) -> list[str] | None:
    return _ordered_ids("coyin_search_order_ids", payload)


def native_analysis_order_ids(payload: str) -> list[str] | None:
    return _ordered_ids("coyin_analysis_order_ids", payload)
