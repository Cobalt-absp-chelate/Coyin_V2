from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from PySide6.QtGui import QUndoCommand

from coyin.core.common import now_iso
from coyin.core.documents.models import DocumentDescriptor, DocumentKind
from coyin.core.workspace.state import ArtifactLink
from coyin.core.workspace.service import WorkspaceService


class RenameDocumentCommand(QUndoCommand):
    def __init__(self, workspace: WorkspaceService, document_id: str, new_title: str):
        super().__init__("重命名文档")
        self.workspace = workspace
        self.document_id = document_id
        self.new_title = new_title
        descriptor = workspace.find_document(document_id)
        self.old_title = descriptor.title if descriptor else ""

    def _apply(self, title: str) -> None:
        descriptor = self.workspace.find_document(self.document_id)
        if not descriptor:
            return
        descriptor = deepcopy(descriptor)
        descriptor.title = title
        descriptor.last_opened = now_iso()
        self.workspace.update_document(descriptor)

    def redo(self) -> None:
        self._apply(self.new_title)

    def undo(self) -> None:
        self._apply(self.old_title)


class ToggleDocumentFavoriteCommand(QUndoCommand):
    def __init__(self, workspace: WorkspaceService, document_id: str):
        super().__init__("切换文档收藏")
        self.workspace = workspace
        self.document_id = document_id
        descriptor = workspace.find_document(document_id)
        self.before = descriptor.favorite if descriptor else False
        self.after = not self.before

    def _apply(self, favorite: bool) -> None:
        descriptor = self.workspace.find_document(self.document_id)
        if not descriptor:
            return
        descriptor = deepcopy(descriptor)
        descriptor.favorite = favorite
        descriptor.last_opened = now_iso()
        self.workspace.update_document(descriptor)

    def redo(self) -> None:
        self._apply(self.after)

    def undo(self) -> None:
        self._apply(self.before)


class CreateDraftDocumentCommand(QUndoCommand):
    def __init__(
        self,
        workspace: WorkspaceService,
        descriptor: DocumentDescriptor,
        html: str,
        link_specs: list[dict] | None = None,
        text: str = "创建写作草稿",
    ):
        super().__init__(text)
        self.workspace = workspace
        self.descriptor = deepcopy(descriptor)
        self.html = html
        self.link_specs = list(link_specs or [])
        self._link_ids: list[str] = []

    def redo(self) -> None:
        path = Path(self.descriptor.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.html, encoding="utf-8")
        if not self.descriptor.excerpt:
            self.descriptor.excerpt = _plain_excerpt(self.html)
        self.workspace.add_documents([deepcopy(self.descriptor)])
        if not self._link_ids:
            for spec in self.link_specs:
                link = self.workspace.link_artifacts(
                    source_kind=spec["source_kind"],
                    source_id=spec["source_id"],
                    target_kind=spec.get("target_kind", "document"),
                    target_id=self.descriptor.document_id,
                    relation_kind=spec["relation_kind"],
                    label=spec.get("label", ""),
                    source_anchor=spec.get("source_anchor", ""),
                    target_anchor=spec.get("target_anchor", ""),
                    meta=spec.get("meta", {}),
                )
                self._link_ids.append(link.link_id)
        else:
            restored = []
            for spec, link_id in zip(self.link_specs, self._link_ids):
                link = self.workspace.link_artifacts(
                    source_kind=spec["source_kind"],
                    source_id=spec["source_id"],
                    target_kind=spec.get("target_kind", "document"),
                    target_id=self.descriptor.document_id,
                    relation_kind=spec["relation_kind"],
                    label=spec.get("label", ""),
                    source_anchor=spec.get("source_anchor", ""),
                    target_anchor=spec.get("target_anchor", ""),
                    meta={**spec.get("meta", {}), "restored_from": link_id},
                )
                restored.append(link.link_id)
            self._link_ids = restored

    def undo(self) -> None:
        self.workspace.remove_document(self.descriptor.document_id)
        if self._link_ids:
            self.workspace.remove_links(self._link_ids)
        path = Path(self.descriptor.path)
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass


class DeleteDocumentCommand(QUndoCommand):
    def __init__(self, workspace: WorkspaceService, descriptor: DocumentDescriptor):
        super().__init__("删除文档")
        self.workspace = workspace
        self.descriptor = deepcopy(descriptor)
        self._backup_bytes = b""
        self._backup_text = ""
        self._backup_mode = "binary"
        self._link_ids: list[str] = []
        self._backup_links: list[ArtifactLink] = []

    def redo(self) -> None:
        if not self._link_ids:
            self._backup_links = [
                deepcopy(link)
                for link in self.workspace.links_for_artifact("document", self.descriptor.document_id)
            ]
            self._link_ids = [link.link_id for link in self._backup_links]
        path = Path(self.descriptor.path)
        if path.exists() and not self._backup_bytes and not self._backup_text:
            try:
                self._backup_bytes = path.read_bytes()
                self._backup_mode = "binary"
            except Exception:
                try:
                    self._backup_text = path.read_text(encoding="utf-8", errors="ignore")
                    self._backup_mode = "text"
                except Exception:
                    self._backup_bytes = b""
        self.workspace.remove_document(self.descriptor.document_id)
        if self._link_ids:
            self.workspace.remove_links(self._link_ids)
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass

    def undo(self) -> None:
        path = Path(self.descriptor.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if self._backup_mode == "text":
            path.write_text(self._backup_text, encoding="utf-8")
        else:
            path.write_bytes(self._backup_bytes)
        self.workspace.add_documents([deepcopy(self.descriptor)])
        for link in self._backup_links:
            self.workspace.add_link(deepcopy(link))


def _plain_excerpt(html: str) -> str:
    text = html.replace("<br/>", " ").replace("<br>", " ").replace("</p>", " ")
    cleaned = []
    inside = False
    for char in text:
        if char == "<":
            inside = True
            continue
        if char == ">":
            inside = False
            continue
        if not inside:
            cleaned.append(char)
    return "".join(cleaned).strip()[:200]
