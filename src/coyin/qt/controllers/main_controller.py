from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Property, Signal, Slot

from coyin.bootstrap import ServiceHub
from coyin.core.common import now_iso, short_id
from coyin.core.documents.models import DocumentDescriptor
from coyin.core.indexing import WorkspaceIndexCore
from coyin.core.tasks import TaskPhase, TaskSnapshot
from coyin.core.workspace.state import AnalysisReportState, LatexSessionState
from coyin.qt.controllers.main_controller_coordinators import (
    AnalysisCoordinator,
    AssistantCoordinator,
    LibraryCoordinator,
    SearchCoordinator,
    SettingsCoordinator,
    TranslationCoordinator,
    WritingLatexCoordinator,
)
from coyin.qt.controllers.task_runner import TaskRunner
from coyin.qt.models.record_list_model import RecordListModel
from coyin.qt.widgets.latex_window import LatexWindow
from coyin.qt.widgets.markdown_window import MarkdownWindow
from coyin.qt.widgets.reader_window import ReaderWindow
from coyin.qt.widgets.theme import qml_tokens
from coyin.qt.widgets.writer_window import WriterWindow


class MainController(QObject):
    libraryChanged = Signal()
    searchChanged = Signal()
    analysisChanged = Signal()
    pluginsChanged = Signal()
    providerChanged = Signal()
    statusChanged = Signal()
    themeChanged = Signal()
    assistantChanged = Signal()

    def __init__(self, services: ServiceHub):
        super().__init__()
        self.services = services
        self.task_runner = TaskRunner(self.services.scheduler)
        self.task_center = self.services.task_center
        self.index_core = WorkspaceIndexCore(
            workspace=self.services.workspace,
            annotation_store=self.services.annotation_store,
            plugin_manager=self.services.plugin_manager,
            search_service=self.services.search_service,
        )

        self._status = "准备就绪"
        self._search_task = self.task_center.snapshot("search")
        self._analysis_task = self.task_center.snapshot("analysis")
        self._assistant_messages: list[dict[str, str]] = []
        self._reader_windows: list[ReaderWindow] = []
        self._writer_windows: list[WriterWindow] = []
        self._markdown_windows: list[MarkdownWindow] = []
        self._latex_windows: list[LatexWindow] = []
        self.library = LibraryCoordinator(self)
        self.search = SearchCoordinator(self)
        self.analysis = AnalysisCoordinator(self)
        self.writing = WritingLatexCoordinator(self)
        self.settings = SettingsCoordinator(self)
        self.assistant = AssistantCoordinator(self)
        self.translation = TranslationCoordinator(self)

        self._home_path_model = RecordListModel(contract_key="homePath", parent=self)
        self._overview_metric_model = RecordListModel(contract_key="homeMetric", parent=self)
        self._library_model = RecordListModel(contract_key="library", parent=self)
        self._document_choice_model = RecordListModel(contract_key="library", parent=self)
        self._recent_document_model = RecordListModel(contract_key="library", parent=self)
        self._recent_writer_model = RecordListModel(contract_key="library", parent=self)
        self._search_source_model = RecordListModel(contract_key="searchSource", parent=self)
        self._search_result_model = RecordListModel(contract_key="searchResult", parent=self)
        self._analysis_history_model = RecordListModel(contract_key="analysisHistory", parent=self)
        self._plugin_model = RecordListModel(contract_key="plugin", parent=self)
        self._group_model = RecordListModel(contract_key="group", parent=self)
        self._library_kind_model = RecordListModel(contract_key="kindOption", parent=self)
        self._recent_note_model = RecordListModel(contract_key="recentNote", parent=self)
        self._recent_search_model = RecordListModel(contract_key="recentSearch", parent=self)
        self._recent_latex_model = RecordListModel(contract_key="recentLatex", parent=self)
        self._provider_model = RecordListModel(contract_key="provider", parent=self)
        self._settings_summary_model = RecordListModel(contract_key="settingsSummary", parent=self)

        self.services.workspace.state_changed.connect(self._emit_workspace_refresh)
        self.services.workspace.library_changed.connect(self._emit_library_refresh)
        self.services.workspace.analyses_changed.connect(self._emit_analysis_refresh)
        self.services.workspace.settings_changed.connect(self._emit_settings_refresh)
        self.services.workspace.document_opened.connect(self._emit_document_open_refresh)
        self.services.plugin_manager.changed.connect(self._emit_settings_refresh)
        self.task_center.taskChanged.connect(self._on_task_changed)

        for manifest in self.services.plugin_manager.manifests():
            self.services.workspace.ensure_plugin_state(manifest.plugin_id)

        self._refresh_models()

    def _emit_workspace_refresh(self) -> None:
        self._refresh_models()
        self.libraryChanged.emit()
        self.searchChanged.emit()
        self.analysisChanged.emit()
        self.pluginsChanged.emit()
        self.providerChanged.emit()
        self.themeChanged.emit()

    def _emit_library_refresh(self) -> None:
        self._refresh_library_models()
        self.libraryChanged.emit()

    def _emit_analysis_refresh(self) -> None:
        self._refresh_analysis_models()
        self.libraryChanged.emit()
        self.analysisChanged.emit()

    def _emit_settings_refresh(self) -> None:
        self._refresh_settings_models()
        self.libraryChanged.emit()
        self.pluginsChanged.emit()
        self.providerChanged.emit()

    def _emit_document_open_refresh(self, _document_id: str) -> None:
        self._library_model.replace(self.index_core.library_rows())
        self._recent_document_model.replace(self.index_core.recent_document_rows())
        self.libraryChanged.emit()

    def _on_task_changed(self, task_id: str) -> None:
        if task_id == "search":
            self._search_task = self.task_center.snapshot(task_id)
            self.searchChanged.emit()
        elif task_id == "analysis":
            self._analysis_task = self.task_center.snapshot(task_id)
            self.analysisChanged.emit()

    def _track_window(self, window, bucket: list) -> object:
        bucket.append(window)
        window.destroyed.connect(lambda *_args, store=bucket, ref=window: self._forget_window(store, ref))
        return window

    def _forget_window(self, bucket: list, window) -> None:
        try:
            if hasattr(window, "window_id"):
                self.services.scheduler.cancel_consumer(getattr(window, "window_id", ""))
            if window in bucket:
                bucket.remove(window)
        except Exception:
            pass

    def _set_status(self, text: str) -> None:
        self._status = text
        self.statusChanged.emit()

    def request_reader_selection_translation(self, document_id: str, text: str, on_success, on_error) -> None:
        self.translation.request_reader_selection_translation(document_id, text, on_success, on_error)

    def request_reader_document_translation(self, document_id: str, text: str, on_success, on_error) -> None:
        self.translation.request_reader_document_translation(document_id, text, on_success, on_error)

    def _sync_task(self, task_id: str, snapshot: TaskSnapshot) -> None:
        if task_id == "search":
            self._search_task = snapshot
            self.searchChanged.emit()
        elif task_id == "analysis":
            self._analysis_task = snapshot
            self.analysisChanged.emit()

    def _refresh_models(self) -> None:
        self._refresh_library_models()
        self._refresh_search_models()
        self._refresh_analysis_models()
        self._refresh_settings_models()

    def _refresh_library_models(self) -> None:
        self._home_path_model.replace(self.index_core.home_path_rows())
        self._overview_metric_model.replace(self.index_core.home_metric_rows())
        self._library_model.replace(self.index_core.library_rows())
        self._document_choice_model.replace(self.index_core.document_choice_rows())
        self._recent_document_model.replace(self.index_core.recent_document_rows())
        self._recent_writer_model.replace(self.index_core.recent_writer_rows())
        self._group_model.replace(self.index_core.group_rows())
        self._library_kind_model.replace(self.index_core.kind_option_rows())
        self._recent_note_model.replace(self.index_core.recent_note_rows())
        self._recent_search_model.replace(self.index_core.recent_search_rows())
        self._recent_latex_model.replace(self.index_core.recent_latex_rows())

    def _refresh_search_models(self) -> None:
        self._search_source_model.replace(self.index_core.source_rows())
        self._search_result_model.replace(self.index_core.search_result_rows())

    def _refresh_analysis_models(self) -> None:
        self._home_path_model.replace(self.index_core.home_path_rows())
        self._overview_metric_model.replace(self.index_core.home_metric_rows())
        self._library_model.replace(self.index_core.library_rows())
        self._analysis_history_model.replace(self.index_core.analysis_history_rows())

    def _refresh_settings_models(self) -> None:
        self._home_path_model.replace(self.index_core.home_path_rows())
        self._overview_metric_model.replace(self.index_core.home_metric_rows())
        self._plugin_model.replace(self.index_core.plugin_rows())
        self._provider_model.replace(self.index_core.provider_rows())
        self._settings_summary_model.replace(self.index_core.settings_summary_rows())

    def _analysis_state(self, report_id: str) -> AnalysisReportState | None:
        return self.services.workspace.find_analysis(report_id)

    def _draft_context(self, draft_id: str) -> dict[str, str]:
        source_document_id = ""
        source_report_id = ""
        linked_latex_id = ""
        for link in self.services.workspace.links_for_artifact("document", draft_id):
            if link.target_kind == "document" and link.source_kind == "document" and link.target_id == draft_id:
                source_document_id = link.source_id
            if link.target_kind == "document" and link.source_kind == "analysis_report" and link.target_id == draft_id:
                source_report_id = link.source_id
            if link.source_kind == "document" and link.source_id == draft_id and link.target_kind == "latex_session":
                linked_latex_id = link.target_id
        return {
            "source_document_id": source_document_id,
            "source_report_id": source_report_id,
            "linked_latex_id": linked_latex_id,
        }

    def _latex_source_context(self, session: LatexSessionState) -> dict[str, str]:
        return {
            "linked_document_id": session.linked_document_id,
            "linked_report_id": session.linked_report_id,
            "linked_draft_id": session.linked_draft_id,
        }

    def _draft_path(self) -> Path:
        return self.services.paths.drafts / f"{short_id('draft')}.cydraft"

    def _latex_session_path(self) -> Path:
        return self.services.paths.latex_runs / f"session_{short_id('latex')}"

    def _build_document_draft_html(self, descriptor: DocumentDescriptor) -> str:
        return "".join(
            [
                f"<h1>{descriptor.title}</h1>",
                "<p>本草稿由资料库直接发起，用于承接阅读和整理路径。</p>",
                "<h2>研究问题</h2><p></p>",
                "<h2>关键引文</h2><p>[作者, 年份]</p>",
                "<h2>方法与实验观察</h2><p></p>",
                "<h2>写作提纲</h2><p></p>",
            ]
        )

    def _build_analysis_draft_html(self, report: AnalysisReportState) -> str:
        return "".join(
            [
                f"<h1>{report.title}</h1>",
                "<h2>结构化摘要</h2>",
                f"<p>{report.summary}</p>",
                "<h2>贡献点</h2>",
                "<ul>" + "".join(f"<li>{item}</li>" for item in report.contributions) + "</ul>",
                "<h2>方法流程</h2>",
                "<ol>" + "".join(f"<li>{item}</li>" for item in report.method_steps) + "</ol>",
                "<h2>风险与局限</h2>",
                "<ul>" + "".join(f"<li>{item}</li>" for item in report.risks) + "</ul>",
                "<h2>阅读笔记</h2>",
                f"<p>{report.reading_note.replace(chr(10), '<br/>')}</p>",
            ]
        )

    def _build_latex_from_analysis(self, report: AnalysisReportState) -> str:
        template = (self.services.paths.templates / "latex" / "basic.tex").read_text(encoding="utf-8")
        body = (
            "\n\\section{结构化摘要}\n"
            + report.summary
            + "\n\\section{贡献点}\n"
            + "\n".join(f"\\paragraph{{要点}} {item}" for item in report.contributions)
            + "\n\\section{方法流程}\n"
            + "\n".join(f"{index + 1}. {item}\\\\" for index, item in enumerate(report.method_steps))
        )
        if "\\end{document}" in template:
            return template.replace("\\end{document}", body + "\n\\end{document}")
        return template + "\n" + body

    def _build_latex_from_draft(self, descriptor: DocumentDescriptor) -> str:
        template = (self.services.paths.templates / "latex" / "basic.tex").read_text(encoding="utf-8")
        html = Path(descriptor.path).read_text(encoding="utf-8", errors="ignore") if Path(descriptor.path).exists() else ""
        blocks = self.services.exporter.html_to_plain_blocks(html)[:12]
        body = "\n\\section{写作草稿承接}\n" + "\n\n".join(blocks)
        if "\\end{document}" in template:
            return template.replace("\\end{document}", body + "\n\\end{document}")
        return template + "\n" + body

    def _build_draft_from_latex(self, title: str, source_text: str) -> str:
        lines = [line.strip() for line in source_text.splitlines() if line.strip()]
        paragraphs = "".join(f"<p>{line}</p>" for line in lines[:24])
        return f"<h1>{title}</h1><p>由 LaTeX 工作区转入写作草稿。</p>{paragraphs}"

    @Property("QVariantMap", notify=themeChanged)
    def themeTokens(self):
        return qml_tokens(self.themeMode)

    @Property("QVariantMap", constant=True)
    def environmentInfo(self):
        return self.settings.environment_info()

    @Property(QObject, constant=True)
    def homePathModel(self):
        return self._home_path_model

    @Property(QObject, constant=True)
    def overviewMetricModel(self):
        return self._overview_metric_model

    @Property(QObject, constant=True)
    def libraryModel(self):
        return self._library_model

    @Property(QObject, constant=True)
    def documentChoiceModel(self):
        return self._document_choice_model

    @Property(QObject, constant=True)
    def recentDocumentModel(self):
        return self._recent_document_model

    @Property(QObject, constant=True)
    def recentWriterModel(self):
        return self._recent_writer_model

    @Property(QObject, constant=True)
    def searchSourceModel(self):
        return self._search_source_model

    @Property(QObject, constant=True)
    def searchResultModel(self):
        return self._search_result_model

    @Property(QObject, constant=True)
    def analysisHistoryModel(self):
        return self._analysis_history_model

    @Property(QObject, constant=True)
    def pluginModel(self):
        return self._plugin_model

    @Property(QObject, constant=True)
    def groupModel(self):
        return self._group_model

    @Property(QObject, constant=True)
    def libraryKindModel(self):
        return self._library_kind_model

    @Property(QObject, constant=True)
    def recentNoteModel(self):
        return self._recent_note_model

    @Property(QObject, constant=True)
    def recentSearchModel(self):
        return self._recent_search_model

    @Property(QObject, constant=True)
    def recentLatexModel(self):
        return self._recent_latex_model

    @Property(QObject, constant=True)
    def providerModel(self):
        return self._provider_model

    @Property(QObject, constant=True)
    def settingsSummaryModel(self):
        return self._settings_summary_model

    @Property("QVariantMap", notify=libraryChanged)
    def homeOverview(self):
        return self.index_core.home_overview()

    @Property("QVariantMap", notify=libraryChanged)
    def homeWorkspaceState(self):
        overview = self.homeOverview
        return {
            "documents": overview["total_documents"],
            "analyses": overview["analysis_reports"],
            "notes": overview["notes"],
            "plugins": overview["plugins"],
        }

    @Property("QVariantList", notify=libraryChanged)
    def libraryDocuments(self):
        return self.index_core.library_rows()

    @Property("QVariantList", notify=libraryChanged)
    def documentChoices(self):
        return self.index_core.document_choice_rows()

    @Property("QVariantList", notify=libraryChanged)
    def recentDocuments(self):
        return self.index_core.recent_document_rows()

    @Property("QVariantList", notify=libraryChanged)
    def recentWriterDocuments(self):
        return self.index_core.recent_writer_rows()

    @Property("QVariantList", notify=libraryChanged)
    def recentSearches(self):
        return [row["label"] for row in self.index_core.recent_search_rows()]

    @Property("QVariantList", notify=libraryChanged)
    def recentNotes(self):
        return self.index_core.recent_note_rows()

    @Property("QVariantList", notify=libraryChanged)
    def recentLatexSessions(self):
        return self.index_core.recent_latex_rows()

    @Property("QVariantList", notify=analysisChanged)
    def recentAnalyses(self):
        return self.index_core.analysis_history_rows()[:8]

    @Property("QVariantList", notify=libraryChanged)
    def groups(self):
        return self.index_core.group_rows()

    @Property("QVariantList", notify=libraryChanged)
    def libraryKindOptions(self):
        return self.index_core.kind_option_rows()

    @Property("QVariantMap", notify=libraryChanged)
    def libraryFilterState(self):
        return self.index_core.library_filter_state()

    @Property("QVariantList", notify=searchChanged)
    def searchResults(self):
        return self.index_core.search_result_rows()

    @Property("QVariantList", notify=searchChanged)
    def searchSources(self):
        return self.index_core.source_rows()

    @Property("QVariantMap", notify=searchChanged)
    def searchWorkspaceState(self):
        return self.index_core.search_workspace_state()

    @Property(bool, notify=searchChanged)
    def searchLoading(self):
        return self._search_task.phase in {TaskPhase.LOADING.value, TaskPhase.REFRESHING.value}

    @Property(str, notify=searchChanged)
    def searchStatusText(self):
        return self._search_task.summary

    @Property("QVariantMap", notify=searchChanged)
    def searchTaskState(self):
        return self._search_task.to_dict()

    @Property("QVariantList", notify=pluginsChanged)
    def pluginEntries(self):
        return self.index_core.plugin_rows()

    @Property(int, notify=pluginsChanged)
    def activePluginCount(self):
        return len([entry for entry in self.pluginEntries if entry["plugin_enabled"]])

    @Property("QVariantList", notify=providerChanged)
    def providerEntries(self):
        return self.index_core.provider_rows()

    @Property("QVariantMap", notify=analysisChanged)
    def currentAnalysis(self):
        return self.index_core.current_analysis_row()

    @Property("QVariantMap", notify=analysisChanged)
    def analysisWorkspaceState(self):
        return self.index_core.analysis_workspace_state()

    @Property(bool, notify=analysisChanged)
    def analysisLoading(self):
        return self._analysis_task.phase in {TaskPhase.LOADING.value, TaskPhase.REFRESHING.value}

    @Property(str, notify=analysisChanged)
    def analysisStatusText(self):
        return self._analysis_task.summary

    @Property("QVariantMap", notify=analysisChanged)
    def analysisTaskState(self):
        return self._analysis_task.to_dict()

    @Property(str, notify=statusChanged)
    def statusText(self):
        return self._status

    @Property(str, notify=themeChanged)
    def themeMode(self):
        return self.services.workspace.state.ui.theme

    @Property(bool, notify=themeChanged)
    def bannerParallaxEnabled(self):
        return self.services.workspace.state.ui.banner_parallax_enabled

    @Property(str, notify=themeChanged)
    def bannerPresetId(self):
        return self.services.workspace.state.ui.banner_preset_id

    @Property(str, constant=True)
    def bannerAssetRoot(self):
        return str(self.services.paths.banner_assets)

    @Property(str, notify=themeChanged)
    def customBannerBackgroundPath(self):
        return self.services.workspace.state.ui.custom_banner_background_path

    @Property(str, notify=themeChanged)
    def customBannerMidgroundPath(self):
        return self.services.workspace.state.ui.custom_banner_midground_path

    @Property(str, notify=themeChanged)
    def customBannerForegroundPath(self):
        return self.services.workspace.state.ui.custom_banner_foreground_path

    @Property(str, notify=themeChanged)
    def customBannerOverlayPath(self):
        return self.services.workspace.state.ui.custom_banner_overlay_path

    @Property("QVariantList", notify=themeChanged)
    def bannerPresetEntries(self):
        return self.settings.banner_preset_entries()

    @Property("QVariantList", notify=assistantChanged)
    def assistantMessages(self):
        return list(self._assistant_messages)

    @Slot(str)
    def syncCurrentPage(self, page_id: str):
        previous = self.services.workspace.state.workflow.current_page
        if page_id == previous:
            return
        self.services.workspace.set_current_page(page_id)
        if previous == "search" and self.searchLoading:
            self.services.scheduler.cancel("search")
            self._sync_task(
                "search",
                self.task_center.idle(
                    "search",
                    summary="检索已取消。",
                    detail="已离开搜索页，旧检索任务失效。",
                ),
            )
        if previous == "analysis" and self.analysisLoading:
            self.services.scheduler.cancel("analysis")
            self._sync_task(
                "analysis",
                self.task_center.idle(
                    "analysis",
                    summary="分析已取消。",
                    detail="已离开分析页，旧分析任务失效。",
                ),
            )

    @Slot(str)
    def triggerWorkbenchAction(self, action_id: str):
        self.library.trigger_workbench_action(action_id)

    @Slot(str)
    def setLibrarySearchQuery(self, query: str):
        self.library.set_library_search_query(query)

    @Slot(str)
    def setLibraryGroupFilter(self, group_id: str):
        self.library.set_library_group_filter(group_id)

    @Slot(str)
    def setLibraryKindFilter(self, kind: str):
        self.library.set_library_kind_filter(kind)

    @Slot(bool)
    def setLibraryRecentOnly(self, recent_only: bool):
        self.library.set_library_recent_only(recent_only)

    @Slot()
    def clearLibraryFilters(self):
        self.library.clear_library_filters()

    @Slot(str)
    def promptRenameDocument(self, document_id: str):
        self.library.prompt_rename_document(document_id)

    @Slot(str)
    def toggleDocumentFavorite(self, document_id: str):
        self.library.toggle_document_favorite(document_id)

    @Slot()
    def importDocuments(self):
        self.library.import_documents()

    @Slot(str)
    def openDocument(self, document_id: str):
        self.library.open_document(document_id)

    @Slot(str)
    def deleteDocument(self, document_id: str):
        self.library.delete_document(document_id)

    def open_reader_document(self, document_id: str, target: ReaderWindow | None = None):
        self.library.open_reader_document(document_id, target=target)

    def _mark_document_opened(self, descriptor: DocumentDescriptor) -> None:
        descriptor.last_opened = now_iso()
        self.services.workspace.mark_document_opened(descriptor)

    def cancel_reader_document(self, window_id: str, document_id: str, task_id: str = "") -> None:
        self.library.cancel_reader_document(window_id, document_id, task_id=task_id)

    def _new_reader_window(self) -> ReaderWindow:
        return self.library.new_reader_window()

    def _create_draft_descriptor(self, title: str, workflow_label: str = "") -> DocumentDescriptor:
        path = self._draft_path()
        descriptor = self.services.repository.create_draft_descriptor(path, title)
        descriptor.kind = DocumentKind.DRAFT.value
        descriptor.workflow_label = workflow_label
        return descriptor

    @Slot()
    def createWriterDocument(self):
        self.writing.create_writer_document()

    @Slot(str)
    def createDraftFromDocument(self, document_id: str):
        self.writing.create_draft_from_document(document_id)

    @Slot(str)
    def openWriterDocument(self, document_id: str):
        self.writing.open_writer_document(document_id)

    def _create_latex_session_state(
        self,
        title: str,
        template_name: str,
        linked_document_id: str = "",
        linked_report_id: str = "",
        linked_draft_id: str = "",
    ) -> LatexSessionState:
        return LatexSessionState(
            session_id=short_id("latex"),
            title=title,
            template=template_name,
            path=str(self._latex_session_path()),
            updated_at=now_iso(),
            linked_document_id=linked_document_id,
            linked_report_id=linked_report_id,
            linked_draft_id=linked_draft_id,
        )

    @Slot()
    def openLatexWindow(self):
        self.writing.open_latex_window()

    @Slot(str)
    def openLatexSession(self, session_id: str):
        self.writing.open_latex_session(session_id)

    def _open_latex_window(self, session_state: LatexSessionState) -> LatexWindow:
        return self.writing._open_latex_window(session_state)

    @Slot(str)
    def openDraftInLatex(self, document_id: str):
        self.writing.open_draft_in_latex(document_id)

    @Slot(str, str)
    def createDraftFromLatexSession(self, session_id: str, source_text: str):
        self.writing.create_draft_from_latex_session(session_id, source_text)

    @Slot(str, "QVariantList")
    def runSearch(self, query: str, source_ids):
        self.search.run_search(query, source_ids)

    @Slot(str)
    def runRecentSearch(self, query: str):
        self.search.run_recent_search(query)

    @Slot(str)
    def openSearchResultLink(self, result_id: str):
        self.search.open_search_result_link(result_id)

    @Slot(str)
    def downloadSearchResult(self, result_id: str):
        self.search.download_search_result(result_id)

    @Slot(str)
    def addSearchResultToLibrary(self, result_id: str):
        self.search.add_search_result_to_library(result_id)

    @Slot(str)
    def addSearchResultToLibraryAndAnalyze(self, result_id: str):
        self.search.add_search_result_to_library_and_analyze(result_id)

    @Slot(str)
    def analyzeDocument(self, document_id: str):
        self.analysis.analyze_document(document_id)

    @Slot(str)
    def focusAnalysis(self, report_id: str):
        self.analysis.focus_analysis(report_id)

    @Slot(str)
    def saveAnalysisToNote(self, report_id: str):
        self.analysis.save_analysis_to_note(report_id)

    @Slot(str)
    def createDraftFromAnalysis(self, report_id: str):
        self.analysis.create_draft_from_analysis(report_id)

    @Slot(str)
    def openAnalysisLatex(self, report_id: str):
        self.analysis.open_analysis_latex(report_id)

    @Slot(str, bool)
    def setPluginEnabled(self, plugin_id: str, enabled: bool):
        self.settings.set_plugin_enabled(plugin_id, enabled)

    @Slot(str, str, str, str, bool)
    def savePrimaryProvider(self, base_url: str, api_key: str, default_model: str, analysis_model: str, active: bool):
        self.settings.save_primary_provider(base_url, api_key, default_model, analysis_model, active)

    @Slot()
    def testPrimaryProvider(self):
        self.settings.test_primary_provider()

    @Slot()
    def toggleTheme(self):
        self.settings.toggle_theme()

    @Slot(bool)
    def setBannerParallaxEnabled(self, enabled: bool):
        self.settings.set_banner_parallax_enabled(enabled)

    @Slot(str)
    def setBannerPreset(self, preset_id: str):
        self.settings.set_banner_preset(preset_id)

    @Slot(str)
    def chooseCustomBannerLayer(self, layer_name: str):
        self.settings.choose_custom_banner_layer(layer_name)

    @Slot()
    def clearCustomBannerLayers(self):
        self.settings.clear_custom_banner_layers()

    @Slot(str)
    def askAssistant(self, question: str):
        self.assistant.ask(question)

    def _local_help(self, question: str) -> str:
        return self.assistant.local_help(question)
