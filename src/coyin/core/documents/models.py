from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class DocumentKind(StrEnum):
    PDF = "pdf"
    MARKDOWN = "markdown"
    TEXT = "text"
    DOCX = "docx"
    DOC = "doc"
    LATEX = "latex"
    DRAFT = "draft"


class AnnotationKind(StrEnum):
    HIGHLIGHT = "highlight"
    UNDERLINE = "underline"
    NOTE = "note"
    TRANSLATION = "translation"


@dataclass(slots=True)
class OutlineItem:
    title: str
    page: int | None = None
    anchor: str | None = None
    children: list["OutlineItem"] = field(default_factory=list)


@dataclass(slots=True)
class DocumentBlock:
    block_id: str
    kind: str
    text: str
    page: int | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ResourceRef:
    resource_id: str
    kind: str
    path: str
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DocumentDescriptor:
    document_id: str
    title: str
    path: str
    kind: str
    authors: list[str] = field(default_factory=list)
    year: str = ""
    source: str = ""
    tags: list[str] = field(default_factory=list)
    group_id: str = "inbox"
    group_color: str = "#40607c"
    favorite: bool = False
    archived: bool = False
    progress: float = 0.0
    added_at: str = ""
    last_opened: str = ""
    fingerprint: str = ""
    excerpt: str = ""
    keywords: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    workflow_label: str = ""


@dataclass(slots=True)
class DocumentSnapshot:
    document_id: str
    raw_text: str
    blocks: list[DocumentBlock] = field(default_factory=list)
    outline: list[OutlineItem] = field(default_factory=list)
    resources: list[ResourceRef] = field(default_factory=list)
    page_count: int = 0
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class DraftState:
    draft_id: str
    title: str
    html: str
    plain_text: str
    resources: list[str] = field(default_factory=list)
    references: list[dict[str, Any]] = field(default_factory=list)
    updated_at: str = ""


@dataclass(slots=True)
class AnnotationRecord:
    annotation_id: str
    document_id: str
    kind: str
    color: str
    page: int | None = None
    anchor: str = ""
    quote: str = ""
    note: str = ""
    rects: list[dict[str, float]] = field(default_factory=list)
    linked_note_id: str = ""
    created_at: str = ""


@dataclass(slots=True)
class SearchResult:
    result_id: str
    source_id: str
    title: str
    authors: list[str]
    year: str
    item_type: str
    abstract: str
    landing_url: str
    pdf_url: str = ""
    doi: str = ""
    venue: str = ""
    raw: dict[str, Any] = field(default_factory=dict)
