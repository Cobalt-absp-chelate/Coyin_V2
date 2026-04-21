from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import Any, Iterable

from coyin.native.bridge import load_model_contracts


@dataclass(frozen=True, slots=True)
class SortRule:
    field: str
    order: str = "asc"

    @property
    def descending(self) -> bool:
        return self.order.lower() == "desc"


@dataclass(frozen=True, slots=True)
class ModelContract:
    key: str
    roles: tuple[str, ...]
    primary_key: str = ""
    sort_rules: tuple[SortRule, ...] = ()
    empty_title: str = ""
    empty_summary: str = ""


FALLBACK_MODEL_CONTRACTS: dict[str, dict[str, Any]] = {
    "homePath": {
        "roles": [
            "path_id",
            "title",
            "caption",
            "detail",
            "badge",
            "page_id",
            "action_id",
            "action_label",
            "mark",
            "tone",
        ],
        "primaryKey": "path_id",
        "sort": [{"field": "title", "order": "asc"}],
    },
    "homeMetric": {
        "roles": ["metric_id", "label", "value", "detail", "tone"],
        "primaryKey": "metric_id",
        "sort": [{"field": "metric_id", "order": "asc"}],
    },
    "library": {
        "roles": [
            "document_id",
            "display_title",
            "kind",
            "kind_label",
            "authors",
            "year",
            "source",
            "source_label",
            "group_id",
            "group_color",
            "progress",
            "excerpt",
            "annotation_count",
            "metadata_summary",
            "favorite",
            "last_opened",
            "status_line",
        ],
        "primaryKey": "document_id",
        "sort": [
            {"field": "favorite", "order": "desc"},
            {"field": "last_opened", "order": "desc"},
            {"field": "year", "order": "desc"},
            {"field": "display_title", "order": "asc"},
        ],
        "emptyTitle": "当前资料视图",
        "emptySummary": "当前筛选下无结果。",
    },
    "searchSource": {
        "roles": ["source_id", "label", "result_count", "available_count", "summary"],
        "primaryKey": "source_id",
        "sort": [{"field": "label", "order": "asc"}],
    },
    "searchResult": {
        "roles": [
            "result_id",
            "title",
            "authors",
            "year",
            "item_type",
            "abstract_text",
            "source_id",
            "source_label",
            "landing_url",
            "pdf_url",
            "venue",
            "doi",
            "has_pdf",
            "meta_summary",
            "status_line",
        ],
        "primaryKey": "result_id",
        "sort": [
            {"field": "has_pdf", "order": "desc"},
            {"field": "year", "order": "desc"},
            {"field": "title", "order": "asc"},
        ],
        "emptyTitle": "结果状态",
        "emptySummary": "暂无检索结果。",
    },
    "analysisHistory": {
        "roles": [
            "report_id",
            "document_id",
            "title",
            "created_at",
            "summary",
            "reading_note",
            "latex_snippet",
            "field_count",
            "experiment_count",
            "comparison_count",
            "status_line",
        ],
        "primaryKey": "report_id",
        "sort": [{"field": "created_at", "order": "desc"}],
    },
    "plugin": {
        "roles": [
            "plugin_id",
            "name",
            "version",
            "author",
            "description",
            "builtin",
            "plugin_enabled",
            "default_enabled",
            "capabilities",
            "load_error",
            "state_label",
        ],
        "primaryKey": "plugin_id",
        "sort": [
            {"field": "plugin_enabled", "order": "desc"},
            {"field": "builtin", "order": "desc"},
            {"field": "name", "order": "asc"},
        ],
    },
    "group": {
        "roles": ["group_id", "name", "group_color", "document_count", "summary"],
        "primaryKey": "group_id",
        "sort": [{"field": "document_count", "order": "desc"}],
    },
    "kindOption": {
        "roles": ["id", "label", "count"],
        "primaryKey": "id",
        "sort": [{"field": "label", "order": "asc"}],
    },
    "recentNote": {
        "roles": ["note_id", "title", "content", "created_at", "status_line"],
        "primaryKey": "note_id",
        "sort": [{"field": "created_at", "order": "desc"}],
    },
    "recentSearch": {
        "roles": ["label"],
        "primaryKey": "label",
    },
    "recentLatex": {
        "roles": ["session_id", "title", "template", "path", "updated_at", "status_line"],
        "primaryKey": "session_id",
        "sort": [{"field": "updated_at", "order": "desc"}],
    },
    "provider": {
        "roles": [
            "provider_id",
            "name",
            "base_url",
            "api_key",
            "default_model",
            "analysis_model",
            "active",
            "state_label",
        ],
        "primaryKey": "provider_id",
        "sort": [{"field": "name", "order": "asc"}],
    },
    "settingsSummary": {
        "roles": ["entry_id", "title", "value", "detail", "state"],
        "primaryKey": "entry_id",
        "sort": [{"field": "title", "order": "asc"}],
    },
}


def _normalize_contract(key: str, payload: dict[str, Any]) -> ModelContract:
    roles = tuple(str(item) for item in payload.get("roles", []))
    rules = tuple(
        SortRule(field=str(rule.get("field", "")), order=str(rule.get("order", "asc")))
        for rule in payload.get("sort", [])
        if str(rule.get("field", "")).strip()
    )
    return ModelContract(
        key=key,
        roles=roles,
        primary_key=str(payload.get("primaryKey", "")),
        sort_rules=rules,
        empty_title=str(payload.get("emptyTitle", "")),
        empty_summary=str(payload.get("emptySummary", "")),
    )


@lru_cache(maxsize=1)
def _contracts() -> dict[str, ModelContract]:
    payload = load_model_contracts() or FALLBACK_MODEL_CONTRACTS
    return {key: _normalize_contract(key, value) for key, value in payload.items()}


def contract_for(key: str) -> ModelContract:
    return _contracts().get(key, _normalize_contract(key, {"roles": []}))


def roles_for_contract(key: str) -> list[str]:
    return list(contract_for(key).roles)


def _sortable_value(value: Any) -> tuple[int, Any]:
    if value is None:
        return (1, "")
    if isinstance(value, bool):
        return (0, int(value))
    if isinstance(value, (int, float)):
        return (0, value)

    text = str(value).strip()
    if not text:
        return (1, "")

    try:
        return (0, float(text))
    except ValueError:
        pass

    try:
        return (0, datetime.fromisoformat(text))
    except ValueError:
        pass

    return (0, text.lower())


def sort_records(contract_key: str, records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    contract = contract_for(contract_key)
    rows = [dict(row) for row in records]
    if not contract.sort_rules:
        return rows

    for rule in reversed(contract.sort_rules):
        rows.sort(key=lambda item, field=rule.field: _sortable_value(item.get(field)), reverse=rule.descending)
    return rows
