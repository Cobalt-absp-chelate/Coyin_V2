from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import shutil
import weakref

import requests
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QInputDialog

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
from coyin.core.tasks import TaskRequest
from coyin.core.workspace.state import AnalysisReportState, ProviderConfig
from coyin.native.bridge import native_available
from coyin.qt.widgets.latex_window import LatexWindow
from coyin.qt.widgets.reader_window import ReaderServices, ReaderWindow
from coyin.qt.widgets.theme import base_stylesheet
from coyin.qt.widgets.writer_window import WriterWindow


class _Coordinator:
    def __init__(self, host):
        self.host = host

    @property
    def services(self):
        return self.host.services


class LibraryCoordinator(_Coordinator):
    def trigger_workbench_action(self, action_id: str) -> None:
        if action_id == "importDocuments":
            self.import_documents()
        elif action_id == "createWriterDocument":
            self.host.writing.create_writer_document()
        elif action_id == "openLatexWindow":
            self.host.writing.open_latex_window()

    def set_library_search_query(self, query: str) -> None:
        self.host.index_core.set_library_query(query)
        self.host._refresh_library_models()
        self.host.libraryChanged.emit()

    def set_library_group_filter(self, group_id: str) -> None:
        self.host.index_core.set_library_group(group_id)
        self.host._refresh_library_models()
        self.host.libraryChanged.emit()

    def set_library_kind_filter(self, kind: str) -> None:
        self.host.index_core.set_library_kind(kind)
        self.host._refresh_library_models()
        self.host.libraryChanged.emit()

    def set_library_recent_only(self, recent_only: bool) -> None:
        self.host.index_core.set_library_recent_only(recent_only)
        self.host._refresh_library_models()
        self.host.libraryChanged.emit()

    def clear_library_filters(self) -> None:
        self.host.index_core.reset_library_filters()
        self.host._refresh_library_models()
        self.host.libraryChanged.emit()

    def prompt_rename_document(self, document_id: str) -> None:
        descriptor = self.services.workspace.find_document(document_id)
        if not descriptor:
            return
        title, accepted = QInputDialog.getText(None, "修改显示名", "标题：", text=descriptor.title)
        if accepted and title.strip():
            self.services.command_bus.execute(
                RenameDocumentCommand(self.services.workspace, document_id, title.strip())
            )
            self.host._set_status("文档显示名已更新。")

    def toggle_document_favorite(self, document_id: str) -> None:
        self.services.command_bus.execute(ToggleDocumentFavoriteCommand(self.services.workspace, document_id))
        self.host._set_status("已更新资料收藏状态。")

    def import_documents(self) -> None:
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
            self.host._set_status(f"已导入 {len(descriptors)} 个文档。")

    def open_document(self, document_id: str) -> None:
        descriptor = self.services.workspace.find_document(document_id)
        if not descriptor:
            return
        if descriptor.kind == DocumentKind.DRAFT.value:
            self.host.writing.open_writer_document(document_id)
            return
        self.open_reader_document(document_id)

    def open_reader_document(self, document_id: str, target: ReaderWindow | None = None) -> None:
        descriptor = self.services.workspace.find_document(document_id)
        if not descriptor:
            self.host._set_status("未找到文档。")
            return
        if target is None:
            if self.host._reader_windows:
                target = self.host._reader_windows[0]
            else:
                target = self.new_reader_window()
        self.host._mark_document_opened(descriptor)
        self.services.workspace.set_current_document(document_id)
        if descriptor.kind == DocumentKind.PDF.value:
            task_id = f"reader::{target.window_id}::{descriptor.document_id}"
            target_ref = weakref.ref(target)
            document_revision = self.services.workspace.state.workflow.document_revision
            target.open_document(descriptor, None, loading=True, task_id=task_id)
            self.host._set_status("PDF 已打开，正在后台整理目录与文本快照…")

            def task(task_token=None):
                return self.services.repository.load_reader_snapshot(descriptor, task_token=task_token)

            def success(snapshot):
                current_target = target_ref()
                if not current_target or descriptor.document_id not in current_target._tab_payloads:
                    return
                payload = current_target._tab_payloads.get(descriptor.document_id, {})
                if payload.get("task_id") != task_id:
                    return
                workflow = self.services.workspace.state.workflow
                if workflow.current_document_id != descriptor.document_id or workflow.document_revision != document_revision:
                    return
                current_target.apply_document_snapshot(descriptor.document_id, snapshot)
                self.host._set_status(f"已完成《{descriptor.title}》的阅读快照。")

            def failure(message):
                current_target = target_ref()
                workflow = self.services.workspace.state.workflow
                if workflow.current_document_id != descriptor.document_id or workflow.document_revision != document_revision:
                    return
                if current_target and descriptor.document_id in current_target._tab_payloads:
                    payload = current_target._tab_payloads.get(descriptor.document_id, {})
                    if payload.get("task_id") == task_id:
                        current_target.mark_document_load_failed(descriptor.document_id, message)
                self.host._set_status(f"PDF 阅读快照加载失败：{message}")

            self.host.task_runner.submit(
                task,
                success,
                failure,
                request=TaskRequest(
                    task_id=task_id,
                    lane="pdf-reader",
                    priority="low-latency",
                    policy="replace",
                    max_concurrency=1,
                    cancellable=True,
                    consumer_id=target.window_id,
                ),
            )
        else:
            snapshot = self.services.repository.load_snapshot(descriptor)
            target.open_document(descriptor, snapshot)
        target.show()
        target.raise_()
        target.activateWindow()

    def cancel_reader_document(self, window_id: str, document_id: str, task_id: str = "") -> None:
        self.services.workspace.clear_current_document(document_id)
        if task_id:
            self.services.scheduler.cancel(task_id)
            return
        self.services.scheduler.cancel(f"reader::{window_id}::{document_id}")

    def new_reader_window(self) -> ReaderWindow:
        window = ReaderWindow(
            ReaderServices(
                annotation_store=self.services.annotation_store,
                command_bus=self.services.command_bus,
                workspace=self.services.workspace,
                render_coordinator=self.services.render_coordinator,
                window_registry=self.services.window_registry,
                open_reader_document=self.open_reader_document,
                cancel_reader_document=self.cancel_reader_document,
                translate_selection=self.host.translation.request_reader_selection_translation,
                translate_document=self.host.translation.request_reader_document_translation,
            ),
            theme_mode=self.host.themeMode,
        )
        window.requestedDetach.connect(
            lambda document_id: self.open_reader_document(document_id, target=self.new_reader_window())
        )
        return self.host._track_window(window, self.host._reader_windows)


class WritingLatexCoordinator(_Coordinator):
    def create_writer_document(self) -> None:
        title = f"文档 {len([doc for doc in self.services.workspace.state.documents if doc.kind == DocumentKind.DRAFT.value]) + 1}"
        descriptor = self.host._create_draft_descriptor(title, workflow_label="空白草稿")
        command = CreateDraftDocumentCommand(
            workspace=self.services.workspace,
            descriptor=descriptor,
            html="<h1>新建文档</h1><p></p>",
            text="创建空白写作草稿",
        )
        self.services.command_bus.execute(command)
        self.open_writer_document(descriptor.document_id)

    def create_draft_from_document(self, document_id: str) -> None:
        descriptor = self.services.workspace.find_document(document_id)
        if not descriptor:
            return
        draft = self.host._create_draft_descriptor(f"{descriptor.title} 写作草稿", workflow_label="资料承接草稿")
        command = CreateDraftDocumentCommand(
            workspace=self.services.workspace,
            descriptor=draft,
            html=self.host._build_document_draft_html(descriptor),
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
        self.open_writer_document(draft.document_id)
        self.host._set_status("已从资料创建写作草稿。")

    def open_writer_document(self, document_id: str) -> None:
        descriptor = self.services.workspace.find_document(document_id)
        if not descriptor:
            return
        self.services.workspace.set_current_draft(document_id)
        window = WriterWindow(
            descriptor=descriptor,
            exporter=self.services.exporter,
            runtime_dir=self.services.paths.exports,
            plugin_manager=self.services.plugin_manager,
            workspace=self.services.workspace,
            command_bus=self.services.command_bus,
            task_center=self.host.task_center,
            task_runner=self.host.task_runner,
            launch_linked_latex=self.open_draft_in_latex,
            theme_mode=self.host.themeMode,
        )
        self.host._track_window(window, self.host._writer_windows)
        window.show()
        self.services.workspace.register_recent_writer(document_id)

    def open_latex_window(self) -> None:
        session = self.host._create_latex_session_state("研究笔记", "basic")
        command = CreateLatexSessionCommand(
            workspace=self.services.workspace,
            session=session,
            initial_text=(self.services.paths.templates / "latex" / "basic.tex").read_text(encoding="utf-8"),
            text="创建 LaTeX 工作区",
        )
        self.services.command_bus.execute(command)
        self._open_latex_window(session_state=command.session)

    def open_latex_session(self, session_id: str) -> None:
        session = self.services.workspace.find_latex_session(session_id)
        if not session:
            self.host._set_status("未找到 LaTeX 会话。")
            return
        self._open_latex_window(session)
        self.host._set_status("已打开 LaTeX 会话。")

    def _open_latex_window(self, session_state) -> LatexWindow:
        self.services.workspace.set_current_latex_session(session_state.session_id)
        window = LatexWindow(
            runtime_dir=self.services.paths.latex_runs,
            templates_dir=self.services.paths.templates / "latex",
            workspace=self.services.workspace,
            task_center=self.host.task_center,
            task_runner=self.host.task_runner,
            theme_mode=self.host.themeMode,
            session_title=session_state.title,
            template_name=session_state.template,
            session_state=session_state,
            open_writer_document=self.open_writer_document,
            create_writer_from_latex=self.create_draft_from_latex_session,
        )
        self.host._track_window(window, self.host._latex_windows)
        window.show()
        return window

    def open_draft_in_latex(self, document_id: str) -> None:
        draft = self.services.workspace.find_document(document_id)
        if not draft:
            return
        context = self.host._draft_context(document_id)
        if context["linked_latex_id"]:
            existing = self.services.workspace.find_latex_session(context["linked_latex_id"])
            if existing:
                self._open_latex_window(existing)
                return
        session = self.host._create_latex_session_state(
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
            initial_text=self.host._build_latex_from_draft(draft),
            link_specs=link_specs,
            text="从写作草稿创建 LaTeX 草稿",
        )
        self.services.command_bus.execute(command)
        self._open_latex_window(command.session)
        self.host._set_status("已从写作草稿打开 LaTeX 工作区。")

    def create_draft_from_latex_session(self, session_id: str, source_text: str) -> None:
        session = self.services.workspace.find_latex_session(session_id)
        if not session:
            return
        if session.linked_draft_id:
            self.open_writer_document(session.linked_draft_id)
            return
        draft = self.host._create_draft_descriptor(f"{session.title} 写作草稿", workflow_label="LaTeX 转写作")
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
            html=self.host._build_draft_from_latex(session.title, source_text),
            link_specs=link_specs,
            text="从 LaTeX 创建写作草稿",
        )
        self.services.command_bus.execute(command)
        self.services.workspace.update_latex_session(session.session_id, linked_draft_id=draft.document_id)
        self.open_writer_document(draft.document_id)
        self.host._set_status("已从 LaTeX 工作区生成写作草稿。")


class SearchCoordinator(_Coordinator):
    def run_search(self, query: str, source_ids) -> None:
        query = query.strip()
        if not query:
            return
        selected = [str(item) for item in source_ids] or [source["source_id"] for source in self.host.searchSources]
        self.services.workspace.set_search_context(query, selected)
        checkpoint = self.services.workspace.search_checkpoint()
        self.services.workspace.add_recent_search(query)
        self.host._set_status("正在检索论文来源…")
        self.host._sync_task(
            "search",
            self.host.task_center.begin(
                "search",
                refreshing=bool(self.host.index_core.search_result_rows()),
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
            if not self.services.workspace.accepts_checkpoint(checkpoint):
                return
            self.host.index_core.set_search_context(results, query=query, source_ids=selected)
            self.host._set_status(f"已返回 {len(results)} 条结果。")
            if results:
                snapshot = self.host.task_center.resolve(
                    "search",
                    summary=f"已整理 {len(results)} 条结果。",
                    detail="结果列表已经同步到搜索中心与资料流转路径。",
                    item_count=len(results),
                    meta={"query": query, "sources": selected},
                )
            else:
                snapshot = self.host.task_center.empty(
                    "search",
                    summary="未找到匹配结果。",
                    detail="可以尝试更换关键词、来源组合或缩短查询文本。",
                    item_count=0,
                    meta={"query": query, "sources": selected},
                )
            self.host._refresh_search_models()
            self.host._sync_task("search", snapshot)
            self.host.searchChanged.emit()

        def failure(message):
            if not self.services.workspace.accepts_checkpoint(checkpoint):
                return
            self.host._set_status(f"检索失败：{message}")
            self.host._sync_task(
                "search",
                self.host.task_center.fail(
                    "search",
                    summary="检索失败",
                    detail=message,
                    meta={"query": query, "sources": selected},
                ),
            )

        self.host.task_runner.submit(
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

    def run_recent_search(self, query: str) -> None:
        sources = [source["source_id"] for source in self.host.searchSources]
        self.run_search(query, sources)

    def open_search_result_link(self, result_id: str) -> None:
        result = self.find_result(result_id)
        if result and result.landing_url:
            QDesktopServices.openUrl(QUrl(result.landing_url))

    def download_search_result(self, result_id: str) -> None:
        result = self.find_result(result_id)
        if not result:
            return
        self.host._set_status("正在下载结果文件…")

        def task():
            return self.services.search_service.download(result, self.services.paths.downloads)

        def success(path):
            self.host._set_status(f"下载完成：{Path(path).name}")

        def failure(message):
            self.host._set_status(f"下载失败：{message}")

        self.host.task_runner.submit(
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

    def import_search_result(self, result: SearchResult) -> DocumentDescriptor:
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

    def add_search_result_to_library(self, result_id: str) -> None:
        result = self.find_result(result_id)
        if not result:
            return
        self.host._set_status("正在将检索结果加入资料库…")

        def task():
            return self.import_search_result(result)

        def success(descriptor):
            self.services.command_bus.execute(ImportDocumentsCommand(self.services.workspace, [descriptor]))
            self.host._set_status("已加入资料库。")

        def failure(message):
            self.host._set_status(f"加入资料库失败：{message}")

        self.host.task_runner.submit(
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

    def add_search_result_to_library_and_analyze(self, result_id: str) -> None:
        result = self.find_result(result_id)
        if not result:
            return
        self.host._set_status("正在入库并准备分析…")

        def task():
            return self.import_search_result(result)

        def success(descriptor):
            self.services.command_bus.execute(ImportDocumentsCommand(self.services.workspace, [descriptor]))
            self.host._set_status("已入库，开始结构化分析。")
            self.host.analysis.analyze_document(descriptor.document_id)

        def failure(message):
            self.host._set_status(f"入库并分析失败：{message}")

        self.host.task_runner.submit(
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

    def find_result(self, result_id: str) -> SearchResult | None:
        return self.host.index_core.find_search_result(result_id)


class AnalysisCoordinator(_Coordinator):
    def analyze_document(self, document_id: str) -> None:
        descriptor = self.services.workspace.find_document(document_id)
        if not descriptor:
            return
        provider = self.services.workspace.active_provider()
        checkpoint = self.services.workspace.analysis_checkpoint()
        self.host._set_status("正在生成结构化分析…")
        self.host._sync_task(
            "analysis",
            self.host.task_center.begin(
                "analysis",
                refreshing=bool(self.services.workspace.state.analyses),
                summary="正在生成结构化分析…",
                detail=f"当前文档：{descriptor.title}",
                meta={"document_id": document_id},
            ),
        )

        def task(task_token=None):
            snapshot = self.services.repository.load_snapshot(descriptor, task_token=task_token)
            return self.services.analysis_service.analyze(descriptor, snapshot, provider)

        def success(report: AnalysisReport):
            if not self.services.workspace.accepts_checkpoint(checkpoint):
                return
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
            self.services.workspace.set_current_analysis(report_state.report_id)
            self.host._set_status("分析完成。")
            self.host._refresh_analysis_models()
            self.host._sync_task(
                "analysis",
                self.host.task_center.resolve(
                    "analysis",
                    summary="分析完成。",
                    detail=f"已生成 {descriptor.title} 的结构化报告。",
                    item_count=len(report_state.fields),
                    meta={"document_id": document_id, "report_id": report_state.report_id},
                ),
            )

        def failure(message):
            if not self.services.workspace.accepts_checkpoint(checkpoint):
                return
            self.host._set_status(f"分析失败：{message}")
            self.host._sync_task(
                "analysis",
                self.host.task_center.fail(
                    "analysis",
                    summary="分析失败",
                    detail=message,
                    meta={"document_id": document_id},
                ),
            )

        self.host.task_runner.submit(
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

    def focus_analysis(self, report_id: str) -> None:
        if self.host._analysis_state(report_id):
            self.services.workspace.set_current_analysis(report_id)
            self.host.analysisChanged.emit()

    def save_analysis_to_note(self, report_id: str) -> None:
        report = self.host._analysis_state(report_id)
        if not report:
            return
        self.services.command_bus.execute(SaveAnalysisToNoteCommand(self.services.workspace, report))
        self.host._set_status("已保存到研究笔记。")

    def create_draft_from_analysis(self, report_id: str) -> None:
        report = self.host._analysis_state(report_id)
        if not report:
            return
        draft = self.host._create_draft_descriptor(f"{report.title} 写作草稿", workflow_label="分析承接草稿")
        command = CreateDraftDocumentCommand(
            workspace=self.services.workspace,
            descriptor=draft,
            html=self.host._build_analysis_draft_html(report),
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
        self.host.writing.open_writer_document(draft.document_id)
        self.host._set_status("已从分析结果生成写作草稿。")

    def open_analysis_latex(self, report_id: str) -> None:
        report = self.host._analysis_state(report_id)
        if not report:
            return
        session = self.host._create_latex_session_state(
            title=f"{report.title} LaTeX 草稿",
            template_name="basic",
            linked_document_id=report.document_id,
            linked_report_id=report.report_id,
        )
        command = CreateLatexSessionCommand(
            workspace=self.services.workspace,
            session=session,
            initial_text=self.host._build_latex_from_analysis(report),
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
        self.host.writing._open_latex_window(command.session)
        self.host._set_status("已从分析结果打开 LaTeX 工作区。")


class SettingsCoordinator(_Coordinator):
    def environment_info(self) -> dict[str, object]:
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

    def set_plugin_enabled(self, plugin_id: str, enabled: bool) -> None:
        try:
            self.services.command_bus.execute(TogglePluginCommand(self.services.plugin_manager, plugin_id, enabled))
            self.host._set_status("插件已启用。" if enabled else "插件已停用。")
        except Exception as exc:
            self.host._set_status(f"插件切换失败：{exc}")
        self.host.pluginsChanged.emit()

    def save_primary_provider(
        self,
        base_url: str,
        api_key: str,
        default_model: str,
        analysis_model: str,
        active: bool,
    ) -> None:
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
        self.host._set_status("模型配置已保存。")

    def test_primary_provider(self) -> None:
        provider = self.services.workspace.state.providers[0]
        if not provider.api_key or not provider.base_url:
            self.host._set_status("请先填写 API 配置。")
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
            self.host._set_status(f"连通性正常，可见模型数：{len(models)}")

        def failure(message):
            self.host._set_status(f"连通性测试失败：{message}")

        self.host.task_runner.submit(
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

    def toggle_theme(self) -> None:
        self.services.workspace.state.ui.theme = "dark" if self.host.themeMode == "light" else "light"
        self.services.workspace.persist()
        for window in [*self.host._reader_windows, *self.host._writer_windows, *self.host._latex_windows]:
            try:
                if hasattr(window, "apply_theme"):
                    window.apply_theme(self.host.themeMode)
                else:
                    window.setStyleSheet(base_stylesheet(self.host.themeMode))
            except Exception:
                continue


class AssistantCoordinator(_Coordinator):
    def ask(self, question: str) -> None:
        question = question.strip()
        if not question:
            return
        self.host._assistant_messages.append({"role": "user", "text": question})
        self.host.assistantChanged.emit()
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
                self.host._assistant_messages.append({"role": "assistant", "text": text})
                self.host.assistantChanged.emit()

            def failure(message):
                self.host._assistant_messages.append(
                    {"role": "assistant", "text": f"当前接口不可用，已切换为本地说明。错误：{message}"}
                )
                self.host._assistant_messages.append({"role": "assistant", "text": self.local_help(question)})
                self.host.assistantChanged.emit()

            self.host.task_runner.submit(
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
            self.host._assistant_messages.append({"role": "assistant", "text": self.local_help(question)})
            self.host.assistantChanged.emit()

    def local_help(self, question: str) -> str:
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


class TranslationCoordinator(_Coordinator):
    def translation_chunks(self, text: str, max_chars: int = 2200) -> list[str]:
        normalized = text.replace("\r\n", "\n").strip()
        if not normalized:
            return []
        chunks: list[str] = []
        current = ""
        for block in normalized.split("\n\n"):
            block = block.strip()
            if not block:
                continue
            candidate = block if not current else f"{current}\n\n{block}"
            if len(candidate) <= max_chars:
                current = candidate
                continue
            if current:
                chunks.append(current)
                current = ""
            while len(block) > max_chars:
                chunks.append(block[:max_chars])
                block = block[max_chars:]
            current = block
        if current:
            chunks.append(current)
        return chunks

    def find_document_by_path(self, path: str) -> DocumentDescriptor | None:
        normalized = str(Path(path).resolve())
        for document in self.services.workspace.state.documents:
            try:
                if str(Path(document.path).resolve()) == normalized:
                    return document
            except Exception:
                if document.path == path:
                    return document
        return None

    def translation_output_candidates(self, descriptor: DocumentDescriptor) -> list[Path]:
        source_path = Path(descriptor.path)
        preferred = source_path.with_name(f"{source_path.stem} 翻译.md")
        fallback = self.services.paths.downloads / "translations" / f"{source_path.stem}-translation.md"
        return [preferred, fallback]

    def translation_markdown(self, title: str, source_title: str, translated_text: str) -> str:
        return "\n".join(
            [
                f"# {title}",
                "",
                f"> 来源：{source_title}",
                "",
                translated_text.strip(),
                "",
            ]
        )

    def translate_text(self, text: str, full_document: bool = False) -> str:
        provider = self.services.workspace.active_provider()
        if not provider or not provider.base_url or not provider.api_key:
            raise RuntimeError("请先在设置中启用可用的 API 接口。")
        model = provider.translation_model or provider.default_model
        chunks = self.translation_chunks(text, max_chars=1800 if full_document else 2400)
        if not chunks:
            return ""
        system_prompt = (
            "你是论文阅读翻译助手。请把用户给出的英文科研内容翻译成流畅、准确、简洁的中文。"
            "保留标题层次、编号、公式、专有名词和缩写；不要添加解释性闲聊。"
        )
        translated: list[str] = []
        for index, chunk in enumerate(chunks):
            user_prompt = chunk
            if full_document:
                user_prompt = f"这是论文片段 {index + 1}/{len(chunks)}，请忠实翻译：\n\n{chunk}"
            response = requests.post(
                provider.base_url.rstrip("/") + "/chat/completions",
                headers={"Authorization": f"Bearer {provider.api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.2,
                },
                timeout=90,
            )
            response.raise_for_status()
            translated.append(response.json()["choices"][0]["message"]["content"].strip())
        return "\n\n".join(part for part in translated if part)

    def request_reader_selection_translation(self, document_id: str, text: str, on_success, on_error) -> None:
        text = text.strip()
        if not text:
            on_error("没有可翻译的选中文本。")
            return
        self.host._set_status("正在翻译选中内容…")

        def task():
            return self.translate_text(text, full_document=False)

        def success(result):
            self.host._set_status("选中翻译已完成。")
            on_success(result)

        def failure(message):
            self.host._set_status(f"选中翻译失败：{message}")
            on_error(message)

        self.host.task_runner.submit(
            task,
            success,
            failure,
            request=TaskRequest(
                task_id=f"translate-selection::{document_id}",
                lane="translation",
                priority="background",
                policy="replace",
                max_concurrency=1,
                timeout_ms=120000,
            ),
        )

    def request_reader_document_translation(self, document_id: str, text: str, on_success, on_error) -> None:
        text = text.strip()
        if not text:
            on_error("当前文档没有可翻译的正文内容。")
            return
        descriptor = self.services.workspace.find_document(document_id)
        if not descriptor:
            on_error("未找到当前文档。")
            return
        self.host._set_status("正在翻译全文…")

        def task():
            translated = self.translate_text(text, full_document=True)
            title = f"{descriptor.title} 翻译"
            target = None
            last_error = None
            for candidate in self.translation_output_candidates(descriptor):
                try:
                    candidate.parent.mkdir(parents=True, exist_ok=True)
                    candidate.write_text(
                        self.translation_markdown(title, descriptor.title, translated),
                        encoding="utf-8",
                    )
                    target = candidate
                    break
                except Exception as exc:
                    last_error = exc
                    continue
            if target is None:
                raise RuntimeError(str(last_error) if last_error else "无法写入译文文件。")
            return {
                "translated_text": translated,
                "output_path": str(target),
                "title": title,
            }

        def success(result):
            target_path = str(result.get("output_path", "")).strip()
            translated_text = str(result.get("translated_text", "")).strip()
            title = str(result.get("title", "")).strip() or f"{descriptor.title} 翻译"
            imported = self.find_document_by_path(target_path)
            if imported is None:
                imported = self.services.repository.import_path(Path(target_path))
                if imported is None:
                    on_error("译文文件已生成，但无法导入资料库。")
                    return
                imported.title = title
                imported.group_id = descriptor.group_id
                imported.group_color = descriptor.group_color
                imported.source = descriptor.source
                imported.workflow_label = "全文翻译"
                self.services.workspace.add_documents([imported])
            else:
                imported = DocumentDescriptor(**asdict(imported))
                imported.title = title
                imported.group_id = descriptor.group_id
                imported.group_color = descriptor.group_color
                imported.source = descriptor.source
                imported.excerpt = translated_text[:200]
                imported.last_opened = now_iso()
                self.services.workspace.update_document(imported)
            self.services.workspace.link_artifacts(
                source_kind="document",
                source_id=document_id,
                target_kind="document",
                target_id=imported.document_id,
                relation_kind="document_translation",
                label="全文翻译生成译文",
            )
            self.host._set_status(f"全文翻译已完成，并已加入资料库：{title}")
            on_success(
                {
                    "document_id": imported.document_id,
                    "title": title,
                    "output_path": target_path,
                    "translated_text": translated_text,
                }
            )

        def failure(message):
            self.host._set_status(f"全文翻译失败：{message}")
            on_error(message)

        self.host.task_runner.submit(
            task,
            success,
            failure,
            request=TaskRequest(
                task_id=f"translate-document::{document_id}",
                lane="translation",
                priority="background",
                policy="replace",
                max_concurrency=1,
                timeout_ms=600000,
            ),
        )
