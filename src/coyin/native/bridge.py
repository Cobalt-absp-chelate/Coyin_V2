from __future__ import annotations

import ctypes
import os
from functools import lru_cache
from pathlib import Path

from coyin.paths import app_root


def _candidate_paths() -> list[Path]:
    root = app_root()
    return [
        root / "build" / "native-qt" / "Release" / "coyin_native.dll",
        root / "build" / "native-qt" / "Debug" / "coyin_native.dll",
        root / "build" / "native-qt" / "coyin_native.dll",
        root / "build" / "Release" / "coyin_native.dll",
        root / "build" / "Debug" / "coyin_native.dll",
        root / "build" / "coyin_native.dll",
        root / "native" / "build" / "Release" / "coyin_native.dll",
        root / "native" / "build" / "Debug" / "coyin_native.dll",
        root / "native" / "build" / "coyin_native.dll",
        root / "native" / "build" / "libcoyin_native.dll",
    ]


def _candidate_dll_directories() -> list[Path]:
    directories: list[Path] = []
    root = app_root()
    try:
        import PySide6

        directories.append(Path(PySide6.__file__).resolve().parent)
    except Exception:
        pass

    for env_name in ("COYIN_QT_BIN", "QT_BIN_DIR", "QTDIR", "QT_DIR"):
        raw = os.environ.get(env_name, "").strip()
        if not raw:
            continue
        env_path = Path(raw)
        directories.append(env_path / "bin" if env_name in {"QTDIR", "QT_DIR"} else env_path)

    directories.extend(
        [
            root / "build" / "native-qt" / "Release",
            root / "build" / "native-qt" / "Debug",
            root / "build" / "native-qt",
        ]
    )

    for raw_path in os.environ.get("PATH", "").split(os.pathsep):
        text = raw_path.strip()
        if not text:
            continue
        candidate = Path(text)
        lower = str(candidate).lower()
        if "qt" in lower or "pyside" in lower:
            directories.append(candidate)

    seen: set[Path] = set()
    ordered: list[Path] = []
    for directory in directories:
        if not directory.exists() or directory in seen:
            continue
        seen.add(directory)
        ordered.append(directory)
    return ordered


@lru_cache(maxsize=1)
def _dll_handles():
    handles = []
    add_directory = getattr(os, "add_dll_directory", None)
    if add_directory is None:
        return handles
    for directory in _candidate_dll_directories():
        try:
            handles.append(add_directory(str(directory)))
        except OSError:
            continue
    return handles


@lru_cache(maxsize=1)
def _library():
    _dll_handles()
    for path in _candidate_paths():
        if path.exists():
            library = ctypes.CDLL(str(path))
            if hasattr(library, "coyin_library_order_ids"):
                library.coyin_library_order_ids.argtypes = [ctypes.c_wchar_p]
                library.coyin_library_order_ids.restype = ctypes.c_wchar_p
            if hasattr(library, "coyin_search_order_ids"):
                library.coyin_search_order_ids.argtypes = [ctypes.c_wchar_p]
                library.coyin_search_order_ids.restype = ctypes.c_wchar_p
            if hasattr(library, "coyin_analysis_order_ids"):
                library.coyin_analysis_order_ids.argtypes = [ctypes.c_wchar_p]
                library.coyin_analysis_order_ids.restype = ctypes.c_wchar_p
            if hasattr(library, "coyin_register_qml_types"):
                library.coyin_register_qml_types.argtypes = []
                library.coyin_register_qml_types.restype = ctypes.c_int
            return library
    return None


def native_available() -> bool:
    return _library() is not None

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


def register_qml_types_native() -> bool:
    library = _library()
    if not library or not hasattr(library, "coyin_register_qml_types"):
        return False
    try:
        return bool(library.coyin_register_qml_types())
    except Exception:
        return False
