from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from coyin.core.documents.models import DocumentDescriptor, DocumentKind, SearchResult
from coyin.core.indexing.contracts import sort_records
from coyin.core.workspace.state import AnalysisReportState
from coyin.native.bridge import native_analysis_order_ids, native_library_order_ids, native_search_order_ids


KIND_LABELS = {
    DocumentKind.PDF.value: "PDF",
    DocumentKind.MARKDOWN.value: "Markdown",
    DocumentKind.TEXT.value: "文本",
    DocumentKind.DOCX.value: "DOCX",
    DocumentKind.DOC.value: "DOC",
    DocumentKind.LATEX.value: "LaTeX",
    DocumentKind.DRAFT.value: "文档草稿",
}

FIELD_LABELS = {
    "datasets": "数据集",
    "reproducibility": "可复现信息",
    "future_work": "未来工作",
    "bibtex_note": "引文整理建议",
    "figure_mentions": "图表提及",
    "glossary_watch": "术语观察",
}


@dataclass(slots=True)
class LibraryFilters:
    query: str = ""
    group_id: str = "all"
    kind: str = "all"
    recent_only: bool = False


class WorkspaceIndexCore:
    def __init__(self, workspace, annotation_store, plugin_manager, search_service):
        self.workspace = workspace
        self.annotation_store = annotation_store
        self.plugin_manager = plugin_manager
        self.search_service = search_service
        self.library_filters = LibraryFilters()
        self._search_results: list[SearchResult] = []

    def _order_with_native(self, rows: list[dict[str, Any]], function, payload_builder) -> list[dict[str, Any]]:
        ordered = function(payload_builder(rows))
        if not ordered:
            return rows
        mapping = {row.get("document_id") or row.get("result_id") or row.get("report_id"): row for row in rows}
        native_rows = [mapping[item_id] for item_id in ordered if item_id in mapping]
        seen = {item.get("document_id") or item.get("result_id") or item.get("report_id") for item in native_rows}
        native_rows.extend(
            row
            for row in rows
            if (row.get("document_id") or row.get("result_id") or row.get("report_id")) not in seen
        )
        return native_rows

    def set_library_query(self, query: str) -> None:
        self.library_filters.query = query

    def set_library_group(self, group_id: str) -> None:
        self.library_filters.group_id = group_id or "all"

    def set_library_kind(self, kind: str) -> None:
        self.library_filters.kind = kind or "all"

    def set_library_recent_only(self, recent_only: bool) -> None:
        self.library_filters.recent_only = bool(recent_only)

    def reset_library_filters(self) -> None:
        self.library_filters = LibraryFilters()

    def set_search_context(self, results: Iterable[SearchResult], query: str, source_ids: list[str]) -> None:
        self._search_results = list(results)
        self.workspace.set_search_context(query, source_ids)

    def set_current_report(self, report_id: str) -> None:
        self.workspace.set_current_analysis(report_id)

    def find_search_result(self, result_id: str) -> SearchResult | None:
        for result in self._search_results:
            if result.result_id == result_id:
                return result
        return None

    def source_rows(self) -> list[dict[str, Any]]:
        counts: dict[str, int] = {}
        for result in self._search_results:
            counts[result.source_id] = counts.get(result.source_id, 0) + 1
        sources = self.search_service.source_list()
        return [
            {
                "source_id": row["source_id"],
                "label": row["label"],
                "result_count": counts.get(row["source_id"], 0),
                "available_count": len(sources),
                "summary": f"{counts.get(row['source_id'], 0)} 条结果",
            }
            for row in sources
        ]

    def all_documents(self) -> list[DocumentDescriptor]:
        return self.workspace.list_documents()

    def filtered_documents(self) -> list[DocumentDescriptor]:
        documents = list(self.all_documents())
        if self.library_filters.recent_only:
            recent_ids = set(self.workspace.state.recent_opened_ids[:12])
            documents = [document for document in documents if document.document_id in recent_ids]
        if self.library_filters.group_id != "all":
            documents = [document for document in documents if document.group_id == self.library_filters.group_id]
        if self.library_filters.kind != "all":
            documents = [document for document in documents if document.kind == self.library_filters.kind]
        query = self.library_filters.query.strip().lower()
        if query:
            filtered: list[DocumentDescriptor] = []
            for document in documents:
                haystacks = [
                    document.title,
                    " ".join(document.authors),
                    document.excerpt,
                    document.source,
                    " ".join(document.tags),
                    " ".join(document.keywords),
                ]
                if any(query in (field or "").lower() for field in haystacks):
                    filtered.append(document)
            documents = filtered
        return documents

    def _source_label_map(self) -> dict[str, str]:
        return {row["source_id"]: row["label"] for row in self.search_service.source_list()}

    def _group_map(self) -> dict[str, Any]:
        return {group.group_id: group for group in self.workspace.state.groups}

    def _doc_row(self, document: DocumentDescriptor) -> dict[str, Any]:
        annotation_count = self.annotation_store.count_for_document(document.document_id)
        group = self._group_map().get(document.group_id)
        links = self.workspace.links_for_artifact("document", document.document_id)
        related_reports = len([link for link in links if link.source_kind == "analysis_report" or link.target_kind == "analysis_report"])
        related_latex = len([link for link in links if link.source_kind == "latex_session" or link.target_kind == "latex_session"])
        metadata_parts = []
        source_label = self._source_label_map().get(document.source, document.source)
        if source_label:
            metadata_parts.append(source_label)
        if document.metadata.get("doi"):
            metadata_parts.append(f"DOI {document.metadata['doi']}")
        if document.metadata.get("page_count"):
            metadata_parts.append(f"{document.metadata['page_count']} 页")
        if document.year:
            metadata_parts.append(str(document.year))
        if annotation_count:
            metadata_parts.append(f"{annotation_count} 条标注")
        return {
            "document_id": document.document_id,
            "title": document.title,
            "display_title": document.title,
            "path": document.path,
            "kind": document.kind,
            "kind_label": KIND_LABELS.get(document.kind, document.kind.upper()),
            "authors": "，".join(document.authors),
            "author_list": list(document.authors),
            "year": document.year,
            "source": document.source,
            "source_label": source_label,
            "tags": " / ".join(document.tags),
            "group_id": document.group_id,
            "group_color": document.group_color or (group.color if group else "#40607c"),
            "favorite": document.favorite,
            "archived": document.archived,
            "progress": round(document.progress * 100),
            "excerpt": document.excerpt,
            "annotation_count": annotation_count,
            "metadata_summary": "  ·  ".join(metadata_parts),
            "last_opened": document.last_opened or document.added_at,
            "status_line": f"{KIND_LABELS.get(document.kind, document.kind.upper())}  ·  {round(document.progress * 100)}% 已读  ·  分析 {related_reports}  ·  LaTeX {related_latex}",
        }

    def library_rows(self) -> list[dict[str, Any]]:
        rows = sort_records("library", [self._doc_row(document) for document in self.filtered_documents()])
        return self._order_with_native(
            rows,
            native_library_order_ids,
            lambda items: "\n".join(
                f"{row['document_id']}\t{1 if row.get('favorite') else 0}\t{row.get('last_opened', '')}\t{row.get('year', '')}\t{str(row.get('display_title', '')).replace(chr(9), ' ').replace(chr(10), ' ')}"
                for row in items
            ),
        )

    def document_choice_rows(self) -> list[dict[str, Any]]:
        rows = [self._doc_row(document) for document in self.all_documents()]
        rows.sort(key=lambda item: item.get("display_title", "").lower())
        return rows

    def recent_document_rows(self) -> list[dict[str, Any]]:
        return [self._doc_row(document) for document in self.workspace.recent_documents()]

    def recent_writer_rows(self) -> list[dict[str, Any]]:
        return [self._doc_row(document) for document in self.workspace.recent_writers()]

    def recent_search_rows(self) -> list[dict[str, Any]]:
        return [{"label": item} for item in self.workspace.state.recent_searches[:8]]

    def recent_note_rows(self) -> list[dict[str, Any]]:
        rows = []
        for note in self.workspace.state.notes[:6]:
            rows.append(
                {
                    "note_id": note.note_id,
                    "title": note.title,
                    "content": note.content,
                    "created_at": note.created_at,
                    "status_line": note.created_at,
                }
            )
        return rows

    def recent_latex_rows(self) -> list[dict[str, Any]]:
        rows = []
        for session in self.workspace.state.recent_latex_sessions[:6]:
            payload = asdict(session)
            payload["status_line"] = f"{session.template}  ·  {session.compile_status or 'idle'}  ·  {session.updated_at}"
            rows.append(payload)
        return rows

    def analysis_history_rows(self) -> list[dict[str, Any]]:
        rows = sort_records("analysisHistory", [self._report_row(report) for report in self.workspace.state.analyses])
        return self._order_with_native(
            rows,
            native_analysis_order_ids,
            lambda items: "\n".join(
                f"{row['report_id']}\t{row.get('created_at', '')}\t{str(row.get('title', '')).replace(chr(9), ' ').replace(chr(10), ' ')}"
                for row in items
            ),
        )

    def _comparison_items(self, rows: list[dict[str, str]]) -> list[dict[str, str]]:
        normalized: list[dict[str, str]] = []
        for item in rows:
            parts = [f"{key}：{value}" for key, value in item.items() if str(value).strip()]
            if parts:
                normalized.append({"label": next(iter(item.keys()), "比较"), "value": "  ·  ".join(parts)})
        return normalized

    def _report_row(self, report: AnalysisReportState) -> dict[str, Any]:
        links = self.workspace.links_for_artifact("analysis_report", report.report_id)
        draft_links = len([link for link in links if link.target_kind == "document"])
        latex_links = len([link for link in links if link.target_kind == "latex_session" or link.source_kind == "latex_session"])
        field_items = [
            {"label": FIELD_LABELS.get(key, key), "value": value}
            for key, value in report.fields.items()
            if str(value).strip()
        ]
        return {
            "report_id": report.report_id,
            "document_id": report.document_id,
            "title": report.title,
            "created_at": report.created_at,
            "summary": report.summary,
            "contributions": list(report.contributions),
            "experiments": list(report.experiments),
            "method_steps": list(report.method_steps),
            "risks": list(report.risks),
            "comparisons": list(report.comparisons),
            "comparison_items": self._comparison_items(report.comparisons),
            "reading_note": report.reading_note,
            "latex_snippet": report.latex_snippet,
            "field_items": field_items,
            "field_count": len(field_items),
            "experiment_count": len(report.experiments),
            "comparison_count": len(report.comparisons),
            "status_line": f"{len(field_items)} 个补充字段  ·  {len(report.experiments)} 组实验  ·  草稿 {draft_links}  ·  LaTeX {latex_links}",
        }

    def current_analysis_row(self) -> dict[str, Any]:
        reports = {report.report_id: report for report in self.workspace.state.analyses}
        target_id = self.workspace.state.workflow.current_analysis_id
        if target_id not in reports and self.workspace.state.analyses:
            target_id = self.workspace.state.analyses[0].report_id
        report = reports.get(target_id)
        return self._report_row(report) if report else {}

    def plugin_rows(self) -> list[dict[str, Any]]:
        rows = []
        for manifest in self.plugin_manager.manifests():
            runtime = self.workspace.plugin_state_for(manifest.plugin_id)
            enabled = self.plugin_manager.is_enabled(manifest.plugin_id)
            rows.append(
                {
                    "plugin_id": manifest.plugin_id,
                    "name": manifest.name,
                    "version": manifest.version,
                    "author": manifest.author,
                    "description": manifest.description,
                    "builtin": manifest.builtin,
                    "plugin_enabled": enabled,
                    "default_enabled": manifest.default_enabled,
                    "capabilities": " / ".join(manifest.capabilities),
                    "capability_list": list(manifest.capabilities),
                    "load_error": runtime.load_error if runtime else "",
                    "state_label": "已启用" if enabled else "未启用",
                }
            )
        return sort_records("plugin", rows)

    def group_rows(self) -> list[dict[str, Any]]:
        counts = {group.group_id: 0 for group in self.workspace.state.groups}
        for document in self.all_documents():
            counts[document.group_id] = counts.get(document.group_id, 0) + 1
        rows = []
        for group in sorted(self.workspace.state.groups, key=lambda item: item.order):
            rows.append(
                {
                    "group_id": group.group_id,
                    "name": group.name,
                    "group_color": group.color,
                    "document_count": counts.get(group.group_id, 0),
                    "summary": f"{counts.get(group.group_id, 0)} 份资料",
                }
            )
        return rows

    def kind_option_rows(self) -> list[dict[str, Any]]:
        counts: dict[str, int] = {}
        for document in self.all_documents():
            counts[document.kind] = counts.get(document.kind, 0) + 1
        options = [{"kind_id": "all", "label": "全部类型", "count": len(self.all_documents())}]
        for kind, count in sorted(counts.items(), key=lambda item: KIND_LABELS.get(item[0], item[0])):
            options.append({"kind_id": kind, "label": KIND_LABELS.get(kind, kind.upper()), "count": count})
        return options

    def provider_rows(self) -> list[dict[str, Any]]:
        rows = []
        for provider in self.workspace.state.providers:
            rows.append(
                {
                    "provider_id": provider.provider_id,
                    "name": provider.name,
                    "base_url": provider.base_url,
                    "api_key": provider.api_key,
                    "default_model": provider.default_model,
                    "analysis_model": provider.analysis_model,
                    "active": provider.active,
                    "state_label": "已启用" if provider.active else "未启用",
                }
            )
        return rows

    def settings_summary_rows(self) -> list[dict[str, Any]]:
        active_provider = self.workspace.active_provider()
        theme_mode = self.workspace.state.ui.theme
        banner_enabled = self.workspace.state.ui.banner_parallax_enabled
        preset_titles = {
            "preset_academic": "浅蓝学术科技风",
            "preset_graph": "深蓝知识图谱风",
            "preset_warm": "暖色纸张书桌风",
            "preset_glass": "极简玻璃空间风",
        }
        return [
            {
                "entry_id": "appearance",
                "title": "界面外观",
                "value": "浅色模式" if theme_mode == "light" else "夜间模式",
                "detail": ("顶部横幅景深已启用" if banner_enabled else "顶部横幅景深已关闭")
                + "  ·  "
                + preset_titles.get(self.workspace.state.ui.banner_preset_id, "默认横幅"),
                "state": theme_mode,
            },
            {
                "entry_id": "provider",
                "title": "主模型接口",
                "value": active_provider.name if active_provider else "未配置",
                "detail": active_provider.default_model if active_provider else "未启用",
                "state": "ready" if active_provider else "empty",
            },
            {
                "entry_id": "plugins",
                "title": "插件运行态",
                "value": f"{len([row for row in self.plugin_rows() if row['plugin_enabled']])} 个已启用",
                "detail": "插件状态",
                "state": "ready",
            },
        ]

    def search_result_rows(self) -> list[dict[str, Any]]:
        labels = self._source_label_map()
        rows = []
        for result in self._search_results:
            venue = result.venue or labels.get(result.source_id, result.source_id)
            rows.append(
                {
                    "result_id": result.result_id,
                    "title": result.title,
                    "authors": "，".join(result.authors) or "作者未标注",
                    "year": result.year or "年份未知",
                    "item_type": result.item_type,
                    "abstract_text": result.abstract or "无摘要",
                    "source_id": result.source_id,
                    "source_label": labels.get(result.source_id, result.source_id),
                    "landing_url": result.landing_url,
                    "pdf_url": result.pdf_url,
                    "venue": result.venue,
                    "doi": result.doi,
                    "has_pdf": bool(result.pdf_url),
                    "meta_summary": "  ·  ".join([part for part in [venue, result.doi and f"DOI {result.doi}"] if part]),
                    "status_line": "可直接加入资料库" if result.pdf_url else "需先打开原页确认",
                }
            )
        rows = sort_records("searchResult", rows)
        return self._order_with_native(
            rows,
            native_search_order_ids,
            lambda items: "\n".join(
                f"{row['result_id']}\t{1 if row.get('has_pdf') else 0}\t{row.get('year', '')}\t{str(row.get('title', '')).replace(chr(9), ' ').replace(chr(10), ' ')}"
                for row in items
            ),
        )

    def home_overview(self) -> dict[str, Any]:
        documents = self.all_documents()
        drafts = [document for document in documents if document.kind == DocumentKind.DRAFT.value]
        analyses = self.workspace.state.analyses
        return {
            "total_documents": len(documents),
            "pdf_documents": len([document for document in documents if document.kind == DocumentKind.PDF.value]),
            "draft_documents": len(drafts),
            "analysis_reports": len(analyses),
            "notes": len(self.workspace.state.notes),
            "plugins": len([entry for entry in self.plugin_rows() if entry["plugin_enabled"]]),
        }

    def home_metric_rows(self) -> list[dict[str, Any]]:
        overview = self.home_overview()
        return [
            {"metric_id": "documents", "label": "资料总量", "value": overview["total_documents"], "detail": "已入库", "tone": "neutral"},
            {"metric_id": "pdf", "label": "PDF", "value": overview["pdf_documents"], "detail": "可阅读", "tone": "neutral"},
            {"metric_id": "drafts", "label": "草稿", "value": overview["draft_documents"], "detail": "可续写", "tone": "accent"},
            {"metric_id": "analyses", "label": "分析", "value": overview["analysis_reports"], "detail": "已生成", "tone": "accent"},
            {"metric_id": "notes", "label": "笔记", "value": overview["notes"], "detail": "已沉淀", "tone": "neutral"},
        ]

    def home_path_rows(self) -> list[dict[str, Any]]:
        recent_search = self.workspace.state.recent_searches[0] if self.workspace.state.recent_searches else "开始检索"
        latest_analysis = self.workspace.state.analyses[0].title if self.workspace.state.analyses else "开始分析"
        latest_writer = self.workspace.recent_writers()[0].title if self.workspace.recent_writers() else "新建草稿"
        latest_latex = self.workspace.state.recent_latex_sessions[0].title if self.workspace.state.recent_latex_sessions else "打开模板"
        return [
            {
                "path_id": "import",
                "title": "资料入库",
                "caption": f"{len(self.all_documents())} 份资料",
                "detail": "导入文档",
                "badge": "资料库",
                "page_id": "library",
                "action_id": "importDocuments",
                "action_label": "导入",
                "mark": "导",
                "tone": "neutral",
            },
            {
                "path_id": "search",
                "title": "论文检索",
                "caption": recent_search,
                "detail": recent_search,
                "badge": "最近检索",
                "page_id": "search",
                "action_id": "gotoSearch",
                "action_label": "进入",
                "mark": "搜",
                "tone": "accent",
            },
            {
                "path_id": "analysis",
                "title": "结构化分析",
                "caption": latest_analysis,
                "detail": latest_analysis,
                "badge": "最新分析",
                "page_id": "analysis",
                "action_id": "gotoAnalysis",
                "action_label": "查看",
                "mark": "析",
                "tone": "accent",
            },
            {
                "path_id": "writer",
                "title": "写作草稿",
                "caption": latest_writer,
                "detail": latest_writer,
                "badge": "最近草稿",
                "page_id": "home",
                "action_id": "createWriterDocument",
                "action_label": "新建",
                "mark": "写",
                "tone": "neutral",
            },
            {
                "path_id": "latex",
                "title": "LaTeX 草案",
                "caption": latest_latex,
                "detail": latest_latex,
                "badge": "最近会话",
                "page_id": "home",
                "action_id": "openLatexWindow",
                "action_label": "打开",
                "mark": "TeX",
                "tone": "neutral",
            },
        ]

    def library_filter_state(self) -> dict[str, Any]:
        return {
            "query": self.library_filters.query,
            "group_id": self.library_filters.group_id,
            "kind": self.library_filters.kind,
            "recent_only": self.library_filters.recent_only,
            "visible_count": len(self.filtered_documents()),
            "total_count": len(self.all_documents()),
        }

    def search_workspace_state(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for row in self.search_result_rows():
            counts[row["source_label"]] = counts.get(row["source_label"], 0) + 1
        latest_year = ""
        for row in self.search_result_rows():
            year = str(row.get("year", "")).strip()
            if year.isdigit():
                latest_year = max(latest_year, year)
        top_source = ""
        if counts:
            top_source = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
        workflow = self.workspace.state.workflow
        return {
            "query": workflow.current_search_query,
            "result_count": len(self._search_results),
            "source_count": len([count for count in counts.values() if count > 0]),
            "pdf_count": len([result for result in self._search_results if result.pdf_url]),
            "top_source": top_source,
            "latest_year": latest_year,
            "selected_sources": list(workflow.current_search_sources),
        }

    def analysis_workspace_state(self) -> dict[str, Any]:
        current = self.current_analysis_row()
        return {
            "history_count": len(self.workspace.state.analyses),
            "current_title": current.get("title", ""),
            "field_count": current.get("field_count", 0),
            "experiment_count": current.get("experiment_count", 0),
            "comparison_count": current.get("comparison_count", 0),
            "has_current": bool(current.get("report_id")),
        }
