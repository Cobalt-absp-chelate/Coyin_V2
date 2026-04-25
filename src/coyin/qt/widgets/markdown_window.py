from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QFont, QKeySequence, QTextCursor
from PySide6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QTextBrowser,
    QStatusBar,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from coyin.core.common import now_iso
from coyin.core.documents.models import DocumentDescriptor
from coyin.qt.widgets.auto_scroll import install_auto_hide_scrollbars
from coyin.qt.widgets.iconography import themed_icon
from coyin.qt.widgets.theme import base_stylesheet, palette_for

try:
    from markdown_it import MarkdownIt
except Exception:  # pragma: no cover
    MarkdownIt = None


class MarkdownWindow(QMainWindow):
    def __init__(self, descriptor: DocumentDescriptor, workspace, theme_mode: str = "light"):
        super().__init__()
        self.descriptor = descriptor
        self.workspace = workspace
        self.theme_mode = theme_mode
        self._dirty = False
        self._outline_open = True
        self._view_mode = "source"

        self.setWindowTitle(descriptor.title)
        self.resize(1280, 920)
        self.setMinimumSize(920, 680)

        self.editor = QPlainTextEdit()
        self.editor.setFont(QFont("Consolas", 12))
        self.editor.setTabStopDistance(28)
        self.editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.editor.textChanged.connect(self._queue_autosave)
        self.editor.textChanged.connect(self._refresh_outline)
        self.editor.textChanged.connect(self._refresh_preview)
        self.editor.textChanged.connect(self._update_status)
        install_auto_hide_scrollbars(self.editor)

        self.preview = QTextBrowser()
        self.preview.setVisible(False)
        self.preview.setOpenExternalLinks(True)
        install_auto_hide_scrollbars(self.preview)

        self.outline_tree = QTreeWidget()
        self.outline_tree.setHeaderHidden(True)
        self.outline_tree.itemActivated.connect(self._jump_from_outline)
        install_auto_hide_scrollbars(self.outline_tree)

        self.outline_dock = QDockWidget("", self)
        self.outline_dock.setWidget(self.outline_tree)
        self.outline_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.outline_dock.setMinimumWidth(220)
        self.outline_dock.setMaximumWidth(340)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.outline_dock)

        shell = QWidget()
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        shell_layout.addWidget(self._build_header())
        shell_layout.addWidget(self._build_toolbar())

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(18, 16, 18, 18)
        body_layout.setSpacing(14)

        self.editor_card = QWidget()
        editor_layout = QVBoxLayout(self.editor_card)
        editor_layout.setContentsMargins(24, 22, 24, 22)
        editor_layout.addWidget(self.editor)
        body_layout.addWidget(self.editor_card, 1)
        body_layout.addWidget(self.preview, 1)

        shell_layout.addWidget(body, 1)
        self.setCentralWidget(shell)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.setInterval(700)
        self.autosave_timer.setSingleShot(True)
        self.autosave_timer.timeout.connect(self._autosave)

        self._build_statusbar()
        self._build_shortcuts()
        self._load_content()
        self.apply_theme(theme_mode)

    def _build_header(self) -> QWidget:
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 10, 14, 8)
        layout.setSpacing(10)
        title_column = QVBoxLayout()
        title_column.setSpacing(2)
        self.title_label = QLabel(self.descriptor.title)
        self.title_label.setStyleSheet("font-size: 16px; font-weight: 600;")
        title_column.addWidget(self.title_label)
        layout.addLayout(title_column)
        layout.addStretch(1)
        return bar

    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        self.outline_button = QToolButton()
        self.outline_button.setIcon(themed_icon("markdown-outline", self.theme_mode, 18))
        self.outline_button.clicked.connect(self._toggle_outline)
        self.outline_button.setToolTip("显示或隐藏侧栏")
        self.outline_button.setText("侧栏")
        self._style_tool(self.outline_button)

        self.view_toggle_button = QToolButton()
        self.view_toggle_button.clicked.connect(self._toggle_view_mode)
        self._style_tool(self.view_toggle_button)

        self.bold_button = QToolButton()
        self.bold_button.setIcon(themed_icon("bold", self.theme_mode, 18))
        self.bold_button.clicked.connect(lambda: self._wrap_selection("**", "**"))
        self.bold_button.setToolTip("加粗 Ctrl+B")
        self.bold_button.setText("加粗")
        self._style_tool(self.bold_button)

        self.italic_button = QToolButton()
        self.italic_button.setIcon(themed_icon("italic", self.theme_mode, 18))
        self.italic_button.clicked.connect(lambda: self._wrap_selection("*", "*"))
        self.italic_button.setToolTip("斜体 Ctrl+I")
        self.italic_button.setText("斜体")
        self._style_tool(self.italic_button)

        self.link_button = QToolButton()
        self.link_button.setIcon(themed_icon("markdown-link", self.theme_mode, 18))
        self.link_button.clicked.connect(lambda: self._wrap_selection("[", "](url)"))
        self.link_button.setToolTip("链接 Ctrl+K")
        self.link_button.setText("链接")
        self._style_tool(self.link_button)

        self.code_button = QToolButton()
        self.code_button.setIcon(themed_icon("markdown-code", self.theme_mode, 18))
        self.code_button.clicked.connect(lambda: self._wrap_selection("`", "`"))
        self.code_button.setToolTip("行内代码 Ctrl+E")
        self.code_button.setText("代码")
        self._style_tool(self.code_button)

        self.code_block_button = QToolButton()
        self.code_block_button.setIcon(themed_icon("markdown-code", self.theme_mode, 18))
        self.code_block_button.clicked.connect(lambda: self._wrap_selection("\n```\n", "\n```\n"))
        self.code_block_button.setToolTip("代码块 Ctrl+Shift+E")
        self.code_block_button.setText("代码块")
        self._style_tool(self.code_block_button)

        self.quote_button = QToolButton()
        self.quote_button.setIcon(themed_icon("markdown-quote", self.theme_mode, 18))
        self.quote_button.clicked.connect(lambda: self._prefix_lines("> "))
        self.quote_button.setToolTip("引用")
        self.quote_button.setText("引用")
        self._style_tool(self.quote_button)

        self.todo_button = QToolButton()
        self.todo_button.setIcon(themed_icon("markdown-task", self.theme_mode, 18))
        self.todo_button.clicked.connect(lambda: self._prefix_lines("- [ ] "))
        self.todo_button.setToolTip("任务列表")
        self.todo_button.setText("任务")
        self._style_tool(self.todo_button)

        self.h1_button = QPushButton("H1")
        self.h1_button.clicked.connect(lambda: self._prefix_lines("# "))
        self.h2_button = QPushButton("H2")
        self.h2_button.clicked.connect(lambda: self._prefix_lines("## "))
        self.h3_button = QPushButton("H3")
        self.h3_button.clicked.connect(lambda: self._prefix_lines("### "))

        for widget in (
            self.outline_button,
            self.view_toggle_button,
            self.bold_button,
            self.italic_button,
            self.link_button,
            self.code_button,
            self.code_block_button,
            self.quote_button,
            self.todo_button,
            self.h1_button,
            self.h2_button,
            self.h3_button,
        ):
            layout.addWidget(widget)
        layout.addStretch(1)
        return bar

    def _style_tool(self, button: QToolButton) -> None:
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        button.setMinimumSize(72, 56)

    def _build_statusbar(self) -> None:
        status = QStatusBar()
        self.setStatusBar(status)
        self.status_label = QLabel()
        status.addPermanentWidget(self.status_label)
        self._update_status()

    def _build_shortcuts(self) -> None:
        shortcuts = [
            (QKeySequence("Ctrl+B"), lambda: self._wrap_selection("**", "**")),
            (QKeySequence("Ctrl+I"), lambda: self._wrap_selection("*", "*")),
            (QKeySequence("Ctrl+K"), lambda: self._wrap_selection("[", "](url)")),
            (QKeySequence("Ctrl+E"), lambda: self._wrap_selection("`", "`")),
            (QKeySequence("Ctrl+Shift+E"), lambda: self._wrap_selection("\n```\n", "\n```\n")),
            (QKeySequence("Ctrl+1"), lambda: self._prefix_lines("# ")),
            (QKeySequence("Ctrl+2"), lambda: self._prefix_lines("## ")),
            (QKeySequence("Ctrl+3"), lambda: self._prefix_lines("### ")),
            (QKeySequence("Ctrl+Shift+7"), lambda: self._prefix_lines("1. ")),
            (QKeySequence("Ctrl+Shift+9"), lambda: self._prefix_lines("- [ ] ")),
        ]
        for seq, handler in shortcuts:
            action = QAction(self)
            action.setShortcut(seq)
            action.triggered.connect(handler)
            self.addAction(action)

    def _load_content(self) -> None:
        path = Path(self.descriptor.path)
        if path.exists():
            self.editor.setPlainText(path.read_text(encoding="utf-8", errors="ignore"))
        else:
            self.editor.setPlainText(f"# {self.descriptor.title}\n\n")
        self._refresh_outline()
        self._refresh_preview()
        self._update_status()

    def _queue_autosave(self) -> None:
        self._dirty = True
        self.autosave_timer.start()

    def _autosave(self) -> None:
        path = Path(self.descriptor.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        text = self.editor.toPlainText()
        path.write_text(text, encoding="utf-8")
        self.descriptor.last_opened = now_iso()
        self.descriptor.excerpt = text.strip()[:200]
        self.workspace.update_document(self.descriptor)
        self._dirty = False

    def _wrap_selection(self, prefix: str, suffix: str) -> None:
        cursor = self.editor.textCursor()
        selected = cursor.selectedText() or "文本"
        cursor.insertText(f"{prefix}{selected}{suffix}")

    def _prefix_lines(self, prefix: str) -> None:
        cursor = self.editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
        text = cursor.selectedText().replace("\u2029", "\n")
        lines = [line if line.startswith(prefix) else prefix + line for line in text.splitlines()]
        cursor.insertText("\n".join(lines))

    def _refresh_outline(self) -> None:
        self.outline_tree.clear()
        for index, line in enumerate(self.editor.toPlainText().splitlines(), start=1):
            stripped = line.strip()
            if not stripped.startswith("#"):
                continue
            depth = len(stripped) - len(stripped.lstrip("#"))
            title = stripped[depth:].strip() or f"标题 {index}"
            item = QTreeWidgetItem([title])
            item.setData(0, Qt.ItemDataRole.UserRole, index)
            self.outline_tree.addTopLevelItem(item)

    def _refresh_preview(self) -> None:
        if self._view_mode != "rendered":
            return
        text = self.editor.toPlainText()
        if MarkdownIt is None:
            self.preview.setPlainText(text)
            return
        self.preview.setHtml(MarkdownIt().render(text))

    def _jump_from_outline(self, item: QTreeWidgetItem) -> None:
        self._set_view_mode("source")
        line = int(item.data(0, Qt.ItemDataRole.UserRole) or 1)
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor, max(0, line - 1))
        self.editor.setTextCursor(cursor)
        self.editor.centerCursor()
        self.editor.setFocus()

    def _toggle_outline(self) -> None:
        self._outline_open = not self._outline_open
        self.outline_dock.setVisible(self._outline_open)

    def _set_view_mode(self, mode: str) -> None:
        self._view_mode = mode
        rendered = mode == "rendered"
        self.editor_card.setVisible(not rendered)
        self.preview.setVisible(rendered)
        self._update_view_toggle_button()
        if rendered:
            self._refresh_preview()

    def _toggle_view_mode(self) -> None:
        self._set_view_mode("rendered" if self._view_mode == "source" else "source")

    def _update_view_toggle_button(self) -> None:
        next_mode = "source" if self._view_mode == "rendered" else "rendered"
        next_text = "源码" if next_mode == "source" else "渲染"
        next_icon = "markdown-code" if next_mode == "source" else "markdown-preview"
        self.view_toggle_button.setIcon(themed_icon(next_icon, self.theme_mode, 18))
        self.view_toggle_button.setToolTip(f"切换到{next_text}模式")
        self.view_toggle_button.setText(next_text)

    def _update_status(self) -> None:
        text = self.editor.toPlainText()
        words = len([part for part in re.split(r"\s+", text) if part.strip()])
        chars = len(text)
        self.status_label.setText(f"总字数 {chars}  ·  {words} 词")

    def apply_theme(self, mode: str) -> None:
        self.theme_mode = mode
        self.setStyleSheet(base_stylesheet(mode))
        palette = palette_for(mode)
        self.editor.setStyleSheet(
            f"background: {palette.panel}; color: {palette.text}; border: none; selection-background-color: {palette.selection};"
        )
        self.preview.setStyleSheet(
            f"background: {palette.panel}; color: {palette.text}; border: 1px solid {palette.border};"
        )
        self._update_view_toggle_button()
        self._set_view_mode(self._view_mode)
