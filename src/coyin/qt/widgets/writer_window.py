from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextListFormat
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFontComboBox,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QSpinBox,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QSplitter,
)

from coyin.core.commands.writer_commands import WriterDocumentStateCommand
from coyin.core.common import now_iso
from coyin.core.documents.models import DocumentDescriptor
from coyin.core.exporters.base import DraftExporter
from coyin.core.tasks import TaskCenter
from coyin.qt.widgets.theme import base_stylesheet, palette_for


class RibbonGroup(QFrame):
    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("RibbonSurface")
        self.setFrameShape(QFrame.Shape.NoFrame)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 6)
        layout.setSpacing(6)
        self.row = QHBoxLayout()
        self.row.setSpacing(6)
        layout.addLayout(self.row)
        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        label.setStyleSheet("font-size: 11px; color: #708195;")
        layout.addWidget(label)


class WriterWindow(QMainWindow):
    def __init__(
        self,
        descriptor: DocumentDescriptor,
        exporter: DraftExporter,
        runtime_dir: Path,
        plugin_manager,
        workspace,
        command_bus,
        task_center: TaskCenter,
        launch_linked_latex=None,
        theme_mode: str = "light",
    ):
        super().__init__()
        self.descriptor = descriptor
        self.exporter = exporter
        self.runtime_dir = runtime_dir
        self.plugin_manager = plugin_manager
        self.workspace = workspace
        self.command_bus = command_bus
        self.task_center = task_center
        self.launch_linked_latex = launch_linked_latex
        self.theme_mode = theme_mode
        self._dirty = False
        self._suspend_autosave = False
        self._last_export_path = ""
        self._export_task_id = f"export::{self.descriptor.document_id}"

        self.setWindowTitle(descriptor.title)
        self.resize(1340, 930)

        self.ribbon_tabs = QTabWidget()
        self.ribbon_tabs.setDocumentMode(True)
        self.ribbon_tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.ribbon_tabs.setMovable(False)

        self.editor = QTextEdit()
        self.editor.setAcceptRichText(True)
        self.editor.setFrameShape(QFrame.Shape.NoFrame)
        self.editor.textChanged.connect(self._queue_autosave)
        self.editor.textChanged.connect(self._update_status)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.setInterval(700)
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.timeout.connect(self._autosave)

        self.page_sheet = QFrame()
        self.page_sheet.setObjectName("PageSheet")
        self.page_sheet.setMinimumWidth(860)
        page_layout = QVBoxLayout(self.page_sheet)
        page_layout.setContentsMargins(56, 46, 56, 56)
        page_layout.addWidget(self.editor)

        page_host = QWidget()
        host_layout = QHBoxLayout(page_host)
        host_layout.setContentsMargins(24, 22, 24, 22)
        host_layout.addStretch(1)
        host_layout.addWidget(self.page_sheet)
        host_layout.addStretch(1)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setWidget(page_host)

        self.inspector = self._build_inspector()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.scroll)
        splitter.addWidget(self.inspector)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([1040, 260])

        shell = QWidget()
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        shell_layout.addWidget(self._build_context_bar())
        shell_layout.addWidget(self.ribbon_tabs)
        shell_layout.addWidget(splitter, 1)
        self.setCentralWidget(shell)

        self._build_ribbon()
        self._build_statusbar()
        self._load_content()
        self._refresh_context_panels()
        self.workspace.register_recent_writer(descriptor.document_id)
        self.apply_theme(theme_mode)

    def _build_context_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("RibbonSurface")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        self.context_title = QLabel("文档工作区")
        self.context_title.setStyleSheet("font-size: 15px; font-weight: 600;")
        self.context_source = QLabel("来源上下文待识别")
        self.context_analysis = QLabel("未关联分析报告")
        self.context_save = QLabel("已加载")

        self.context_source.setStyleSheet("font-size: 11px; color: #708195;")
        self.context_analysis.setStyleSheet("font-size: 11px; color: #708195;")
        self.context_save.setStyleSheet("font-size: 11px; color: #164e74;")

        titles = QVBoxLayout()
        titles.setSpacing(2)
        titles.addWidget(self.context_title)
        titles.addWidget(self.context_source)

        layout.addLayout(titles)
        layout.addWidget(self.context_analysis)
        layout.addStretch(1)
        layout.addWidget(self.context_save)
        return bar

    def _build_inspector(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("InspectorPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        source_box = QFrame()
        source_box.setObjectName("PageSheet")
        source_layout = QVBoxLayout(source_box)
        source_layout.setContentsMargins(12, 12, 12, 12)
        source_layout.setSpacing(8)
        source_layout.addWidget(self._section_title("来源与承接"))
        self.source_document_label = QLabel("当前草稿暂无来源文档。")
        self.source_document_label.setWordWrap(True)
        self.source_analysis_label = QLabel("当前草稿暂无关联分析。")
        self.source_analysis_label.setWordWrap(True)
        source_layout.addWidget(self.source_document_label)
        source_layout.addWidget(self.source_analysis_label)
        layout.addWidget(source_box)

        action_box = QFrame()
        action_box.setObjectName("PageSheet")
        action_layout = QVBoxLayout(action_box)
        action_layout.setContentsMargins(12, 12, 12, 12)
        action_layout.setSpacing(8)
        action_layout.addWidget(self._section_title("高频承接动作"))
        self.insert_summary_button = QPushButton("插入分析摘要")
        self.insert_summary_button.clicked.connect(self._insert_analysis_summary)
        self.insert_contrib_button = QPushButton("插入贡献清单")
        self.insert_contrib_button.clicked.connect(self._insert_analysis_contributions)
        self.insert_method_button = QPushButton("插入方法框架")
        self.insert_method_button.clicked.connect(self._insert_method_scaffold)
        self.open_latex_button = QPushButton("转为 LaTeX")
        self.open_latex_button.clicked.connect(self._launch_latex)
        for widget in (
            self.insert_summary_button,
            self.insert_contrib_button,
            self.insert_method_button,
            self.open_latex_button,
        ):
            action_layout.addWidget(widget)
        layout.addWidget(action_box)

        export_box = QFrame()
        export_box.setObjectName("PageSheet")
        export_layout = QVBoxLayout(export_box)
        export_layout.setContentsMargins(12, 12, 12, 12)
        export_layout.setSpacing(8)
        export_layout.addWidget(self._section_title("导出与状态"))
        self.export_status_label = QLabel("尚未导出。")
        self.export_status_label.setWordWrap(True)
        self.save_status_label = QLabel("准备就绪。")
        self.save_status_label.setWordWrap(True)
        export_layout.addWidget(self.save_status_label)
        export_layout.addWidget(self.export_status_label)
        layout.addWidget(export_box)

        layout.addStretch(1)
        return panel

    def _section_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-size: 13px; font-weight: 600; color: #164e74;")
        return label

    def apply_theme(self, mode: str) -> None:
        self.theme_mode = mode
        palette = palette_for(mode)
        self.setStyleSheet(base_stylesheet(mode))
        self.editor.setStyleSheet(
            f"background: transparent; border: none; color: {palette.text};"
            f"selection-background-color: {palette.selection};"
        )
        self.page_sheet.setStyleSheet(
            f"QFrame#PageSheet {{ background: {palette.panel}; border: 1px solid {palette.border}; border-radius: 6px; }}"
        )

    def _build_statusbar(self) -> None:
        status = QStatusBar()
        self.setStatusBar(status)
        self.status_summary = QLabel()
        self.status_cursor = QLabel()
        self.status_pipeline = QLabel()
        status.addWidget(self.status_summary)
        status.addPermanentWidget(self.status_pipeline)
        status.addPermanentWidget(self.status_cursor)
        self._update_status()

    def _add_button(self, group: RibbonGroup, text: str, handler) -> None:
        button = QToolButton()
        button.setText(text)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        button.clicked.connect(handler)
        group.row.addWidget(button)

    def _build_ribbon(self) -> None:
        self.font_combo = QFontComboBox()
        self.font_combo.currentFontChanged.connect(self._set_font_family)
        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 48)
        self.size_spin.setValue(12)
        self.size_spin.valueChanged.connect(self._set_font_size)
        self.line_spacing = QComboBox()
        self.line_spacing.addItems(["1.0", "1.15", "1.5", "2.0"])
        self.line_spacing.setCurrentText("1.15")
        self.line_spacing.currentTextChanged.connect(self._apply_line_spacing)

        start_page = QWidget()
        start_layout = QHBoxLayout(start_page)
        start_layout.setContentsMargins(8, 8, 8, 8)
        start_layout.setSpacing(8)

        font_group = RibbonGroup("字体")
        font_group.row.addWidget(self.font_combo)
        font_group.row.addWidget(self.size_spin)
        start_layout.addWidget(font_group)

        style_group = RibbonGroup("样式")
        for label, handler in (
            ("加粗", lambda: self._toggle_char_attr("bold")),
            ("斜体", lambda: self._toggle_char_attr("italic")),
            ("下划线", lambda: self._toggle_char_attr("underline")),
            ("高亮", self._toggle_highlight),
            ("清除格式", self._clear_format),
            ("标题", lambda: self._push_document_command("应用标题样式", self._apply_heading_core)),
            ("正文", lambda: self._push_document_command("应用正文样式", self._apply_body_core)),
        ):
            self._add_button(style_group, label, handler)
        start_layout.addWidget(style_group)

        paragraph_group = RibbonGroup("段落")
        for label, handler in (
            ("左对齐", lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignLeft)),
            ("居中", lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignHCenter)),
            ("右对齐", lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignRight)),
            ("两端对齐", lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignJustify)),
            ("项目符号", lambda: self._apply_list(False)),
            ("编号", lambda: self._apply_list(True)),
        ):
            self._add_button(paragraph_group, label, handler)
        paragraph_group.row.addWidget(QLabel("行距"))
        paragraph_group.row.addWidget(self.line_spacing)
        start_layout.addWidget(paragraph_group)

        workflow_group = RibbonGroup("工作流")
        for label, handler in (
            ("分析摘要", self._insert_analysis_summary),
            ("贡献清单", self._insert_analysis_contributions),
            ("方法框架", self._insert_method_scaffold),
            ("转 LaTeX", self._launch_latex),
        ):
            self._add_button(workflow_group, label, handler)
        start_layout.addWidget(workflow_group)
        start_layout.addStretch(1)
        self.ribbon_tabs.addTab(start_page, "开始")

        insert_page = QWidget()
        insert_layout = QHBoxLayout(insert_page)
        insert_layout.setContentsMargins(8, 8, 8, 8)
        insert_layout.setSpacing(8)
        media_group = RibbonGroup("插入")
        for label, handler in (
            ("图片", self._insert_image),
            ("文本框", lambda: self._push_document_command("插入文本框", self._insert_text_box_core)),
            ("矩形框", lambda: self._push_document_command("插入矩形框", self._insert_shape_box_core)),
            ("分隔线", lambda: self._push_document_command("插入分隔线", self._insert_rule_core)),
            ("表格", self._insert_table),
        ):
            self._add_button(media_group, label, handler)
        insert_layout.addWidget(media_group)

        reference_group = RibbonGroup("引用与批注")
        for label, handler in (
            ("引用条目", lambda: self._push_document_command("插入引用条目", self._insert_reference_core)),
            ("图注", lambda: self._push_document_command("插入图注", lambda: self._insert_caption_core("图"))),
            ("表注", lambda: self._push_document_command("插入表注", lambda: self._insert_caption_core("表"))),
            ("批注", self._insert_comment),
        ):
            self._add_button(reference_group, label, handler)
        insert_layout.addWidget(reference_group)
        insert_layout.addStretch(1)
        self.ribbon_tabs.addTab(insert_page, "插入")

        layout_page = QWidget()
        layout_row = QHBoxLayout(layout_page)
        layout_row.setContentsMargins(8, 8, 8, 8)
        layout_row.setSpacing(8)
        spacing_group = RibbonGroup("布局")
        for label, handler in (
            ("段前 +6", lambda: self._adjust_spacing(6, 0)),
            ("段后 +6", lambda: self._adjust_spacing(0, 6)),
            ("增加缩进", lambda: self._adjust_indent(18)),
            ("减少缩进", lambda: self._adjust_indent(-18)),
            ("插入分页", lambda: self._push_document_command("插入分页", self._insert_page_break_core)),
        ):
            self._add_button(spacing_group, label, handler)
        layout_row.addWidget(spacing_group)
        layout_row.addStretch(1)
        self.ribbon_tabs.addTab(layout_page, "布局")

        reference_page = QWidget()
        reference_row = QHBoxLayout(reference_page)
        reference_row.setContentsMargins(8, 8, 8, 8)
        reference_row.setSpacing(8)
        citation_group = RibbonGroup("引用")
        for label, handler in (
            ("引用占位", lambda: self._push_document_command("插入引用占位", self._insert_reference_core)),
            ("参考文献列表", lambda: self._push_document_command("插入参考文献列表", self._insert_reference_list_core)),
        ):
            self._add_button(citation_group, label, handler)
        for factory in self.plugin_manager.writer_action_factories():
            for action_meta in factory():
                self._add_button(
                    citation_group,
                    action_meta["label"],
                    lambda checked=False, meta=action_meta: self._handle_plugin_action(meta["id"]),
                )
        reference_row.addWidget(citation_group)
        reference_row.addStretch(1)
        self.ribbon_tabs.addTab(reference_page, "引用")

        view_page = QWidget()
        view_row = QHBoxLayout(view_page)
        view_row.setContentsMargins(8, 8, 8, 8)
        view_row.setSpacing(8)
        export_group = RibbonGroup("导出")
        for label, handler in (
            ("导出 PDF", self._export_pdf),
            ("导出 DOCX", self._export_docx),
            ("导出 Markdown", self._export_markdown),
        ):
            self._add_button(export_group, label, handler)
        view_row.addWidget(export_group)
        inspect_group = RibbonGroup("视图与查找")
        for label, handler in (
            ("查找", self._find_text),
            ("放大", lambda: self._zoom_editor(1.08)),
            ("缩小", lambda: self._zoom_editor(0.92)),
        ):
            self._add_button(inspect_group, label, handler)
        view_row.addWidget(inspect_group)
        view_row.addStretch(1)
        self.ribbon_tabs.addTab(view_page, "导出")

    def _load_content(self) -> None:
        path = Path(self.descriptor.path)
        self._suspend_autosave = True
        if path.exists():
            self.editor.setHtml(path.read_text(encoding="utf-8", errors="ignore"))
        self._suspend_autosave = False
        self._set_save_feedback("已载入当前草稿。", dirty=False)

    def _resolve_context(self) -> dict:
        links = self.workspace.links_for_artifact("document", self.descriptor.document_id)
        source_document = None
        source_report = None
        linked_latex = []
        for link in links:
            if link.source_kind == "document" and link.source_id != self.descriptor.document_id:
                source_document = self.workspace.find_document(link.source_id)
            if link.source_kind == "analysis_report":
                source_report = self.workspace.find_analysis(link.source_id)
            if link.target_kind == "latex_session":
                session = self.workspace.find_latex_session(link.target_id)
                if session:
                    linked_latex.append(session)
        return {
            "source_document": source_document,
            "source_report": source_report,
            "linked_latex": linked_latex,
        }

    def _refresh_context_panels(self) -> None:
        context = self._resolve_context()
        source_document = context["source_document"]
        source_report = context["source_report"]
        linked_latex = context["linked_latex"]
        self.context_title.setText(self.descriptor.title)
        self.context_source.setText(
            f"来源文档：{source_document.title}" if source_document else "来源文档：当前草稿暂无来源文档"
        )
        self.context_analysis.setText(
            f"关联分析：{source_report.title}" if source_report else "关联分析：当前草稿暂无结构化分析承接"
        )
        self.source_document_label.setText(
            f"源文档：{source_document.title}\n可继续回到资料与阅读链路。"
            if source_document
            else "当前草稿尚未绑定来源文档。"
        )
        self.source_analysis_label.setText(
            f"关联分析：{source_report.title}\n可直接插入摘要、贡献点和方法结构。"
            if source_report
            else "当前草稿尚未绑定分析报告。"
        )
        self.insert_summary_button.setEnabled(source_report is not None)
        self.insert_contrib_button.setEnabled(source_report is not None)
        self.insert_method_button.setEnabled(source_report is not None)
        self.open_latex_button.setText("打开关联 LaTeX" if linked_latex else "转为 LaTeX")

    def _queue_autosave(self) -> None:
        if self._suspend_autosave:
            return
        self._dirty = True
        self._set_save_feedback("内容有变更，准备自动保存…", dirty=True)
        self.autosave_timer.start()

    def _autosave(self) -> None:
        path = Path(self.descriptor.path)
        path.write_text(self.editor.toHtml(), encoding="utf-8")
        self.descriptor.last_opened = now_iso()
        self.descriptor.excerpt = self.editor.toPlainText().strip()[:200]
        self.workspace.update_document(self.descriptor)
        self._dirty = False
        self._set_save_feedback(f"已自动保存 {self.descriptor.last_opened}", dirty=False)
        self._refresh_context_panels()

    def _set_save_feedback(self, text: str, dirty: bool) -> None:
        self.context_save.setText(text)
        self.save_status_label.setText(text)
        self.status_pipeline.setText("待保存" if dirty else "已保存")

    def _update_status(self) -> None:
        text = self.editor.toPlainText()
        word_count = len([part for part in text.split() if part.strip()])
        char_count = len(text)
        cursor = self.editor.textCursor()
        self.status_summary.setText(f"字数 {char_count}  ·  词数 {word_count}")
        self.status_cursor.setText(f"段落 {cursor.blockNumber() + 1}  ·  列 {cursor.columnNumber() + 1}")

    def apply_command_html(self, html: str) -> None:
        self._suspend_autosave = True
        self.editor.setHtml(html)
        self._suspend_autosave = False
        self._queue_autosave()

    def _push_document_command(self, label: str, action) -> None:
        before_html = self.editor.toHtml()
        action()
        after_html = self.editor.toHtml()
        if before_html != after_html:
            self.command_bus.execute(WriterDocumentStateCommand(self, label, before_html, after_html))
            self._set_save_feedback(f"已应用：{label}", dirty=True)

    def _set_font_family(self, font: QFont) -> None:
        self.editor.setCurrentFont(font)

    def _set_font_size(self, value: int) -> None:
        self.editor.setFontPointSize(float(value))

    def _toggle_char_attr(self, attr: str) -> None:
        if attr == "bold":
            self.editor.setFontWeight(
                QFont.Weight.Bold if self.editor.fontWeight() != QFont.Weight.Bold else QFont.Weight.Normal
            )
        elif attr == "italic":
            self.editor.setFontItalic(not self.editor.fontItalic())
        elif attr == "underline":
            self.editor.setFontUnderline(not self.editor.fontUnderline())

    def _toggle_highlight(self) -> None:
        char_format = QTextCharFormat()
        existing = self.editor.textCursor().charFormat().background().color()
        if existing.isValid() and existing.alpha() > 0:
            char_format.setBackground(Qt.GlobalColor.transparent)
        else:
            char_format.setBackground(self.palette().highlight().color().lighter(160))
        self.editor.textCursor().mergeCharFormat(char_format)

    def _clear_format(self) -> None:
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            cursor.setCharFormat(QTextCharFormat())
        else:
            self.editor.selectAll()
            self.editor.textCursor().setCharFormat(QTextCharFormat())
            self.editor.moveCursor(QTextCursor.MoveOperation.Start)

    def _apply_heading_core(self) -> None:
        cursor = self.editor.textCursor()
        block = QTextBlockFormat()
        block.setTopMargin(16)
        block.setBottomMargin(10)
        block.setLineHeight(120, QTextBlockFormat.LineHeightTypes.ProportionalHeight)
        cursor.mergeBlockFormat(block)
        char_format = QTextCharFormat()
        char_format.setFontPointSize(18)
        char_format.setFontWeight(QFont.Weight.DemiBold)
        cursor.mergeCharFormat(char_format)

    def _apply_body_core(self) -> None:
        cursor = self.editor.textCursor()
        block = QTextBlockFormat()
        block.setTopMargin(6)
        block.setBottomMargin(6)
        block.setLineHeight(115, QTextBlockFormat.LineHeightTypes.ProportionalHeight)
        cursor.mergeBlockFormat(block)
        char_format = QTextCharFormat()
        char_format.setFontPointSize(12)
        char_format.setFontWeight(QFont.Weight.Normal)
        cursor.mergeCharFormat(char_format)

    def _apply_line_spacing(self, value: str) -> None:
        cursor = self.editor.textCursor()
        block = cursor.blockFormat()
        block.setLineHeight(int(float(value) * 100), QTextBlockFormat.LineHeightTypes.ProportionalHeight)
        cursor.mergeBlockFormat(block)

    def _apply_list(self, numbered: bool) -> None:
        cursor = self.editor.textCursor()
        list_format = QTextListFormat()
        list_format.setStyle(QTextListFormat.Style.ListDecimal if numbered else QTextListFormat.Style.ListDisc)
        cursor.createList(list_format)

    def _insert_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "插入图片", "", "Images (*.png *.jpg *.jpeg *.bmp *.svg)")
        if not path:
            return
        self.editor.textCursor().insertImage(path)

    def _insert_text_box_core(self) -> None:
        self.editor.textCursor().insertHtml(
            "<div style='border:1px solid #c6d0d8; padding:12px; margin:8px 0;'>文本框内容</div>"
        )

    def _insert_shape_box_core(self) -> None:
        self.editor.textCursor().insertHtml(
            "<div style='border:1px solid #8aa0b2; padding:10px 14px; margin:8px 0;'>矩形说明框</div>"
        )

    def _insert_rule_core(self) -> None:
        self.editor.textCursor().insertHtml("<hr />")

    def _insert_page_break_core(self) -> None:
        self.editor.textCursor().insertHtml("<div style='page-break-after:always;'></div>")

    def _insert_table(self) -> None:
        rows, accepted = QInputDialog.getInt(self, "插入表格", "行数：", value=3, minValue=1, maxValue=20)
        if not accepted:
            return
        cols, accepted = QInputDialog.getInt(self, "插入表格", "列数：", value=3, minValue=1, maxValue=10)
        if not accepted:
            return
        self.editor.textCursor().insertTable(rows, cols)

    def _insert_reference_core(self) -> None:
        self.editor.textCursor().insertText("[作者, 年份]")

    def _insert_reference_list_core(self) -> None:
        self.editor.textCursor().insertHtml("<h2>参考文献</h2><p>[1] 作者. 题目. 年份.</p>")

    def _insert_caption_core(self, prefix: str) -> None:
        self.editor.textCursor().insertText(f"{prefix} 1  ")

    def _insert_comment(self) -> None:
        text, accepted = QInputDialog.getText(self, "插入批注", "内容：")
        if accepted and text:
            self._push_document_command(
                "插入批注",
                lambda: self.editor.textCursor().insertHtml(
                    f"<span style='background:#f0e4c8; padding:1px 4px;'>[{text}]</span>"
                ),
            )

    def _insert_analysis_summary(self) -> None:
        report = self._resolve_context()["source_report"]
        if not report:
            return
        self._push_document_command(
            "插入分析摘要",
            lambda: self.editor.textCursor().insertHtml(
                f"<h2>结构化摘要</h2><p>{report.summary}</p>"
            ),
        )

    def _insert_analysis_contributions(self) -> None:
        report = self._resolve_context()["source_report"]
        if not report:
            return
        self._push_document_command(
            "插入贡献清单",
            lambda: self.editor.textCursor().insertHtml(
                "<h2>贡献点</h2><ul>" + "".join(f"<li>{item}</li>" for item in report.contributions) + "</ul>"
            ),
        )

    def _insert_method_scaffold(self) -> None:
        report = self._resolve_context()["source_report"]
        if report and report.method_steps:
            body = "<h2>方法流程</h2><ol>" + "".join(f"<li>{item}</li>" for item in report.method_steps) + "</ol>"
        else:
            body = "<h2>方法概述</h2><p></p><h2>实验设置</h2><p></p><h2>结果分析</h2><p></p>"
        self._push_document_command("插入方法框架", lambda: self.editor.textCursor().insertHtml(body))

    def _adjust_spacing(self, top_delta: int, bottom_delta: int) -> None:
        cursor = self.editor.textCursor()
        block = cursor.blockFormat()
        block.setTopMargin(max(0, block.topMargin() + top_delta))
        block.setBottomMargin(max(0, block.bottomMargin() + bottom_delta))
        cursor.mergeBlockFormat(block)

    def _adjust_indent(self, delta: int) -> None:
        cursor = self.editor.textCursor()
        block = cursor.blockFormat()
        block.setLeftMargin(max(0, block.leftMargin() + delta))
        cursor.mergeBlockFormat(block)

    def _find_text(self) -> None:
        text, accepted = QInputDialog.getText(self, "查找", "关键词：")
        if accepted and text:
            self.editor.find(text)

    def _zoom_editor(self, factor: float) -> None:
        current = self.editor.fontPointSize() or 12.0
        self.editor.setFontPointSize(max(8.0, min(current * factor, 28.0)))

    def _run_export(self, label: str, suffix: str, action) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            f"导出 {label}",
            str(self.runtime_dir / f"{self.descriptor.title}{suffix}"),
            f"{label} (*{suffix})",
        )
        if not path:
            return
        self.task_center.begin(
            self._export_task_id,
            summary=f"正在导出 {label}…",
            detail=self.descriptor.title,
            meta={"target": path},
        )
        try:
            action(Path(path))
            self._last_export_path = path
            self.task_center.resolve(
                self._export_task_id,
                summary=f"{label} 导出完成。",
                detail=path,
                meta={"target": path},
            )
            self.export_status_label.setText(f"最近导出：{path}")
            QMessageBox.information(self, "导出完成", f"{label} 已导出。")
        except Exception as exc:
            self.task_center.fail(
                self._export_task_id,
                summary=f"{label} 导出失败",
                detail=str(exc),
                meta={"target": path},
            )
            QMessageBox.warning(self, "导出失败", str(exc))

    def _export_pdf(self) -> None:
        self._run_export("PDF", ".pdf", lambda target: self.exporter.export_pdf(self.editor.toHtml(), target))

    def _export_docx(self) -> None:
        self._run_export(
            "DOCX",
            ".docx",
            lambda target: self.exporter.export_docx(self.descriptor.title, self.editor.toHtml(), target),
        )

    def _export_markdown(self) -> None:
        self._run_export("Markdown", ".md", lambda target: self.exporter.export_markdown(self.editor.toHtml(), target))

    def _handle_plugin_action(self, action_id: str) -> None:
        if action_id == "insert_reference_stub":
            self._push_document_command("插入引用占位", lambda: self.editor.textCursor().insertText("[Ref: 作者, 题目, 年份]"))
        elif action_id == "insert_method_scaffold":
            self._insert_method_scaffold()
        elif action_id == "check_glossary_consistency":
            text = self.editor.toPlainText()
            acronyms = sorted(set(part for part in text.split() if part.isupper() and 2 <= len(part) <= 8))
            QMessageBox.information(
                self,
                "术语一致性",
                "检测到的缩写：\n" + ("\n".join(acronyms) if acronyms else "未发现明显缩写。"),
            )

    def _launch_latex(self) -> None:
        if self.launch_linked_latex:
            if self._dirty:
                self._autosave()
            self.launch_linked_latex(self.descriptor.document_id)
