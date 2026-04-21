from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from coyin.core.common import dataclass_to_dict, hash_file, read_json, short_id, write_json


@dataclass(slots=True)
class ResourceHandle:
    resource_id: str
    kind: str
    path: str
    fingerprint: str
    references: int = 0
    meta: dict[str, Any] = field(default_factory=dict)


class ResourceCatalog:
    def __init__(self, storage_file: Path):
        self.storage_file = storage_file
        payload = read_json(storage_file, [])
        self._resources = [ResourceHandle(**item) for item in payload]

    def _persist(self) -> None:
        write_json(self.storage_file, dataclass_to_dict(self._resources))

    def register(self, path: Path, kind: str, meta: dict[str, Any] | None = None) -> ResourceHandle:
        fingerprint = hash_file(path)
        for resource in self._resources:
            if resource.fingerprint == fingerprint:
                resource.references += 1
                self._persist()
                return resource
        handle = ResourceHandle(
            resource_id=short_id("res"),
            kind=kind,
            path=str(path),
            fingerprint=fingerprint,
            references=1,
            meta=meta or {},
        )
        self._resources.append(handle)
        self._persist()
        return handle

    def list_all(self) -> list[ResourceHandle]:
        return list(self._resources)
