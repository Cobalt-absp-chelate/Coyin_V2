from __future__ import annotations

import re
import subprocess
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QProcess, Qt, QTimer
from PySide6.QtGui import QColor, QTextCursor
from PySide6.QtPdf import QPdfDocument
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
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
)

from coyin.core.common import now_iso
from coyin.core.tasks import TaskCenter
from coyin.core.workspace.state import LatexSessionState
from coyin.qt.widgets.latex_highlighter import LatexHighlighter
from coyin.qt.widgets.pdf_view import SyncPdfView
from coyin.qt.widgets.theme import base_stylesheet, palette_for


TEMPLATE_DESCRIPTIONS = {
    "basic": "通用研究记录模板，适合从分析报告或写作草稿继续整理。",
    "ieee": "IEEE 风格论文骨架，适合进入正式投稿排版。",
}


class LatexWindow(QMainWindow):
    def __init__(
        self,
        runtime_dir: Path,
        templates_dir: Path,
        workspace,
        task_center: TaskCenter,
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
        self.theme_mode = theme_mode
        self.open_writer_document = open_writer_document
        self.create_writer_from_latex = create_writer_from_latex
        self.session_state = session_state
        self.current_template_name = (
            session_state.template if session_state else template_name
        )
        self.work_dir = Path(session_state.path) if session_state else runtime_dir / f"session_{uuid4().hex[:8]}"
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.tex_path = self.work_dir / "main.tex"
        self.pdf_path = self.work_dir / "main.pdf"
        self.log_path = self.work_dir / "main.log"
        self.task_id = f"latex_compile::{session_state.session_id if session_state else self.work_dir.name}"
        self.export_task_id = f"export::{session_state.session_id if session_state else self.work_dir.name}"
        self._suspend_save = False

        self.setWindowTitle(session_state.title if session_state else session_title)
        self.resize(1460, 940)

        self.editor = QPlainTextEdit()
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.highlighter = LatexHighlighter(self.editor.document())
        self.editor.textChanged.connect(self._queue_session_update)

        self.preview_document = QPdfDocument(self)
        self.preview_view = SyncPdfView()
        self.preview_view.setDocument(self.preview_document)
        self.preview_view.inverseSyncRequested.connect(self._inverse_sync)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.issue_view = QPlainTextEdit()
        self.issue_view.setReadOnly(True)

        self.editor_frame = QFrame()
        self.editor_frame.setObjectName("PageSheet")
        editor_layout = QVBoxLayout(self.editor_frame)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.addWidget(self.editor)

        self.preview_frame = QFrame()
        self.preview_frame.setObjectName("PageSheet")
        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.addWidget(self.preview_view)

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
        self._refresh_context_labels()
        self.apply_theme(theme_mode)

    def _build_context_header(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("RibbonSurface")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        self.header_title = QLabel(self.windowTitle())
        self.header_title.setStyleSheet("font-size: 15px; font-weight: 600;")
        self.header_context = QLabel("LaTeX 工作区")
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

        self.compile_button = QPushButton("编译")
        self.compile_button.clicked.connect(self.compile)
        self.sync_button = QPushButton("同步到预览")
        self.sync_button.clicked.connect(self._forward_sync)
        self.export_button = QPushButton("导出 PDF")
        self.export_button.clicked.connect(self._export_pdf)
        self.reload_button = QPushButton("重新载入模板")
        self.reload_button.clicked.connect(lambda: self._load_template(self.template_combo.currentText(), force=True))
        self.find_button = QPushButton("查找")
        self.find_button.clicked.connect(self._find_text)
        self.writer_button = QPushButton("打开关联草稿")
        self.writer_button.clicked.connect(self._open_or_create_writer)

        self.chrome_hint = QLabel("模板、编译、日志、导出和写作承接都集中在这一条工作流里。")

        layout.addWidget(QLabel("模板"))
        layout.addWidget(self.template_combo)
        layout.addWidget(self.compile_button)
        layout.addWidget(self.sync_button)
        layout.addWidget(self.export_button)
        layout.addWidget(self.writer_button)
        layout.addWidget(self.find_button)
        layout.addWidget(self.reload_button)
        layout.addStretch(1)
        layout.addWidget(self.chrome_hint)
        return bar

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

    def _load_source_file(self) -> None:
        self._suspend_save = True
        self.editor.setPlainText(self.tex_path.read_text(encoding="utf-8", errors="ignore"))
        self._suspend_save = False

    def _load_template(self, name: str, force: bool = False) -> None:
        template = self.templates_dir / f"{name}.tex"
        if not template.exists():
            return
        self.current_template_name = name
        self.template_description_label.setText(TEMPLATE_DESCRIPTIONS.get(name, "当前模板可用于继续排版与导出。"))
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
        program = "xelatex"
        args = ["-interaction=nonstopmode", "-synctex=1", "-halt-on-error", self.tex_path.name]
        self.process.setWorkingDirectory(str(self.work_dir))
        self.process.start(program, args)

    def _append_stdout(self) -> None:
        self.log_view.appendPlainText(bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="ignore"))

    def _append_stderr(self) -> None:
        self.log_view.appendPlainText(bytes(self.process.readAllStandardError()).decode("utf-8", errors="ignore"))

    def _on_compile_finished(self, exit_code: int, exit_status) -> None:
        _ = exit_status
        self.compile_button.setEnabled(True)
        error_count = self._highlight_errors()
        self.error_label.setText(f"错误 {error_count}")
        if exit_code == 0 and self.pdf_path.exists():
            self.preview_document.load(str(self.pdf_path))
            self.preview_view.set_fit_mode("width")
            self.status_label.setText("编译完成，可继续同步定位或导出 PDF。")
            self.compile_status_label.setText("编译完成，右侧预览已更新。")
            self.task_center.resolve(
                self.task_id,
                summary="编译完成。",
                detail=str(self.pdf_path),
                item_count=max(1, self.preview_document.pageCount()),
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

    def _highlight_errors(self) -> int:
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
        if count == 0 and self.log_view.toPlainText().strip():
            issues.append("日志未定位到明显行号错误，请继续核对输出信息。")
        self.editor.setExtraSelections(selections)
        self.issue_view.setPlainText("\n".join(issues))
        return count

    def _forward_sync(self) -> None:
        if not self.pdf_path.exists():
            return
        self._persist_source()
        line = self.editor.textCursor().blockNumber() + 1
        result = subprocess.run(
            ["synctex", "view", "-i", f"{line}:0:{self.tex_path.name}", "-o", self.pdf_path.name],
            cwd=self.work_dir,
            capture_output=True,
            text=True,
            timeout=15,
        )
        payload = result.stdout + result.stderr
        page_match = re.search(r"Page:(\d+)", payload)
        x_match = re.search(r"x:([0-9.\-]+)", payload)
        y_match = re.search(r"y:([0-9.\-]+)", payload)
        if page_match and x_match and y_match:
            from PySide6.QtCore import QPointF

            page = int(page_match.group(1)) - 1
            point = QPointF(float(x_match.group(1)), float(y_match.group(1)))
            self.preview_view.pageNavigator().jump(page, point, self.preview_view.zoomFactor())
            self.status_label.setText(f"已同步到第 {page + 1} 页附近。")

    def _inverse_sync(self, page: int, x: float, y: float) -> None:
        if not self.pdf_path.exists():
            return
        result = subprocess.run(
            ["synctex", "edit", "-o", f"{page}:{x}:{y}:{self.pdf_path.name}"],
            cwd=self.work_dir,
            capture_output=True,
            text=True,
            timeout=15,
        )
        payload = result.stdout + result.stderr
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
        try:
            Path(path).write_bytes(self.pdf_path.read_bytes())
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
        except Exception as exc:
            self.task_center.fail(
                self.export_task_id,
                summary="PDF 导出失败",
                detail=str(exc),
                meta={"session": self.windowTitle()},
            )
            QMessageBox.warning(self, "导出失败", str(exc))

    def _find_text(self) -> None:
        from PySide6.QtWidgets import QInputDialog

        text, accepted = QInputDialog.getText(self, "查找", "关键词：")
        if accepted and text:
            self.editor.find(text)

    def _refresh_context_labels(self) -> None:
        document = self.workspace.find_document(self.session_state.linked_document_id) if self.session_state else None
        report = self.workspace.find_analysis(self.session_state.linked_report_id) if self.session_state else None
        draft = self.workspace.find_document(self.session_state.linked_draft_id) if self.session_state else None
        self.header_context.setText(
            f"模板：{self.current_template_name}  ·  工作目录：{self.work_dir.name}"
        )
        self.linked_document_label.setText(
            f"来源文档：{document.title}" if document else "未关联来源文档。"
        )
        self.linked_report_label.setText(
            f"关联分析：{report.title}" if report else "未关联分析报告。"
        )
        self.linked_draft_label.setText(
            f"关联草稿：{draft.title}" if draft else "未关联写作草稿。"
        )
        self.writer_button.setText("打开关联草稿" if draft else "转写作草稿")

    def _open_or_create_writer(self) -> None:
        self._persist_source()
        if self.session_state and self.session_state.linked_draft_id and self.open_writer_document:
            self.open_writer_document(self.session_state.linked_draft_id)
            return
        if self.session_state and self.create_writer_from_latex:
            self.create_writer_from_latex(self.session_state.session_id, self.editor.toPlainText())
