from __future__ import annotations

import re
import os
import subprocess
from pathlib import Path
import shutil
from uuid import uuid4

from PySide6.QtCore import QProcess, QProcessEnvironment, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QKeySequence, QPixmap, QTextCursor
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QTabWidget,
    QToolButton,
)

from coyin.core.common import now_iso
from coyin.paths import app_root
from coyin.core.tasks import TaskCenter, TaskRequest
from coyin.core.workspace.state import LatexSessionState
from coyin.qt.widgets.auto_scroll import install_auto_hide_scrollbars
from coyin.qt.widgets.iconography import themed_icon
from coyin.qt.widgets.latex_highlighter import LatexHighlighter
from coyin.qt.widgets.quick_pdf_view import QuickPdfView
from coyin.qt.widgets.theme import base_stylesheet, palette_for


TEMPLATE_DESCRIPTIONS = {
    "basic": "通用研究记录模板，适合从分析报告或写作草稿继续整理。",
    "ieee": "IEEE 风格论文骨架，适合进入正式投稿排版。",
}

LATEX_TOOLBAR_META = {
    "latex-compile": ("编译", "编译当前 LaTeX 源文件并刷新 PDF 预览。"),
    "reader-right": ("同步到预览", "把当前光标位置同步到右侧 PDF 预览。"),
    "export-pdf": ("导出 PDF", "将当前编译结果导出为 PDF 文件。"),
    "notes": ("打开关联草稿", "打开已关联的写作草稿，或根据当前内容创建草稿。"),
    "find": ("查找", "在当前 LaTeX 源码中查找关键词。"),
    "more": ("重新载入模板", "按当前模板重新载入源码骨架。"),
    "reader-fit-page": ("适应页面", "切换为整页缩放预览。"),
    "reader-fit-width": ("适应宽度", "切换为按页面宽度缩放预览。"),
    "zoom-out": ("缩小", "降低 PDF 预览缩放比例。"),
    "zoom-in": ("放大", "提高 PDF 预览缩放比例。"),
}


class LatexWindow(QMainWindow):
    def __init__(
        self,
        runtime_dir: Path,
        templates_dir: Path,
        workspace,
        task_center: TaskCenter,
        task_runner=None,
        theme_mode: str = "light",
        session_title: str = "LaTeX",
        template_name: str = "basic",
        session_state: LatexSessionState | None = None,
        open_writer_document=None,
        create_writer_from_latex=None,
    ):
        super().__init__()
        self.runtime_dir = runtime_dir
        self.templates_dir = templates_dir
        self.workspace = workspace
        self.task_center = task_center
        self.task_runner = task_runner
        self.theme_mode = theme_mode
        self.open_writer_document = open_writer_document
        self.create_writer_from_latex = create_writer_from_latex
        self.session_state = session_state
        self.current_template_name = (
            session_state.template if session_state else template_name
        )
        self.preview_fit_mode = "width"
        self.work_dir = Path(session_state.path) if session_state else runtime_dir / f"session_{uuid4().hex[:8]}"
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.tex_path = self.work_dir / "main.tex"
        self.pdf_path = self.work_dir / "main.pdf"
        self.log_path = self.work_dir / "main.log"
        self.task_id = f"latex_compile::{session_state.session_id if session_state else self.work_dir.name}"
        self.export_task_id = f"export::{session_state.session_id if session_state else self.work_dir.name}"
        self._consumer_id = f"latex::{session_state.session_id if session_state else self.work_dir.name}"
        self._suspend_save = False
        self._latex_runtime_root = self._detect_latex_runtime_root()

        self.setWindowTitle(session_state.title if session_state else session_title)
        self.resize(1460, 940)

        self.editor = QPlainTextEdit()
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.highlighter = LatexHighlighter(self.editor.document())
        self.editor.textChanged.connect(self._queue_session_update)

        self.preview_view = QuickPdfView()
        self.preview_view.inverseSyncRequested.connect(self._inverse_sync)
        self.preview_view.stateChanged.connect(self._update_preview_state)
        self.preview_view.documentLoadChanged.connect(self._handle_preview_loaded)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.issue_view = QPlainTextEdit()
        self.issue_view.setReadOnly(True)
        install_auto_hide_scrollbars(self.editor)
        install_auto_hide_scrollbars(self.log_view)
        install_auto_hide_scrollbars(self.issue_view)

        self.editor_frame = QFrame()
        self.editor_frame.setObjectName("PageSheet")
        editor_layout = QVBoxLayout(self.editor_frame)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.addWidget(self.editor)

        self.preview_frame = QFrame()
        self.preview_frame.setObjectName("PageSheet")
        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(0)
        preview_layout.addWidget(self._build_preview_toolbar())
        preview_layout.addWidget(self.preview_view, 1)

        self.inspector_frame = self._build_inspector()

        horizontal = QSplitter(Qt.Orientation.Horizontal)
        horizontal.addWidget(self.editor_frame)
        horizontal.addWidget(self.preview_frame)
        horizontal.addWidget(self.inspector_frame)
        horizontal.setSizes([660, 760, 240])

        log_tabs = QTabWidget()
        log_tabs.addTab(self.log_view, "编译日志")
        log_tabs.addTab(self.issue_view, "问题摘要")
        self.log_frame = QFrame()
        self.log_frame.setObjectName("LogPanel")
        log_layout = QVBoxLayout(self.log_frame)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.addWidget(log_tabs)

        vertical = QSplitter(Qt.Orientation.Vertical)
        vertical.addWidget(horizontal)
        vertical.addWidget(self.log_frame)
        vertical.setSizes([800, 140])

        chrome = QWidget()
        chrome_layout = QVBoxLayout(chrome)
        chrome_layout.setContentsMargins(0, 0, 0, 0)
        chrome_layout.setSpacing(0)
        chrome_layout.addWidget(self._build_context_header())
        chrome_layout.addWidget(self._build_header())
        chrome_layout.addWidget(vertical, 1)
        self.setCentralWidget(chrome)

        status = QStatusBar()
        self.setStatusBar(status)
        self.status_label = QLabel("模板已载入，准备编译。")
        self.error_label = QLabel("错误 0")
        self.path_label = QLabel(str(self.work_dir))
        status.addWidget(self.status_label)
        status.addPermanentWidget(self.path_label)
        status.addPermanentWidget(self.error_label)

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self._append_stdout)
        self.process.readyReadStandardError.connect(self._append_stderr)
        self.process.finished.connect(self._on_compile_finished)

        self.save_timer = QTimer(self)
        self.save_timer.setInterval(700)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self._persist_source)

        self._load_template(self.current_template_name, force=not self.tex_path.exists())
        if self.tex_path.exists():
            self._load_source_file()
        if self.pdf_path.exists():
            self.preview_view.open_pdf(str(self.pdf_path))
            self.preview_view.set_scale_mode("width")
            self.status_label.setText("已载入最近一次编译结果，可继续编辑或重新编译。")
            self.compile_status_label.setText("已载入最近一次编译结果。")
        self._refresh_context_labels()
        self.apply_theme(theme_mode)
        self._build_shortcuts()
        self.preview_view.request_state()

    def _detect_latex_runtime_root(self) -> Path | None:
        root = app_root()
        candidates = [
            root / "latex_runtime" / "MiKTeX",
            root / "MiKTeX",
            Path(r"C:\MikTeX"),
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _latex_bin_dir(self) -> Path | None:
        runtime = self._latex_runtime_root
        if runtime is None:
            return None
        candidates = [
            runtime / "miktex" / "bin" / "x64",
            runtime / "bin" / "x64",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _latex_command_path(self, command_name: str) -> str:
        executable = command_name if command_name.lower().endswith(".exe") else f"{command_name}.exe"
        bin_dir = self._latex_bin_dir()
        if bin_dir is not None:
            candidate = bin_dir / executable
            if candidate.exists():
                return str(candidate)
        resolved = shutil.which(command_name)
        return resolved or command_name

    def _latex_env(self) -> dict[str, str]:
        env = dict(os.environ)
        bin_dir = self._latex_bin_dir()
        if bin_dir is not None:
            env["PATH"] = str(bin_dir) + os.pathsep + env.get("PATH", "")
        return env

    def closeEvent(self, event) -> None:
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
            self.process.waitForFinished(1500)
        if self.task_runner:
            self.task_runner.scheduler.cancel_consumer(self._consumer_id)
        return super().closeEvent(event)

    def _tooltip_html(self, title: str, description: str) -> str:
        return (
            f"<div style='min-width:180px;'>"
            f"<div style='font-weight:700; margin-bottom:4px;'>{title}</div>"
            f"<div style='color:#4c5d70; line-height:1.45;'>{description}</div>"
            "</div>"
        )

    def _icon_meta(self, action_id: str, fallback_title: str = "", fallback_description: str = "") -> tuple[str, str]:
        return LATEX_TOOLBAR_META.get(
            action_id,
            (fallback_title or action_id, fallback_description or "执行该操作。"),
        )

    def _configure_icon_button(
        self,
        button: QToolButton,
        action_id: str,
        *,
        size: int = 18,
        title: str = "",
        description: str = "",
    ) -> None:
        resolved_title, resolved_description = self._icon_meta(action_id, title, description)
        button.setProperty("actionId", action_id)
        button.setAccessibleName(resolved_title)
        button.setToolTip(self._tooltip_html(resolved_title, resolved_description))
        button.setStatusTip(resolved_description)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        button.setAutoRaise(True)
        button.setFixedSize(34, 30)
        button.setText("")
        button.setIcon(themed_icon(action_id, self.theme_mode, size))
        button.setIconSize(QPixmap(size, size).size())

    def _configure_toolbar_button(
        self,
        button: QToolButton,
        action_id: str,
        label: str,
        *,
        size: int = 18,
    ) -> None:
        title, description = self._icon_meta(action_id, label)
        button.setProperty("actionId", action_id)
        button.setAccessibleName(title)
        button.setToolTip(self._tooltip_html(title, description))
        button.setStatusTip(description)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        button.setAutoRaise(False)
        button.setMinimumHeight(34)
        button.setMinimumWidth(76)
        button.setText(label)
        button.setIcon(themed_icon(action_id, self.theme_mode, size))
        button.setIconSize(QPixmap(size, size).size())

    def _build_context_header(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("RibbonSurface")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        self.header_title = QLabel(self.windowTitle())
        self.header_title.setStyleSheet("font-size: 15px; font-weight: 600;")
        self.header_context = QLabel("模板：basic")
        self.header_context.setStyleSheet("font-size: 11px; color: #708195;")
        self.header_status = QLabel("已载入")
        self.header_status.setStyleSheet("font-size: 11px; color: #164e74;")

        titles = QVBoxLayout()
        titles.setSpacing(2)
        titles.addWidget(self.header_title)
        titles.addWidget(self.header_context)

        layout.addLayout(titles)
        layout.addStretch(1)
        layout.addWidget(self.header_status)
        return bar

    def _build_header(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("RibbonSurface")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        self.template_combo = QComboBox()
        self.template_combo.addItems(sorted(path.stem for path in self.templates_dir.glob("*.tex")))
        self.template_combo.setCurrentText(self.current_template_name)
        self.template_combo.currentTextChanged.connect(lambda text: self._load_template(text, force=True))
        self.template_combo.setMinimumWidth(132)

        self.compile_button = QToolButton()
        self._configure_toolbar_button(self.compile_button, "latex-compile", "编译")
        self.compile_button.clicked.connect(self.compile)
        self.sync_button = QToolButton()
        self._configure_toolbar_button(self.sync_button, "reader-right", "同步")
        self.sync_button.clicked.connect(self._forward_sync)
        self.export_button = QToolButton()
        self._configure_toolbar_button(self.export_button, "export-pdf", "导出")
        self.export_button.clicked.connect(self._export_pdf)
        self.reload_button = QToolButton()
        self._configure_toolbar_button(self.reload_button, "more", "重载")
        self.reload_button.clicked.connect(lambda: self._load_template(self.template_combo.currentText(), force=True))
        self.find_button = QToolButton()
        self._configure_toolbar_button(self.find_button, "find", "查找")
        self.find_button.clicked.connect(self._find_text)
        self.writer_button = QToolButton()
        self._configure_toolbar_button(self.writer_button, "notes", "草稿")
        self.writer_button.clicked.connect(self._open_or_create_writer)

        layout.addWidget(QLabel("模板"))
        layout.addWidget(self.template_combo)
        layout.addWidget(self.compile_button)
        layout.addWidget(self.sync_button)
        layout.addWidget(self.export_button)
        layout.addWidget(self.writer_button)
        layout.addWidget(self.find_button)
        layout.addWidget(self.reload_button)
        layout.addStretch(1)
        return bar

    def _build_shortcuts(self) -> None:
        self.find_preview_action = QAction(self)
        self.find_preview_action.setShortcut(QKeySequence.StandardKey.Find)
        self.find_preview_action.triggered.connect(self._focus_preview_search)
        self.addAction(self.find_preview_action)

    def _build_preview_toolbar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("RibbonSurface")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        preview_title = QLabel("PDF 预览")
        preview_title.setStyleSheet("font-size: 13px; font-weight: 600;")

        self.preview_fit_toggle_button = QToolButton()
        self._configure_icon_button(self.preview_fit_toggle_button, "reader-fit-page")
        self.preview_fit_toggle_button.clicked.connect(self._toggle_preview_fit_mode)
        self.preview_page_edit = QLineEdit()
        self.preview_page_edit.setFixedWidth(52)
        self.preview_page_edit.setPlaceholderText("页码")
        self.preview_page_edit.returnPressed.connect(self._jump_preview_page)
        self.preview_page_total_label = QLabel("/ 0")
        self.preview_zoom_out_button = QToolButton()
        self._configure_icon_button(self.preview_zoom_out_button, "zoom-out")
        self.preview_zoom_out_button.clicked.connect(lambda: self._nudge_preview_zoom(-10))
        self.preview_zoom_edit = QLineEdit("100%")
        self.preview_zoom_edit.setFixedWidth(64)
        self.preview_zoom_edit.returnPressed.connect(self._apply_preview_zoom)
        self.preview_zoom_in_button = QToolButton()
        self._configure_icon_button(self.preview_zoom_in_button, "zoom-in")
        self.preview_zoom_in_button.clicked.connect(lambda: self._nudge_preview_zoom(10))
        self.preview_search_edit = QLineEdit()
        self.preview_search_edit.setPlaceholderText("搜索当前文档")
        self.preview_search_edit.returnPressed.connect(self._search_preview)
        self.preview_hint = QLabel("Ctrl+滚轮缩放")
        self.preview_hint.setStyleSheet("font-size: 11px; color: #708195;")
        self._apply_preview_toolbar_icons()

        layout.addWidget(preview_title)
        layout.addSpacing(6)
        layout.addWidget(self.preview_fit_toggle_button)
        layout.addWidget(self.preview_page_edit)
        layout.addWidget(self.preview_page_total_label)
        layout.addSpacing(8)
        layout.addWidget(self.preview_zoom_out_button)
        layout.addWidget(self.preview_zoom_edit)
        layout.addWidget(self.preview_zoom_in_button)
        layout.addSpacing(8)
        layout.addWidget(self.preview_search_edit, 1)
        layout.addWidget(self.preview_hint)
        return bar

    def _apply_button_icon(self, button: QToolButton, action_id: str, size: int = 18) -> None:
        button.setIcon(themed_icon(action_id, self.theme_mode, size))
        button.setIconSize(QPixmap(size, size).size())

    def _apply_header_icons(self) -> None:
        self._apply_button_icon(self.compile_button, "latex-compile")
        self._apply_button_icon(self.sync_button, "reader-right")
        self._apply_button_icon(self.export_button, "export-pdf")
        self._apply_button_icon(self.writer_button, "notes")
        self._apply_button_icon(self.find_button, "find")
        self._apply_button_icon(self.reload_button, "more")

    def _apply_preview_toolbar_icons(self) -> None:
        fit_action = "reader-fit-width" if self.preview_fit_mode == "page" else "reader-fit-page"
        title, description = self._icon_meta(fit_action)
        self.preview_fit_toggle_button.setAccessibleName(title)
        self.preview_fit_toggle_button.setToolTip(self._tooltip_html(title, description))
        self.preview_fit_toggle_button.setStatusTip(description)
        self._apply_button_icon(self.preview_fit_toggle_button, fit_action)
        self._apply_button_icon(self.preview_zoom_out_button, "zoom-out")
        self._apply_button_icon(self.preview_zoom_in_button, "zoom-in")

    def _build_inspector(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("InspectorPanel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        template_box = QFrame()
        template_box.setObjectName("PageSheet")
        template_layout = QVBoxLayout(template_box)
        template_layout.setContentsMargins(12, 12, 12, 12)
        template_layout.setSpacing(8)
        template_layout.addWidget(self._section_title("模板入口"))
        self.template_description_label = QLabel("")
        self.template_description_label.setWordWrap(True)
        template_layout.addWidget(self.template_description_label)
        layout.addWidget(template_box)

        context_box = QFrame()
        context_box.setObjectName("PageSheet")
        context_layout = QVBoxLayout(context_box)
        context_layout.setContentsMargins(12, 12, 12, 12)
        context_layout.setSpacing(8)
        context_layout.addWidget(self._section_title("关联路径"))
        self.linked_document_label = QLabel("未关联来源文档。")
        self.linked_document_label.setWordWrap(True)
        self.linked_report_label = QLabel("未关联分析报告。")
        self.linked_report_label.setWordWrap(True)
        self.linked_draft_label = QLabel("未关联写作草稿。")
        self.linked_draft_label.setWordWrap(True)
        context_layout.addWidget(self.linked_document_label)
        context_layout.addWidget(self.linked_report_label)
        context_layout.addWidget(self.linked_draft_label)
        layout.addWidget(context_box)

        status_box = QFrame()
        status_box.setObjectName("PageSheet")
        status_layout = QVBoxLayout(status_box)
        status_layout.setContentsMargins(12, 12, 12, 12)
        status_layout.setSpacing(8)
        status_layout.addWidget(self._section_title("编译与导出"))
        self.compile_status_label = QLabel("等待编译。")
        self.compile_status_label.setWordWrap(True)
        self.export_status_label = QLabel("尚未导出 PDF。")
        self.export_status_label.setWordWrap(True)
        status_layout.addWidget(self.compile_status_label)
        status_layout.addWidget(self.export_status_label)
        layout.addWidget(status_box)

        layout.addStretch(1)
        return frame

    def _section_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-size: 13px; font-weight: 600; color: #164e74;")
        return label

    def _set_preview_fit_mode(self, mode: str) -> None:
        self.preview_view.set_scale_mode(mode)

    def _toggle_preview_fit_mode(self) -> None:
        self._set_preview_fit_mode("page" if self.preview_fit_mode == "width" else "width")

    def _jump_preview_page(self) -> None:
        text = self.preview_page_edit.text().strip()
        if not text:
            return
        try:
            page = int(text)
        except Exception:
            self.preview_view.request_state()
            return
        self.preview_view.go_to_page(page)

    def _apply_preview_zoom(self) -> None:
        text = self.preview_zoom_edit.text().strip().replace("%", "")
        try:
            percent = int(float(text))
        except Exception:
            self.preview_view.request_state()
            return
        self.preview_view.set_scale_percent(percent)

    def _nudge_preview_zoom(self, delta: int) -> None:
        self.preview_view.set_scale_percent(max(20, min(self.preview_view.zoom_percent() + delta, 400)))

    def _update_preview_state(self, payload: dict) -> None:
        if not hasattr(self, "preview_fit_toggle_button"):
            return
        self.preview_fit_mode = str(payload.get("fitMode", "width"))
        if self.preview_fit_mode not in {"width", "page", "custom"}:
            self.preview_fit_mode = "width"
        page = int(payload.get("page", 0) or 0)
        total = int(payload.get("totalPages", 0) or 0)
        percent = int(payload.get("scalePercent", 100) or 100)
        self.preview_page_edit.setText(str(page) if page else "")
        self.preview_page_total_label.setText(f"/ {total}")
        self.preview_zoom_edit.setText(f"{percent}%")
        self._apply_preview_toolbar_icons()

    def _search_preview(self) -> None:
        self.preview_view.search(self.preview_search_edit.text())

    def _focus_preview_search(self) -> None:
        self.preview_search_edit.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.preview_search_edit.selectAll()

    def apply_theme(self, mode: str) -> None:
        self.theme_mode = mode
        palette = palette_for(mode)
        self.setStyleSheet(base_stylesheet(mode))
        editor_style = (
            f"background: {palette.panel}; border: none; color: {palette.text};"
            f"selection-background-color: {palette.selection};"
        )
        self.editor.setStyleSheet(editor_style)
        self.log_view.setStyleSheet(editor_style)
        self.issue_view.setStyleSheet(editor_style)
        self.preview_view.set_theme(mode)
        self._apply_header_icons()
        self._apply_preview_toolbar_icons()

    def _decode_process_output(self, payload: bytes) -> str:
        if not payload:
            return ""
        for encoding in ("utf-8", "utf-8-sig", "gb18030", "gbk"):
            try:
                return payload.decode(encoding)
            except UnicodeDecodeError:
                continue
        return payload.decode("utf-8", errors="ignore")

    def _run_sync_command(self, args: list[str]) -> str:
        try:
            result = subprocess.run(
                [self._latex_command_path(args[0]), *args[1:]],
                cwd=self.work_dir,
                capture_output=True,
                text=False,
                timeout=15,
                env=self._latex_env(),
            )
        except Exception as exc:
            return str(exc)
        stdout = self._decode_process_output(result.stdout or b"")
        stderr = self._decode_process_output(result.stderr or b"")
        return stdout + stderr

    def _load_source_file(self) -> None:
        self._suspend_save = True
        self.editor.setPlainText(self.tex_path.read_text(encoding="utf-8", errors="ignore"))
        self._suspend_save = False

    def _handle_preview_loaded(self, ok: bool) -> None:
        if ok and self.preview_fit_mode != "custom":
            QTimer.singleShot(0, lambda: self.preview_view.set_scale_mode(self.preview_fit_mode))

    def _load_template(self, name: str, force: bool = False) -> None:
        template = self.templates_dir / f"{name}.tex"
        if not template.exists():
            return
        self.current_template_name = name
        self.template_description_label.setText(TEMPLATE_DESCRIPTIONS.get(name, "当前模板可直接用于排版与导出。"))
        if force:
            self._suspend_save = True
            self.editor.setPlainText(template.read_text(encoding="utf-8"))
            self._suspend_save = False
            self._persist_source()
            self.status_label.setText(f"已载入模板：{name}")

    def _queue_session_update(self) -> None:
        if self._suspend_save:
            return
        self.header_status.setText("源码有更新，准备保存…")
        self.save_timer.start()

    def _persist_source(self) -> None:
        self.tex_path.write_text(self.editor.toPlainText(), encoding="utf-8")
        self.header_status.setText(f"已保存源码 {now_iso()}")
        if self.session_state:
            self.workspace.update_latex_session(self.session_state.session_id, template=self.current_template_name)

    def compile(self) -> None:
        self._persist_source()
        self.log_view.clear()
        self.issue_view.clear()
        self.compile_button.setEnabled(False)
        self.status_label.setText("正在编译…")
        self.compile_status_label.setText("正在编译 LaTeX…")
        self.task_center.begin(
            self.task_id,
            refreshing=self.pdf_path.exists(),
            summary="正在编译 LaTeX…",
            detail=self.windowTitle(),
            meta={"session": self.windowTitle()},
        )
        program = self._latex_command_path("xelatex")
        args = ["-interaction=nonstopmode", "-synctex=1", "-halt-on-error", self.tex_path.name]
        self.process.setWorkingDirectory(str(self.work_dir))
        self.process.setProcessEnvironment(self.processEnvironmentFromSystem())
        self.process.start(program, args)

    def processEnvironmentFromSystem(self):
        process_env = QProcessEnvironment.systemEnvironment()
        for key, value in self._latex_env().items():
            process_env.insert(key, value)
        return process_env

    def _append_stdout(self) -> None:
        self.log_view.appendPlainText(bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="ignore"))

    def _append_stderr(self) -> None:
        self.log_view.appendPlainText(bytes(self.process.readAllStandardError()).decode("utf-8", errors="ignore"))

    def _on_compile_finished(self, exit_code: int, exit_status) -> None:
        _ = exit_status
        self.compile_button.setEnabled(True)
        error_count = self._highlight_errors(include_fallback_notice=exit_code != 0)
        self.error_label.setText(f"错误 {error_count}")
        if exit_code == 0 and self.pdf_path.exists():
            self.preview_view.open_pdf(str(self.pdf_path))
            self.preview_view.set_scale_mode("width")
            self.status_label.setText("编译完成，可继续同步定位或导出 PDF。")
            self.compile_status_label.setText("编译完成，右侧预览已更新。")
            self.task_center.resolve(
                self.task_id,
                summary="编译完成。",
                detail=str(self.pdf_path),
                item_count=1,
                meta={"session": self.windowTitle()},
            )
            if self.session_state:
                self.workspace.update_latex_session(
                    self.session_state.session_id,
                    compile_status="ready",
                    last_error="",
                )
        else:
            self.status_label.setText("编译失败，请查看日志中的错误行。")
            self.compile_status_label.setText("编译失败，请先处理问题摘要中的错误。")
            self.task_center.fail(
                self.task_id,
                summary="编译失败",
                detail=self.issue_view.toPlainText() or "请查看编译日志。",
                meta={"session": self.windowTitle()},
            )
            if self.session_state:
                self.workspace.update_latex_session(
                    self.session_state.session_id,
                    compile_status="error",
                    last_error=self.issue_view.toPlainText()[:500],
                )
            QMessageBox.warning(self, "编译失败", "请查看下方日志并修正错误。")

    def _highlight_errors(self, include_fallback_notice: bool = False) -> int:
        selections = []
        count = 0
        issues: list[str] = []
        for match in re.finditer(r"l\.(\d+)", self.log_view.toPlainText()):
            line_number = int(match.group(1))
            block = self.editor.document().findBlockByLineNumber(line_number - 1)
            if not block.isValid():
                continue
            cursor = QTextCursor(block)
            selection = QPlainTextEdit.ExtraSelection()
            selection.cursor = cursor
            selection.format.setBackground(QColor("#7a2f2f"))
            selection.format.setForeground(QColor("#ffffff"))
            selections.append(selection)
            issues.append(f"第 {line_number} 行附近存在编译错误。")
            count += 1
        if include_fallback_notice and count == 0 and self.log_view.toPlainText().strip():
            issues.append("日志未定位到明显行号错误，请继续核对输出信息。")
        self.editor.setExtraSelections(selections)
        self.issue_view.setPlainText("\n".join(issues))
        return count

    def _forward_sync(self) -> None:
        if not self.pdf_path.exists():
            return
        self._persist_source()
        line = self.editor.textCursor().blockNumber() + 1
        payload = self._run_sync_command(
            ["synctex", "view", "-i", f"{line}:0:{self.tex_path.name}", "-o", self.pdf_path.name]
        )
        page_match = re.search(r"Page:(\d+)", payload)
        x_match = re.search(r"x:([0-9.\-]+)", payload)
        y_match = re.search(r"y:([0-9.\-]+)", payload)
        if page_match and x_match and y_match:
            page = int(page_match.group(1)) - 1
            self.preview_view.go_to_location_index(
                page,
                float(x_match.group(1)),
                float(y_match.group(1)),
                self.preview_view.zoom_percent() / 100.0,
            )
            self.status_label.setText(f"已同步到第 {page + 1} 页附近。")

    def _inverse_sync(self, page: int, x: float, y: float) -> None:
        if not self.pdf_path.exists():
            return
        payload = self._run_sync_command(
            ["synctex", "edit", "-o", f"{page}:{x}:{y}:{self.pdf_path.name}"]
        )
        match = re.search(r"Line:(\d+)", payload)
        if match:
            line = int(match.group(1)) - 1
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor, line)
            self.editor.setTextCursor(cursor)
            self.editor.centerCursor()
            self.status_label.setText(f"已从预览定位回源码第 {line + 1} 行。")

    def _export_pdf(self) -> None:
        if not self.pdf_path.exists():
            QMessageBox.information(self, "尚未生成 PDF", "请先编译。")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "导出 PDF",
            str(self.runtime_dir / "latex_output.pdf"),
            "PDF (*.pdf)",
        )
        if not path:
            return
        self.task_center.begin(
            self.export_task_id,
            summary="正在导出 PDF…",
            detail=path,
            meta={"session": self.windowTitle()},
        )
        target = Path(path)

        def success(_result=None):
            self.status_label.setText("已导出 PDF。")
            self.export_status_label.setText(f"最近导出：{path}")
            self.task_center.resolve(
                self.export_task_id,
                summary="PDF 导出完成。",
                detail=path,
                meta={"session": self.windowTitle()},
            )
            if self.session_state:
                self.workspace.update_latex_session(
                    self.session_state.session_id,
                    last_export_path=path,
                )
            QMessageBox.information(self, "导出完成", "PDF 已导出。")

        def failure(message: str):
            self.task_center.fail(
                self.export_task_id,
                summary="PDF 导出失败",
                detail=message,
                meta={"session": self.windowTitle()},
            )
            QMessageBox.warning(self, "导出失败", message)

        if self.task_runner:
            self.task_runner.submit(
                lambda: target.write_bytes(self.pdf_path.read_bytes()),
                success,
                failure,
                request=TaskRequest(
                    task_id=self.export_task_id,
                    lane="export",
                    priority="background",
                    policy="replace",
                    max_concurrency=1,
                    consumer_id=self._consumer_id,
                ),
            )
        else:
            try:
                target.write_bytes(self.pdf_path.read_bytes())
                success()
            except Exception as exc:
                failure(str(exc))

    def _find_text(self) -> None:
        from PySide6.QtWidgets import QInputDialog

        text, accepted = QInputDialog.getText(self, "查找", "关键词：")
        if accepted and text:
            self.editor.find(text)

    def _refresh_context_labels(self) -> None:
        document = self.workspace.find_document(self.session_state.linked_document_id) if self.session_state else None
        report = self.workspace.find_analysis(self.session_state.linked_report_id) if self.session_state else None
        draft = self.workspace.find_document(self.session_state.linked_draft_id) if self.session_state else None
        self.header_context.setText(f"模板：{self.current_template_name}")
        self.linked_document_label.setText(
            f"来源文档：{document.title}" if document else "未关联来源文档。"
        )
        self.linked_report_label.setText(
            f"关联分析：{report.title}" if report else "未关联分析报告。"
        )
        self.linked_draft_label.setText(
            f"关联草稿：{draft.title}" if draft else "未关联写作草稿。"
        )
        writer_title = "打开关联草稿" if draft else "转写作草稿"
        writer_description = "打开当前 LaTeX 已关联的写作草稿。" if draft else "根据当前 LaTeX 内容创建新的写作草稿。"
        self.writer_button.setAccessibleName(writer_title)
        self.writer_button.setToolTip(self._tooltip_html(writer_title, writer_description))
        self.writer_button.setStatusTip(writer_description)

    def _open_or_create_writer(self) -> None:
        self._persist_source()
        if self.session_state and self.session_state.linked_draft_id and self.open_writer_document:
            self.open_writer_document(self.session_state.linked_draft_id)
            return
        if self.session_state and self.create_writer_from_latex:
            self.create_writer_from_latex(self.session_state.session_id, self.editor.toPlainText())
