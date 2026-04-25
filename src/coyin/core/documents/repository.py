from __future__ import annotations

from pathlib import Path

from coyin.core.common import now_iso, short_id
from coyin.core.documents.adapters import DocumentAdapterRegistry
from coyin.core.documents.models import DocumentDescriptor, DocumentKind, DocumentSnapshot
from coyin.core.tasks import TaskToken


class DocumentRepository:
    def __init__(self, registry: DocumentAdapterRegistry):
        self.registry = registry
        self._snapshot_cache: dict[tuple[str, str, int], DocumentSnapshot] = {}

    def import_path(self, path: Path) -> DocumentDescriptor | None:
        adapter = self.registry.for_path(path)
        if not adapter:
            return None
        return adapter.create_descriptor(path)

    def _cache_key(self, descriptor: DocumentDescriptor, mode: str) -> tuple[str, str, int]:
        path = Path(descriptor.path)
        stamp = path.stat().st_mtime_ns if path.exists() else 0
        return descriptor.document_id, mode, stamp

    def load_snapshot(self, descriptor: DocumentDescriptor, task_token: TaskToken | None = None) -> DocumentSnapshot:
        cache_key = self._cache_key(descriptor, "full")
        if descriptor.kind == DocumentKind.PDF.value:
            cached = self._snapshot_cache.get(cache_key)
            if cached is not None:
                return cached
        adapter = self.registry.for_path(Path(descriptor.path))
        if not adapter:
            return DocumentSnapshot(document_id=descriptor.document_id, raw_text="", blocks=[])
        snapshot = adapter.load_snapshot(descriptor, task_token=task_token)
        if descriptor.kind == DocumentKind.PDF.value:
            self._snapshot_cache[cache_key] = snapshot
        return snapshot

    def load_reader_snapshot(self, descriptor: DocumentDescriptor, task_token: TaskToken | None = None) -> DocumentSnapshot:
        cache_key = self._cache_key(descriptor, "reader")
        if descriptor.kind == DocumentKind.PDF.value:
            cached = self._snapshot_cache.get(cache_key)
            if cached is not None:
                return cached
        adapter = self.registry.for_path(Path(descriptor.path))
        if not adapter:
            return DocumentSnapshot(document_id=descriptor.document_id, raw_text="", blocks=[])
        snapshot = adapter.load_reader_snapshot(descriptor, task_token=task_token)
        if descriptor.kind == DocumentKind.PDF.value:
            self._snapshot_cache[cache_key] = snapshot
        return snapshot

    def invalidate(self, descriptor: DocumentDescriptor) -> None:
        prefix = descriptor.document_id
        keys = [key for key in self._snapshot_cache if key[0] == prefix]
        for key in keys:
            self._snapshot_cache.pop(key, None)

    def create_draft_descriptor(self, path: Path, title: str) -> DocumentDescriptor:
        return DocumentDescriptor(
            document_id=short_id("draft"),
            title=title,
            path=str(path),
            kind=DocumentKind.DRAFT.value,
            added_at=now_iso(),
            last_opened=now_iso(),
            excerpt="",
        )

    def create_descriptor_for_kind(self, path: Path, title: str, kind: DocumentKind) -> DocumentDescriptor:
        descriptor = DocumentDescriptor(
            document_id=short_id("doc"),
            title=title,
            path=str(path),
            kind=kind.value,
            added_at=now_iso(),
            last_opened=now_iso(),
            excerpt="",
        )
        return descriptor
