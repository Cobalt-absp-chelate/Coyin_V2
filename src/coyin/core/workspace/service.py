from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from PySide6.QtCore import QObject, Signal

from coyin.core.common import dataclass_to_dict, now_iso, read_json, short_id, write_json
from coyin.core.documents.models import DocumentDescriptor, DraftState
from coyin.core.workspace.state import (
    AnalysisReportState,
    ArtifactLink,
    LatexSessionState,
    LibraryGroup,
    PluginRuntimeState,
    ProviderConfig,
    ResearchNote,
    UiState,
    WorkflowState,
    WorkspaceState,
)


def _document_from_dict(payload: dict) -> DocumentDescriptor:
    return DocumentDescriptor(**payload)


def _group_from_dict(payload: dict) -> LibraryGroup:
    return LibraryGroup(**payload)


def _note_from_dict(payload: dict) -> ResearchNote:
    return ResearchNote(**payload)


def _analysis_from_dict(payload: dict) -> AnalysisReportState:
    return AnalysisReportState(**payload)


def _link_from_dict(payload: dict) -> ArtifactLink:
    return ArtifactLink(**payload)


def _latex_session_from_dict(payload: dict) -> LatexSessionState:
    return LatexSessionState(**payload)


def _plugin_state_from_dict(payload: dict) -> PluginRuntimeState:
    return PluginRuntimeState(**payload)


def _provider_from_dict(payload: dict) -> ProviderConfig:
    return ProviderConfig(**payload)


def _workflow_from_dict(payload: dict) -> WorkflowState:
    return WorkflowState(**payload)


class WorkspaceService(QObject):
    state_changed = Signal()
    library_changed = Signal()
    analyses_changed = Signal()
    settings_changed = Signal()
    document_opened = Signal(str)

    def __init__(self, workspace_file: Path):
        super().__init__()
        self.workspace_file = workspace_file
        self.state = self._normalize_state(self._load_state())
        self._save_state(self.state)

    def _load_state(self) -> WorkspaceState:
        payload = read_json(self.workspace_file, {})
        if not payload:
            state = WorkspaceState.create_default()
            self._save_state(state)
            return state
        return WorkspaceState(
            documents=[_document_from_dict(item) for item in payload.get("documents", [])],
            groups=[_group_from_dict(item) for item in payload.get("groups", [])],
            notes=[_note_from_dict(item) for item in payload.get("notes", [])],
            recent_latex_sessions=[_latex_session_from_dict(item) for item in payload.get("recent_latex_sessions", [])],
            analyses=[_analysis_from_dict(item) for item in payload.get("analyses", [])],
            links=[_link_from_dict(item) for item in payload.get("links", [])],
            recent_searches=payload.get("recent_searches", []),
            recent_opened_ids=payload.get("recent_opened_ids", []),
            recent_writer_ids=payload.get("recent_writer_ids", []),
            plugin_states=[_plugin_state_from_dict(item) for item in payload.get("plugin_states", [])],
            providers=[_provider_from_dict(item) for item in payload.get("providers", [])],
            ui=UiState(**payload.get("ui", {})),
            workflow=_workflow_from_dict(payload.get("workflow", {})),
        )

    def _save_state(self, state: WorkspaceState | None = None) -> None:
        write_json(self.workspace_file, dataclass_to_dict(state or self.state))

    def _normalize_state(self, state: WorkspaceState) -> WorkspaceState:
        state.documents = self._dedupe_documents(state.documents)
        state.recent_opened_ids = self._dedupe_ids(state.recent_opened_ids)
        state.recent_writer_ids = self._dedupe_ids(state.recent_writer_ids)
        state.recent_searches = self._dedupe_ids(state.recent_searches)
        state.plugin_states = self._dedupe_plugin_states(state.plugin_states)
        state.workflow.current_search_sources = self._dedupe_ids(state.workflow.current_search_sources)
        return state

    def _dedupe_documents(self, documents: list[DocumentDescriptor]) -> list[DocumentDescriptor]:
        latest: dict[tuple[str, str], DocumentDescriptor] = {}
        for document in documents:
            marker = (document.document_id, document.path)
            current = latest.get(marker)
            if current is None or (document.last_opened or document.added_at) >= (current.last_opened or current.added_at):
                latest[marker] = document
        return sorted(latest.values(), key=lambda item: item.last_opened or item.added_at, reverse=True)

    def _dedupe_ids(self, values: list[str]) -> list[str]:
        ordered: list[str] = []
        seen: set[str] = set()
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            ordered.append(value)
        return ordered

    def _dedupe_plugin_states(self, values: list[PluginRuntimeState]) -> list[PluginRuntimeState]:
        ordered: list[PluginRuntimeState] = []
        seen: set[str] = set()
        for value in values:
            if value.plugin_id in seen:
                continue
            seen.add(value.plugin_id)
            ordered.append(value)
        return ordered

    def persist(self, emit_state: bool = True) -> None:
        self._save_state()
        if emit_state:
            self.state_changed.emit()

    def add_documents(self, documents: Iterable[DocumentDescriptor]) -> None:
        known = {document.fingerprint: document for document in self.state.documents if document.fingerprint}
        for document in documents:
            if document.fingerprint and document.fingerprint in known:
                continue
            self.state.documents.insert(0, document)
            self._touch_recent(document.document_id)
        self.persist(emit_state=False)
        self.library_changed.emit()

    def remove_document(self, document_id: str) -> None:
        self.remove_documents([document_id])

    def remove_documents(self, document_ids: Iterable[str]) -> None:
        removed = set(document_ids)
        self.state.documents = [item for item in self.state.documents if item.document_id not in removed]
        self.state.recent_opened_ids = [item for item in self.state.recent_opened_ids if item not in removed]
        self.state.recent_writer_ids = [item for item in self.state.recent_writer_ids if item not in removed]
        self.persist(emit_state=False)
        self.library_changed.emit()

    def update_document(self, descriptor: DocumentDescriptor) -> None:
        for index, current in enumerate(self.state.documents):
            if current.document_id == descriptor.document_id:
                self.state.documents[index] = descriptor
                break
        self.persist(emit_state=False)
        self.library_changed.emit()

    def mark_document_opened(self, descriptor: DocumentDescriptor) -> None:
        for index, current in enumerate(self.state.documents):
            if current.document_id == descriptor.document_id:
                self.state.documents[index] = descriptor
                break
        self._touch_recent(descriptor.document_id)
        self.persist(emit_state=False)
        self.document_opened.emit(descriptor.document_id)

    def _touch_recent(self, document_id: str) -> None:
        if document_id in self.state.recent_opened_ids:
            self.state.recent_opened_ids.remove(document_id)
        self.state.recent_opened_ids.insert(0, document_id)
        del self.state.recent_opened_ids[20:]

    def touch_recent(self, document_id: str) -> None:
        self._touch_recent(document_id)
        self.persist(emit_state=False)
        self.library_changed.emit()

    def register_recent_writer(self, draft_id: str) -> None:
        if draft_id in self.state.recent_writer_ids:
            self.state.recent_writer_ids.remove(draft_id)
        self.state.recent_writer_ids.insert(0, draft_id)
        del self.state.recent_writer_ids[20:]
        self.persist(emit_state=False)
        self.library_changed.emit()

    def add_recent_search(self, query: str) -> None:
        query = query.strip()
        if not query:
            return
        if query in self.state.recent_searches:
            self.state.recent_searches.remove(query)
        self.state.recent_searches.insert(0, query)
        del self.state.recent_searches[12:]
        self.persist(emit_state=False)
        self.library_changed.emit()

    def add_note(
        self,
        title: str,
        content: str,
        linked_document_id: str = "",
        linked_annotation_id: str = "",
        linked_report_id: str = "",
    ) -> ResearchNote:
        note = ResearchNote(
            note_id=short_id("note"),
            title=title,
            content=content,
            linked_document_id=linked_document_id,
            linked_annotation_id=linked_annotation_id,
            linked_report_id=linked_report_id,
            created_at=now_iso(),
        )
        self.state.notes.insert(0, note)
        del self.state.notes[20:]
        self.persist(emit_state=False)
        self.library_changed.emit()
        return note

    def remove_note(self, note_id: str) -> None:
        self.state.notes = [note for note in self.state.notes if note.note_id != note_id]
        self.persist(emit_state=False)
        self.library_changed.emit()

    def find_note(self, note_id: str) -> ResearchNote | None:
        for note in self.state.notes:
            if note.note_id == note_id:
                return note
        return None

    def register_latex_session(
        self,
        title: str,
        template: str,
        path: str,
        linked_document_id: str = "",
        linked_report_id: str = "",
        linked_draft_id: str = "",
    ) -> LatexSessionState:
        for session in self.state.recent_latex_sessions:
            if session.path == path:
                session.title = title
                session.template = template
                session.linked_document_id = linked_document_id or session.linked_document_id
                session.linked_report_id = linked_report_id or session.linked_report_id
                session.linked_draft_id = linked_draft_id or session.linked_draft_id
                session.updated_at = now_iso()
                self.persist(emit_state=False)
                self.library_changed.emit()
                return session
        session = LatexSessionState(
            session_id=short_id("latex"),
            title=title,
            template=template,
            path=path,
            updated_at=now_iso(),
            linked_document_id=linked_document_id,
            linked_report_id=linked_report_id,
            linked_draft_id=linked_draft_id,
        )
        self.state.recent_latex_sessions.insert(0, session)
        del self.state.recent_latex_sessions[12:]
        self.persist(emit_state=False)
        self.library_changed.emit()
        return session

    def update_latex_session(self, session_id: str, **changes) -> LatexSessionState | None:
        for session in self.state.recent_latex_sessions:
            if session.session_id == session_id:
                for key, value in changes.items():
                    if hasattr(session, key):
                        setattr(session, key, value)
                session.updated_at = now_iso()
                self.persist(emit_state=False)
                self.library_changed.emit()
                return session
        return None

    def remove_latex_session(self, session_id: str) -> None:
        self.state.recent_latex_sessions = [
            session for session in self.state.recent_latex_sessions if session.session_id != session_id
        ]
        self.persist(emit_state=False)
        self.library_changed.emit()

    def find_latex_session(self, session_id: str) -> LatexSessionState | None:
        for session in self.state.recent_latex_sessions:
            if session.session_id == session_id:
                return session
        return None

    def set_current_page(self, page_id: str) -> int:
        if page_id == self.state.workflow.current_page:
            return self.state.workflow.page_revision
        self.state.workflow.current_page = page_id
        self.state.workflow.page_revision += 1
        self.persist()
        return self.state.workflow.page_revision

    def set_current_document(self, document_id: str) -> int:
        if document_id == self.state.workflow.current_document_id:
            return self.state.workflow.document_revision
        self.state.workflow.current_document_id = document_id
        self.state.workflow.document_revision += 1
        self.persist()
        return self.state.workflow.document_revision

    def clear_current_document(self, document_id: str) -> int:
        if self.state.workflow.current_document_id != document_id:
            return self.state.workflow.document_revision
        self.state.workflow.current_document_id = ""
        self.state.workflow.document_revision += 1
        self.persist()
        return self.state.workflow.document_revision

    def set_current_analysis(self, report_id: str) -> int:
        if report_id == self.state.workflow.current_analysis_id:
            return self.state.workflow.analysis_revision
        self.state.workflow.current_analysis_id = report_id
        self.state.workflow.analysis_revision += 1
        self.persist()
        return self.state.workflow.analysis_revision

    def set_current_draft(self, draft_id: str) -> int:
        if draft_id == self.state.workflow.current_draft_id:
            return self.state.workflow.writing_revision
        self.state.workflow.current_draft_id = draft_id
        self.state.workflow.writing_revision += 1
        self.persist()
        return self.state.workflow.writing_revision

    def set_current_latex_session(self, session_id: str) -> int:
        if session_id == self.state.workflow.current_latex_session_id:
            return self.state.workflow.writing_revision
        self.state.workflow.current_latex_session_id = session_id
        self.state.workflow.writing_revision += 1
        self.persist()
        return self.state.workflow.writing_revision

    def set_search_context(self, query: str, source_ids: list[str]) -> int:
        workflow = self.state.workflow
        next_query = query.strip()
        next_sources = self._dedupe_ids([str(item) for item in source_ids if str(item).strip()])
        if workflow.current_search_query == next_query and workflow.current_search_sources == next_sources:
            return workflow.search_revision
        workflow.current_search_query = next_query
        workflow.current_search_sources = next_sources
        workflow.search_revision += 1
        self.persist()
        return workflow.search_revision

    def search_checkpoint(self) -> dict[str, object]:
        workflow = self.state.workflow
        return {
            "search_revision": workflow.search_revision,
            "page_revision": workflow.page_revision,
            "required_page": "search",
        }

    def analysis_checkpoint(self) -> dict[str, object]:
        workflow = self.state.workflow
        return {
            "page_revision": workflow.page_revision,
            "required_page": workflow.current_page,
        }

    def accepts_checkpoint(self, checkpoint: dict[str, object]) -> bool:
        workflow = self.state.workflow
        page_revision = int(checkpoint.get("page_revision", workflow.page_revision))
        if workflow.page_revision != page_revision:
            return False
        required_page = str(checkpoint.get("required_page", ""))
        if required_page and workflow.current_page != required_page:
            return False
        if "search_revision" in checkpoint:
            return workflow.search_revision == int(checkpoint.get("search_revision", workflow.search_revision))
        return True

    def add_analysis(self, report: AnalysisReportState) -> None:
        self.state.analyses.insert(0, report)
        del self.state.analyses[30:]
        self.persist(emit_state=False)
        self.analyses_changed.emit()

    def find_analysis(self, report_id: str) -> AnalysisReportState | None:
        for report in self.state.analyses:
            if report.report_id == report_id:
                return report
        return None

    def add_link(self, link: ArtifactLink) -> ArtifactLink:
        for index, current in enumerate(self.state.links):
            if (
                current.source_kind == link.source_kind
                and current.source_id == link.source_id
                and current.target_kind == link.target_kind
                and current.target_id == link.target_id
                and current.relation_kind == link.relation_kind
            ):
                self.state.links[index] = link
                self.persist(emit_state=False)
                self.library_changed.emit()
                return link
        self.state.links.insert(0, link)
        self.persist(emit_state=False)
        self.library_changed.emit()
        return link

    def link_artifacts(
        self,
        source_kind: str,
        source_id: str,
        target_kind: str,
        target_id: str,
        relation_kind: str,
        label: str = "",
        source_anchor: str = "",
        target_anchor: str = "",
        meta: dict | None = None,
    ) -> ArtifactLink:
        link = ArtifactLink(
            link_id=short_id("link"),
            source_kind=source_kind,
            source_id=source_id,
            target_kind=target_kind,
            target_id=target_id,
            relation_kind=relation_kind,
            label=label,
            source_anchor=source_anchor,
            target_anchor=target_anchor,
            created_at=now_iso(),
            meta=dict(meta or {}),
        )
        return self.add_link(link)

    def remove_link(self, link_id: str) -> None:
        self.state.links = [link for link in self.state.links if link.link_id != link_id]
        self.persist(emit_state=False)
        self.library_changed.emit()

    def remove_links(self, link_ids: Iterable[str]) -> None:
        removed = set(link_ids)
        self.state.links = [link for link in self.state.links if link.link_id not in removed]
        self.persist(emit_state=False)
        self.library_changed.emit()

    def links_for_artifact(self, kind: str, artifact_id: str) -> list[ArtifactLink]:
        return [
            link
            for link in self.state.links
            if (link.source_kind == kind and link.source_id == artifact_id)
            or (link.target_kind == kind and link.target_id == artifact_id)
        ]

    def ensure_plugin_state(self, plugin_id: str) -> PluginRuntimeState:
        for item in self.state.plugin_states:
            if item.plugin_id == plugin_id:
                return item
        runtime = PluginRuntimeState(plugin_id=plugin_id)
        self.state.plugin_states.append(runtime)
        self.persist(emit_state=False)
        self.settings_changed.emit()
        return runtime

    def plugin_state_for(self, plugin_id: str) -> PluginRuntimeState | None:
        for item in self.state.plugin_states:
            if item.plugin_id == plugin_id:
                return item
        return None

    def set_plugin_enabled(self, plugin_id: str, enabled: bool, load_error: str = "") -> None:
        runtime = self.ensure_plugin_state(plugin_id)
        runtime.enabled = enabled
        runtime.load_error = load_error
        self.persist(emit_state=False)
        self.settings_changed.emit()

    def active_provider(self) -> ProviderConfig | None:
        for provider in self.state.providers:
            if provider.active:
                return provider
        return self.state.providers[0] if self.state.providers else None

    def upsert_provider(self, provider: ProviderConfig) -> None:
        replaced = False
        for index, current in enumerate(self.state.providers):
            if current.provider_id == provider.provider_id:
                self.state.providers[index] = provider
                replaced = True
                break
        if not replaced:
            self.state.providers.append(provider)
        self.persist(emit_state=False)
        self.settings_changed.emit()

    def list_documents(self) -> list[DocumentDescriptor]:
        return list(self.state.documents)

    def find_document(self, document_id: str) -> DocumentDescriptor | None:
        for document in self.state.documents:
            if document.document_id == document_id:
                return document
        return None

    def recent_documents(self) -> list[DocumentDescriptor]:
        mapping = {document.document_id: document for document in self.state.documents}
        result = [mapping[item] for item in self.state.recent_opened_ids if item in mapping]
        return result[:8]

    def recent_writers(self) -> list[DocumentDescriptor]:
        mapping = {document.document_id: document for document in self.state.documents}
        result = [mapping[item] for item in self.state.recent_writer_ids if item in mapping]
        return result[:8]
