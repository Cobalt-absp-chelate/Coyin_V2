from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import shutil

import requests
from PySide6.QtCore import QObject, Property, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QInputDialog

from coyin.bootstrap import ServiceHub
from coyin.core.analysis.models import AnalysisReport
from coyin.core.commands.analysis_commands import CreateLatexSessionCommand, SaveAnalysisToNoteCommand
from coyin.core.commands.document_commands import (
    CreateDraftDocumentCommand,
    RenameDocumentCommand,
    ToggleDocumentFavoriteCommand,
)
from coyin.core.commands.library_commands import ImportDocumentsCommand
from coyin.core.commands.plugin_commands import TogglePluginCommand
from coyin.core.common import now_iso, short_id
from coyin.core.documents.models import DocumentDescriptor, DocumentKind, SearchResult
from coyin.core.indexing import WorkspaceIndexCore
from coyin.core.tasks import TaskPhase, TaskRequest, TaskSnapshot
from coyin.core.workspace.state import AnalysisReportState, LatexSessionState, ProviderConfig
from coyin.native.bridge import native_available
from coyin.qt.controllers.task_runner import TaskRunner
from coyin.qt.models.record_list_model import RecordListModel
from coyin.qt.widgets.latex_window import LatexWindow
from coyin.qt.widgets.reader_window import ReaderServices, ReaderWindow
from coyin.qt.widgets.theme import base_stylesheet, qml_tokens
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
        self._latex_windows: list[LatexWindow] = []

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
            if window in bucket:
                bucket.remove(window)
        except Exception:
            pass

    def _set_status(self, text: str) -> None:
        self._status = text
        self.statusChanged.emit()

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
        return {
            "workspaceFile": str(self.services.paths.workspace_file),
            "draftsDir": str(self.services.paths.drafts),
            "downloadsDir": str(self.services.paths.downloads),
            "latexDir": str(self.services.paths.latex_runs),
            "pluginsDir": str(self.services.paths.plugins),
            "templateCount": len(list(self.services.paths.templates.glob("latex/*.tex"))),
            "nativeAvailable": native_available(),
            "xelatexAvailable": bool(shutil.which("xelatex")),
        }

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

    @Property("QVariantList", notify=assistantChanged)
    def assistantMessages(self):
        return list(self._assistant_messages)

    @Slot(str)
    def triggerWorkbenchAction(self, action_id: str):
        actions = {
            "importDocuments": self.importDocuments,
            "createWriterDocument": self.createWriterDocument,
            "openLatexWindow": self.openLatexWindow,
        }
        action = actions.get(action_id)
        if action:
            action()

    @Slot(str)
    def setLibrarySearchQuery(self, query: str):
        self.index_core.set_library_query(query)
        self._refresh_models()
        self.libraryChanged.emit()

    @Slot(str)
    def setLibraryGroupFilter(self, group_id: str):
        self.index_core.set_library_group(group_id)
        self._refresh_models()
        self.libraryChanged.emit()

    @Slot(str)
    def setLibraryKindFilter(self, kind: str):
        self.index_core.set_library_kind(kind)
        self._refresh_models()
        self.libraryChanged.emit()

    @Slot(bool)
    def setLibraryRecentOnly(self, recent_only: bool):
        self.index_core.set_library_recent_only(recent_only)
        self._refresh_models()
        self.libraryChanged.emit()

    @Slot()
    def clearLibraryFilters(self):
        self.index_core.reset_library_filters()
        self._refresh_models()
        self.libraryChanged.emit()

    @Slot(str)
    def promptRenameDocument(self, document_id: str):
        descriptor = self.services.workspace.find_document(document_id)
        if not descriptor:
            return
        title, accepted = QInputDialog.getText(None, "修改显示名", "标题：", text=descriptor.title)
        if accepted and title.strip():
            self.services.command_bus.execute(RenameDocumentCommand(self.services.workspace, document_id, title.strip()))
            self._set_status("文档显示名已更新。")

    @Slot(str)
    def toggleDocumentFavorite(self, document_id: str):
        self.services.command_bus.execute(ToggleDocumentFavoriteCommand(self.services.workspace, document_id))
        self._set_status("已更新资料收藏状态。")

    @Slot()
    def importDocuments(self):
        paths, _ = QFileDialog.getOpenFileNames(
            None,
            "导入文档",
            "",
            "Documents (*.pdf *.md *.txt *.docx *.doc *.tex *.cydraft)",
        )
        if not paths:
            return
        descriptors: list[DocumentDescriptor] = []
        for raw in paths:
            path = Path(raw)
            descriptor = self.services.repository.import_path(path)
            if not descriptor:
                continue
            payload = {"descriptor": asdict(descriptor)}
            for hook in self.services.plugin_manager.context.document_import_hooks:
                try:
                    hook(payload)
                except Exception:
                    continue
            descriptor.metadata.update(payload["descriptor"].get("metadata", {}))
            descriptors.append(descriptor)
        if descriptors:
            self.services.command_bus.execute(ImportDocumentsCommand(self.services.workspace, descriptors))
            self._set_status(f"已导入 {len(descriptors)} 个文档。")

    @Slot(str)
    def openDocument(self, document_id: str):
        self.open_reader_document(document_id)

    def open_reader_document(self, document_id: str, target: ReaderWindow | None = None):
        descriptor = self.services.workspace.find_document(document_id)
        if not descriptor:
            self._set_status("未找到文档。")
            return
        if target is None:
            if self._reader_windows:
                target = self._reader_windows[0]
            else:
                target = self._new_reader_window()
        self._mark_document_opened(descriptor)
        if descriptor.kind == DocumentKind.PDF.value:
            target.open_document(descriptor, None, loading=True)
            self._set_status("PDF 已打开，正在后台整理目录与文本快照…")

            def task():
                return self.services.repository.load_reader_snapshot(descriptor)

            def success(snapshot):
                target.apply_document_snapshot(descriptor.document_id, snapshot)
                self._set_status(f"已完成《{descriptor.title}》的阅读快照。")

            def failure(message):
                target.mark_document_load_failed(descriptor.document_id, message)
                self._set_status(f"PDF 阅读快照加载失败：{message}")

            self.task_runner.submit(
                task,
                success,
                failure,
                request=TaskRequest(
                    task_id=f"reader::{descriptor.document_id}",
                    lane="pdf-reader",
                    priority="low-latency",
                    policy="replace",
                    max_concurrency=1,
                    cancellable=True,
                ),
            )
        else:
            snapshot = self.services.repository.load_snapshot(descriptor)
            target.open_document(descriptor, snapshot)
        target.show()
        target.raise_()
        target.activateWindow()
        self.libraryChanged.emit()

    def _mark_document_opened(self, descriptor: DocumentDescriptor) -> None:
        descriptor.last_opened = now_iso()
        self.services.repository.invalidate(descriptor)
        self.services.workspace.mark_document_opened(descriptor)

    def _new_reader_window(self) -> ReaderWindow:
        window = ReaderWindow(
            ReaderServices(
                annotation_store=self.services.annotation_store,
                command_bus=self.services.command_bus,
                workspace=self.services.workspace,
                render_coordinator=self.services.render_coordinator,
                window_registry=self.services.window_registry,
                open_reader_document=self.open_reader_document,
            ),
            theme_mode=self.themeMode,
        )
        window.requestedDetach.connect(
            lambda document_id: self.open_reader_document(document_id, target=self._new_reader_window())
        )
        return self._track_window(window, self._reader_windows)

    def _create_draft_descriptor(self, title: str, workflow_label: str = "") -> DocumentDescriptor:
        path = self._draft_path()
        descriptor = self.services.repository.create_draft_descriptor(path, title)
        descriptor.kind = DocumentKind.DRAFT.value
        descriptor.workflow_label = workflow_label
        return descriptor

    @Slot()
    def createWriterDocument(self):
        title = f"文档 {len([doc for doc in self.services.workspace.state.documents if doc.kind == DocumentKind.DRAFT.value]) + 1}"
        descriptor = self._create_draft_descriptor(title, workflow_label="空白草稿")
        command = CreateDraftDocumentCommand(
            workspace=self.services.workspace,
            descriptor=descriptor,
            html="<h1>新建文档</h1><p></p>",
            text="创建空白写作草稿",
        )
        self.services.command_bus.execute(command)
        self.openWriterDocument(descriptor.document_id)

    @Slot(str)
    def createDraftFromDocument(self, document_id: str):
        descriptor = self.services.workspace.find_document(document_id)
        if not descriptor:
            return
        draft = self._create_draft_descriptor(f"{descriptor.title} 写作草稿", workflow_label="资料承接草稿")
        command = CreateDraftDocumentCommand(
            workspace=self.services.workspace,
            descriptor=draft,
            html=self._build_document_draft_html(descriptor),
            link_specs=[
                {
                    "source_kind": "document",
                    "source_id": descriptor.document_id,
                    "relation_kind": "document_to_draft",
                    "label": "资料承接写作草稿",
                }
            ],
            text="从资料创建写作草稿",
        )
        self.services.command_bus.execute(command)
        self.openWriterDocument(draft.document_id)
        self._set_status("已从资料创建写作草稿。")

    @Slot(str)
    def openWriterDocument(self, document_id: str):
        descriptor = self.services.workspace.find_document(document_id)
        if not descriptor:
            return
        window = WriterWindow(
            descriptor=descriptor,
            exporter=self.services.exporter,
            runtime_dir=self.services.paths.exports,
            plugin_manager=self.services.plugin_manager,
            workspace=self.services.workspace,
            command_bus=self.services.command_bus,
            task_center=self.task_center,
            launch_linked_latex=self.openDraftInLatex,
            theme_mode=self.themeMode,
        )
        self._track_window(window, self._writer_windows)
        window.show()
        self.services.workspace.register_recent_writer(document_id)

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
        session = self._create_latex_session_state("研究笔记", "basic")
        command = CreateLatexSessionCommand(
            workspace=self.services.workspace,
            session=session,
            initial_text=(self.services.paths.templates / "latex" / "basic.tex").read_text(encoding="utf-8"),
            text="创建 LaTeX 工作区",
        )
        self.services.command_bus.execute(command)
        self._open_latex_window(session_state=command.session)

    @Slot(str)
    def openLatexSession(self, session_id: str):
        session = self.services.workspace.find_latex_session(session_id)
        if not session:
            self._set_status("未找到 LaTeX 会话。")
            return
        self._open_latex_window(session)
        self._set_status("已打开 LaTeX 会话。")

    def _open_latex_window(self, session_state: LatexSessionState) -> LatexWindow:
        window = LatexWindow(
            runtime_dir=self.services.paths.latex_runs,
            templates_dir=self.services.paths.templates / "latex",
            workspace=self.services.workspace,
            task_center=self.task_center,
            theme_mode=self.themeMode,
            session_title=session_state.title,
            template_name=session_state.template,
            session_state=session_state,
            open_writer_document=self.openWriterDocument,
            create_writer_from_latex=self.createDraftFromLatexSession,
        )
        self._track_window(window, self._latex_windows)
        window.show()
        return window

    @Slot(str)
    def openDraftInLatex(self, document_id: str):
        draft = self.services.workspace.find_document(document_id)
        if not draft:
            return
        context = self._draft_context(document_id)
        if context["linked_latex_id"]:
            existing = self.services.workspace.find_latex_session(context["linked_latex_id"])
            if existing:
                self._open_latex_window(existing)
                return
        session = self._create_latex_session_state(
            title=f"{draft.title} LaTeX 草稿",
            template_name="basic",
            linked_document_id=context["source_document_id"],
            linked_report_id=context["source_report_id"],
            linked_draft_id=draft.document_id,
        )
        link_specs = [
            {
                "source_kind": "document",
                "source_id": draft.document_id,
                "relation_kind": "draft_to_latex",
                "label": "写作转 LaTeX",
            }
        ]
        if context["source_report_id"]:
            link_specs.append(
                {
                    "source_kind": "analysis_report",
                    "source_id": context["source_report_id"],
                    "relation_kind": "analysis_to_latex",
                    "label": "分析延续到 LaTeX",
                }
            )
        command = CreateLatexSessionCommand(
            workspace=self.services.workspace,
            session=session,
            initial_text=self._build_latex_from_draft(draft),
            link_specs=link_specs,
            text="从写作草稿创建 LaTeX 草稿",
        )
        self.services.command_bus.execute(command)
        self._open_latex_window(command.session)
        self._set_status("已从写作草稿打开 LaTeX 工作区。")

    @Slot(str, str)
    def createDraftFromLatexSession(self, session_id: str, source_text: str):
        session = self.services.workspace.find_latex_session(session_id)
        if not session:
            return
        if session.linked_draft_id:
            self.openWriterDocument(session.linked_draft_id)
            return
        draft = self._create_draft_descriptor(f"{session.title} 写作草稿", workflow_label="LaTeX 转写作")
        link_specs = [
            {
                "source_kind": "latex_session",
                "source_id": session.session_id,
                "relation_kind": "latex_to_draft",
                "label": "LaTeX 转写作草稿",
            }
        ]
        if session.linked_report_id:
            link_specs.append(
                {
                    "source_kind": "analysis_report",
                    "source_id": session.linked_report_id,
                    "relation_kind": "analysis_to_draft",
                    "label": "分析延续写作草稿",
                }
            )
        command = CreateDraftDocumentCommand(
            workspace=self.services.workspace,
            descriptor=draft,
            html=self._build_draft_from_latex(session.title, source_text),
            link_specs=link_specs,
            text="从 LaTeX 创建写作草稿",
        )
        self.services.command_bus.execute(command)
        self.services.workspace.update_latex_session(session.session_id, linked_draft_id=draft.document_id)
        self.openWriterDocument(draft.document_id)
        self._set_status("已从 LaTeX 工作区生成写作草稿。")

    @Slot(str, "QVariantList")
    def runSearch(self, query: str, source_ids):
        query = query.strip()
        if not query:
            return
        selected = [str(item) for item in source_ids] or [source["source_id"] for source in self.searchSources]
        self.services.workspace.add_recent_search(query)
        self._set_status("正在检索论文来源…")
        self._sync_task(
            "search",
            self.task_center.begin(
                "search",
                refreshing=bool(self.index_core.search_result_rows()),
                summary="正在检索论文来源…",
                detail="多来源检索与结果整理正在后台进行。",
                meta={"query": query, "sources": selected},
            ),
        )

        def task():
            results = self.services.search_service.search(query, selected)
            for handler in self.services.plugin_manager.search_postprocessors():
                results = [
                    SearchResult(**item) if isinstance(item, dict) else item
                    for item in handler([asdict(result) for result in results])
                ]
            return results

        def success(results):
            self.index_core.set_search_context(results, query=query, source_ids=selected)
            self._set_status(f"已返回 {len(results)} 条结果。")
            if results:
                snapshot = self.task_center.resolve(
                    "search",
                    summary=f"已整理 {len(results)} 条结果。",
                    detail="结果列表已经同步到搜索中心与资料流转路径。",
                    item_count=len(results),
                    meta={"query": query, "sources": selected},
                )
            else:
                snapshot = self.task_center.empty(
                    "search",
                    summary="未找到匹配结果。",
                    detail="可以尝试更换关键词、来源组合或缩短查询文本。",
                    item_count=0,
                    meta={"query": query, "sources": selected},
                )
            self._refresh_search_models()
            self._sync_task("search", snapshot)
            self.searchChanged.emit()

        def failure(message):
            self._set_status(f"检索失败：{message}")
            self._sync_task(
                "search",
                self.task_center.fail(
                    "search",
                    summary="检索失败",
                    detail=message,
                    meta={"query": query, "sources": selected},
                ),
            )

        self.task_runner.submit(
            task,
            success,
            failure,
            request=TaskRequest(
                task_id="search",
                lane="search",
                priority="low-latency",
                policy="replace",
                max_concurrency=1,
                cancellable=True,
            ),
        )

    @Slot(str)
    def runRecentSearch(self, query: str):
        sources = [source["source_id"] for source in self.searchSources]
        self.runSearch(query, sources)

    @Slot(str)
    def openSearchResultLink(self, result_id: str):
        result = self._find_result(result_id)
        if result and result.landing_url:
            QDesktopServices.openUrl(QUrl(result.landing_url))

    @Slot(str)
    def downloadSearchResult(self, result_id: str):
        result = self._find_result(result_id)
        if not result:
            return
        self._set_status("正在下载结果文件…")

        def task():
            return self.services.search_service.download(result, self.services.paths.downloads)

        def success(path):
            self._set_status(f"下载完成：{Path(path).name}")

        def failure(message):
            self._set_status(f"下载失败：{message}")

        self.task_runner.submit(
            task,
            success,
            failure,
            request=TaskRequest(
                task_id=f"download::{result_id}",
                lane="downloads",
                priority="background",
                policy="replace",
                max_concurrency=2,
            ),
        )

    def _import_search_result(self, result: SearchResult) -> DocumentDescriptor:
        path = self.services.search_service.download(result, self.services.paths.downloads)
        descriptor = self.services.repository.import_path(path)
        if not descriptor:
            raise RuntimeError("下载完成，但当前文件无法入库")
        descriptor.source = result.source_id
        descriptor.year = result.year
        descriptor.authors = result.authors
        if result.doi:
            descriptor.metadata["doi"] = result.doi
        return descriptor

    @Slot(str)
    def addSearchResultToLibrary(self, result_id: str):
        result = self._find_result(result_id)
        if not result:
            return
        self._set_status("正在将检索结果加入资料库…")

        def task():
            return self._import_search_result(result)

        def success(descriptor):
            self.services.command_bus.execute(ImportDocumentsCommand(self.services.workspace, [descriptor]))
            self._set_status("已加入资料库。")

        def failure(message):
            self._set_status(f"加入资料库失败：{message}")

        self.task_runner.submit(
            task,
            success,
            failure,
            request=TaskRequest(
                task_id=f"import::{result_id}",
                lane="downloads",
                priority="background",
                policy="replace",
                max_concurrency=1,
            ),
        )

    @Slot(str)
    def addSearchResultToLibraryAndAnalyze(self, result_id: str):
        result = self._find_result(result_id)
        if not result:
            return
        self._set_status("正在入库并准备分析…")

        def task():
            return self._import_search_result(result)

        def success(descriptor):
            self.services.command_bus.execute(ImportDocumentsCommand(self.services.workspace, [descriptor]))
            self._set_status("已入库，开始结构化分析。")
            self.analyzeDocument(descriptor.document_id)

        def failure(message):
            self._set_status(f"入库并分析失败：{message}")

        self.task_runner.submit(
            task,
            success,
            failure,
            request=TaskRequest(
                task_id=f"import-analyze::{result_id}",
                lane="downloads",
                priority="background",
                policy="replace",
                max_concurrency=1,
            ),
        )

    def _find_result(self, result_id: str) -> SearchResult | None:
        return self.index_core.find_search_result(result_id)

    @Slot(str)
    def analyzeDocument(self, document_id: str):
        descriptor = self.services.workspace.find_document(document_id)
        if not descriptor:
            return
        provider = self.services.workspace.active_provider()
        self._set_status("正在生成结构化分析…")
        self._sync_task(
            "analysis",
            self.task_center.begin(
                "analysis",
                refreshing=bool(self.services.workspace.state.analyses),
                summary="正在生成结构化分析…",
                detail=f"当前文档：{descriptor.title}",
                meta={"document_id": document_id},
            ),
        )

        def task():
            snapshot = self.services.repository.load_snapshot(descriptor)
            return self.services.analysis_service.analyze(descriptor, snapshot, provider)

        def success(report: AnalysisReport):
            report_state = AnalysisReportState(
                report_id=short_id("report"),
                document_id=document_id,
                title=descriptor.title,
                created_at=now_iso(),
                summary=report.summary,
                contributions=report.contributions,
                experiments=report.experiments,
                method_steps=report.method_steps,
                risks=report.risks,
                comparisons=report.comparison_rows,
                reading_note=report.reading_note,
                latex_snippet=report.latex_snippet,
                fields=report.raw_fields,
            )
            self.services.workspace.add_analysis(report_state)
            self.services.workspace.link_artifacts(
                source_kind="document",
                source_id=document_id,
                target_kind="analysis_report",
                target_id=report_state.report_id,
                relation_kind="document_to_analysis",
                label="资料生成结构化分析",
            )
            self.index_core.set_current_report(report_state.report_id)
            self._set_status("分析完成。")
            self._refresh_analysis_models()
            self._sync_task(
                "analysis",
                self.task_center.resolve(
                    "analysis",
                    summary="分析完成。",
                    detail=f"已生成 {descriptor.title} 的结构化报告。",
                    item_count=len(report_state.fields),
                    meta={"document_id": document_id, "report_id": report_state.report_id},
                ),
            )

        def failure(message):
            self._set_status(f"分析失败：{message}")
            self._sync_task(
                "analysis",
                self.task_center.fail(
                    "analysis",
                    summary="分析失败",
                    detail=message,
                    meta={"document_id": document_id},
                ),
            )

        self.task_runner.submit(
            task,
            success,
            failure,
            request=TaskRequest(
                task_id="analysis",
                lane="analysis",
                priority="heavy",
                policy="replace",
                max_concurrency=1,
                cancellable=True,
            ),
        )

    @Slot(str)
    def focusAnalysis(self, report_id: str):
        if self._analysis_state(report_id):
            self.index_core.set_current_report(report_id)
            self.analysisChanged.emit()

    @Slot(str)
    def saveAnalysisToNote(self, report_id: str):
        report = self._analysis_state(report_id)
        if not report:
            return
        self.services.command_bus.execute(SaveAnalysisToNoteCommand(self.services.workspace, report))
        self._set_status("已保存到研究笔记。")

    @Slot(str)
    def createDraftFromAnalysis(self, report_id: str):
        report = self._analysis_state(report_id)
        if not report:
            return
        draft = self._create_draft_descriptor(f"{report.title} 写作草稿", workflow_label="分析承接草稿")
        command = CreateDraftDocumentCommand(
            workspace=self.services.workspace,
            descriptor=draft,
            html=self._build_analysis_draft_html(report),
            link_specs=[
                {
                    "source_kind": "analysis_report",
                    "source_id": report.report_id,
                    "relation_kind": "analysis_to_draft",
                    "label": "分析生成写作草稿",
                },
                {
                    "source_kind": "document",
                    "source_id": report.document_id,
                    "relation_kind": "document_to_draft",
                    "label": "资料承接写作草稿",
                },
            ],
            text="从分析结果创建写作草稿",
        )
        self.services.command_bus.execute(command)
        self.openWriterDocument(draft.document_id)
        self._set_status("已从分析结果生成写作草稿。")

    @Slot(str)
    def openAnalysisLatex(self, report_id: str):
        report = self._analysis_state(report_id)
        if not report:
            return
        session = self._create_latex_session_state(
            title=f"{report.title} LaTeX 草稿",
            template_name="basic",
            linked_document_id=report.document_id,
            linked_report_id=report.report_id,
        )
        command = CreateLatexSessionCommand(
            workspace=self.services.workspace,
            session=session,
            initial_text=self._build_latex_from_analysis(report),
            link_specs=[
                {
                    "source_kind": "analysis_report",
                    "source_id": report.report_id,
                    "relation_kind": "analysis_to_latex",
                    "label": "分析生成 LaTeX 草稿",
                },
                {
                    "source_kind": "document",
                    "source_id": report.document_id,
                    "relation_kind": "document_to_latex",
                    "label": "资料延续到 LaTeX",
                },
            ],
            text="从分析结果创建 LaTeX 草稿",
        )
        self.services.command_bus.execute(command)
        self._open_latex_window(command.session)
        self._set_status("已从分析结果打开 LaTeX 工作区。")

    @Slot(str, bool)
    def setPluginEnabled(self, plugin_id: str, enabled: bool):
        try:
            self.services.command_bus.execute(TogglePluginCommand(self.services.plugin_manager, plugin_id, enabled))
            self._set_status("插件已启用。" if enabled else "插件已停用。")
        except Exception as exc:
            self._set_status(f"插件切换失败：{exc}")
        self.pluginsChanged.emit()

    @Slot(str, str, str, str, bool)
    def savePrimaryProvider(self, base_url: str, api_key: str, default_model: str, analysis_model: str, active: bool):
        current = self.services.workspace.state.providers[0]
        provider = ProviderConfig(
            provider_id=current.provider_id,
            name=current.name,
            base_url=base_url.strip() or current.base_url,
            api_key=api_key.strip(),
            default_model=default_model.strip() or current.default_model,
            analysis_model=analysis_model.strip() or default_model.strip() or current.default_model,
            assistant_model=current.assistant_model,
            translation_model=current.translation_model,
            active=active,
        )
        self.services.workspace.upsert_provider(provider)
        self._set_status("模型配置已保存。")

    @Slot()
    def testPrimaryProvider(self):
        provider = self.services.workspace.state.providers[0]
        if not provider.api_key or not provider.base_url:
            self._set_status("请先填写 API 配置。")
            return

        def task():
            response = requests.get(
                provider.base_url.rstrip("/") + "/models",
                headers={"Authorization": f"Bearer {provider.api_key}"},
                timeout=20,
            )
            response.raise_for_status()
            return response.json()

        def success(payload):
            models = payload.get("data", [])
            self._set_status(f"连通性正常，可见模型数：{len(models)}")

        def failure(message):
            self._set_status(f"连通性测试失败：{message}")

        self.task_runner.submit(
            task,
            success,
            failure,
            request=TaskRequest(
                task_id="provider-test",
                lane="network",
                priority="low-latency",
                policy="replace",
                max_concurrency=1,
                timeout_ms=25000,
            ),
        )

    @Slot()
    def toggleTheme(self):
        self.services.workspace.state.ui.theme = "dark" if self.themeMode == "light" else "light"
        self.services.workspace.persist()
        for window in [*self._reader_windows, *self._writer_windows, *self._latex_windows]:
            try:
                if hasattr(window, "apply_theme"):
                    window.apply_theme(self.themeMode)
                else:
                    window.setStyleSheet(base_stylesheet(self.themeMode))
            except Exception:
                continue

    @Slot(str)
    def askAssistant(self, question: str):
        question = question.strip()
        if not question:
            return
        self._assistant_messages.append({"role": "user", "text": question})
        self.assistantChanged.emit()
        provider = self.services.workspace.active_provider()
        if provider and provider.active and provider.api_key:

            def task():
                response = requests.post(
                    provider.base_url.rstrip("/") + "/chat/completions",
                    headers={"Authorization": f"Bearer {provider.api_key}", "Content-Type": "application/json"},
                    json={
                        "model": provider.assistant_model or provider.default_model,
                        "messages": [
                            {"role": "system", "content": "你是 Coyin 的桌面软件助手，只回答软件功能、使用路径和当前工作流建议。"},
                            {"role": "user", "content": question},
                        ],
                    },
                    timeout=40,
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]

            def success(text):
                self._assistant_messages.append({"role": "assistant", "text": text})
                self.assistantChanged.emit()

            def failure(message):
                self._assistant_messages.append({"role": "assistant", "text": f"当前接口不可用，已切换为本地说明。错误：{message}"})
                self._assistant_messages.append({"role": "assistant", "text": self._local_help(question)})
                self.assistantChanged.emit()

            self.task_runner.submit(
                task,
                success,
                failure,
                request=TaskRequest(
                    task_id="assistant",
                    lane="assistant",
                    priority="background",
                    policy="replace",
                    max_concurrency=1,
                    timeout_ms=45000,
                ),
            )
        else:
            self._assistant_messages.append({"role": "assistant", "text": self._local_help(question)})
            self.assistantChanged.emit()

    def _local_help(self, question: str) -> str:
        lowered = question.lower()
        if "latex" in lowered:
            return "从顶部的 LaTeX 入口打开，也可以从写作草稿直接转入 LaTeX 工作区。"
        if "搜索" in question or "论文" in question:
            return "搜索中心支持直接入库，或一键加入资料库后继续分析。"
        if "分析" in question:
            return "分析工作区可直接转研究笔记、写作草稿和 LaTeX 草案。"
        if "资料库" in question:
            return "资料库支持筛选、重命名、收藏、分析和直接生成写作草稿。"
        return "可继续阅读、搜索、分析、写作或转入 LaTeX。"
