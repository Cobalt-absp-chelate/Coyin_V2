from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any

from coyin.core.documents.models import DocumentDescriptor


@dataclass(slots=True)
class LibraryGroup:
    group_id: str
    name: str
    color: str
    order: int


@dataclass(slots=True)
class ProviderConfig:
    provider_id: str
    name: str
    base_url: str
    api_key: str
    default_model: str
    analysis_model: str = ""
    assistant_model: str = ""
    translation_model: str = ""
    active: bool = False


@dataclass(slots=True)
class PluginRuntimeState:
    plugin_id: str
    enabled: bool = False
    config: dict[str, Any] = field(default_factory=dict)
    load_error: str = ""


@dataclass(slots=True)
class ResearchNote:
    note_id: str
    title: str
    content: str
    linked_document_id: str = ""
    linked_annotation_id: str = ""
    linked_report_id: str = ""
    created_at: str = ""


@dataclass(slots=True)
class LatexSessionState:
    session_id: str
    title: str
    template: str
    path: str
    updated_at: str
    linked_document_id: str = ""
    linked_report_id: str = ""
    linked_draft_id: str = ""
    compile_status: str = "idle"
    last_export_path: str = ""
    last_error: str = ""


@dataclass(slots=True)
class AnalysisReportState:
    report_id: str
    document_id: str
    title: str
    created_at: str
    summary: str
    contributions: list[str] = field(default_factory=list)
    experiments: list[dict[str, str]] = field(default_factory=list)
    method_steps: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    comparisons: list[dict[str, str]] = field(default_factory=list)
    reading_note: str = ""
    latex_snippet: str = ""
    fields: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ArtifactLink:
    link_id: str
    source_kind: str
    source_id: str
    target_kind: str
    target_id: str
    relation_kind: str
    label: str = ""
    source_anchor: str = ""
    target_anchor: str = ""
    created_at: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class UiState:
    theme: str = "light"
    sidebar_collapsed: bool = False
    banner_parallax_enabled: bool = True
    banner_preset_id: str = "preset_academic"
    custom_banner_background_path: str = ""
    custom_banner_midground_path: str = ""
    custom_banner_foreground_path: str = ""
    custom_banner_overlay_path: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "UiState":
        data = dict(payload or {})
        if "depth_effect_enabled" in data and "banner_parallax_enabled" not in data:
            data["banner_parallax_enabled"] = bool(data.get("depth_effect_enabled"))
        allowed = {field.name for field in fields(cls)}
        filtered = {key: value for key, value in data.items() if key in allowed}
        if not filtered.get("banner_preset_id"):
            filtered["banner_preset_id"] = "preset_academic"
        return cls(**filtered)


@dataclass(slots=True)
class WorkflowState:
    current_page: str = "home"
    current_document_id: str = ""
    current_analysis_id: str = ""
    current_draft_id: str = ""
    current_latex_session_id: str = ""
    current_search_query: str = ""
    current_search_sources: list[str] = field(default_factory=list)
    page_revision: int = 0
    document_revision: int = 0
    analysis_revision: int = 0
    writing_revision: int = 0
    search_revision: int = 0


@dataclass(slots=True)
class WorkspaceState:
    documents: list[DocumentDescriptor] = field(default_factory=list)
    groups: list[LibraryGroup] = field(default_factory=list)
    notes: list[ResearchNote] = field(default_factory=list)
    recent_latex_sessions: list[LatexSessionState] = field(default_factory=list)
    analyses: list[AnalysisReportState] = field(default_factory=list)
    links: list[ArtifactLink] = field(default_factory=list)
    recent_searches: list[str] = field(default_factory=list)
    recent_opened_ids: list[str] = field(default_factory=list)
    recent_writer_ids: list[str] = field(default_factory=list)
    plugin_states: list[PluginRuntimeState] = field(default_factory=list)
    providers: list[ProviderConfig] = field(default_factory=list)
    ui: UiState = field(default_factory=UiState)
    workflow: WorkflowState = field(default_factory=WorkflowState)

    @classmethod
    def create_default(cls) -> "WorkspaceState":
        return cls(
            groups=[
                LibraryGroup("inbox", "收集箱", "#40607c", 0),
                LibraryGroup("method", "方法与实验", "#5a6b54", 1),
                LibraryGroup("survey", "综述与回顾", "#7f6747", 2),
            ],
            providers=[
                ProviderConfig(
                    provider_id="default",
                    name="默认 OpenAI 兼容接口",
                    base_url="https://api.openai.com/v1",
                    api_key="",
                    default_model="gpt-4o-mini",
                    analysis_model="gpt-4o-mini",
                    assistant_model="gpt-4o-mini",
                    translation_model="gpt-4o-mini",
                    active=False,
                )
            ],
        )
