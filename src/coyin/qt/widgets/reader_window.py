from __future__ import annotations

from dataclasses import dataclass
from html import escape

from PySide6.QtCore import QCoreApplication, QEvent, QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QImage, QKeySequence, QPixmap, QTextCharFormat, QTextCursor
from PySide6.QtPdf import QPdfDocument
from PySide6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenu,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QTreeWidget,
    QTreeWidgetItem,
    QListWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from markdown_it import MarkdownIt

from coyin.core.common import now_iso, short_id
from coyin.core.commands.annotation_commands import AddAnnotationCommand, RemoveAnnotationCommand, UpdateAnnotationCommand
from coyin.core.documents.models import (
    AnnotationKind,
    AnnotationRecord,
    DocumentDescriptor,
    DocumentKind,
    DocumentSnapshot,
)
from coyin.qt.widgets.auto_scroll import install_auto_hide_scrollbars
from coyin.qt.widgets.detachable_tabs import DetachableTabWidget
from coyin.qt.widgets.iconography import themed_icon
from coyin.qt.widgets.quick_pdf_view import QuickPdfView
from coyin.qt.widgets.theme import base_stylesheet
try:
    import fitz  # type: ignore[import-untyped]
except Exception:  # pragma: no cover
    fitz = None


ANNOTATION_COLORS = {
    AnnotationKind.HIGHLIGHT.value: "#e2c48b",
    AnnotationKind.UNDERLINE.value: "#9fb6cb",
    AnnotationKind.NOTE.value: "#c6b28d",
}

READER_TOOLBAR_META = {
    "reader-left": ("边栏", "显示或隐藏左侧导航边栏。"),
    "reader-right": ("标注与翻译", "显示或隐藏右侧的标注与翻译面板。"),
    "reader-translate": ("全文翻译", "将当前文档翻译为独立文件并自动加入文库。"),
    "reader-fit-page": ("适应页面", "切换为整页缩放显示。"),
    "reader-fit-width": ("适应宽度", "切换为按页面宽度缩放显示。"),
    "reader-one-page": ("单页流", "使用连续滚动的单页流视图。"),
    "reader-two-page": ("双页视图", "以类似文档排版的双页并排方式阅读。"),
    "zoom-out": ("缩小", "降低当前文档的缩放比例。"),
    "zoom-in": ("放大", "提高当前文档的缩放比例。"),
}


class TextReaderPane(QWidget):
    annotationRequested = Signal(dict)
    translationRequested = Signal(dict)

    def __init__(self, descriptor: DocumentDescriptor, snapshot: DocumentSnapshot):
        super().__init__()
        self.document_id = descriptor.document_id
        self.descriptor = descriptor
        self.snapshot = snapshot
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setReadOnly(True)
        self.browser.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.browser.customContextMenuRequested.connect(self._open_context_menu)
        install_auto_hide_scrollbars(self.browser)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.browser)
        self._apply_content()

    def _apply_content(self) -> None:
        if self.descriptor.kind == DocumentKind.MARKDOWN.value:
            self.browser.setHtml(MarkdownIt().render(self.snapshot.raw_text))
        else:
            self.browser.setPlainText(self.snapshot.raw_text)

    def _open_context_menu(self, point) -> None:
        cursor = self.browser.cursorForPosition(point)
        self.browser.setTextCursor(cursor)
        selected = self.browser.textCursor().selectedText().strip()
        menu = self.browser.createStandardContextMenu()
        if selected:
            menu.addSeparator()
            for kind in (AnnotationKind.HIGHLIGHT.value, AnnotationKind.UNDERLINE.value, AnnotationKind.NOTE.value):
                action = menu.addAction(f"添加{kind}")
                action.triggered.connect(lambda checked=False, item=kind: self._emit_annotation(item, selected))
            translate_action = menu.addAction("翻译选中内容")
            translate_action.triggered.connect(lambda checked=False: self.translationRequested.emit({"text": selected}))
        menu.exec(self.browser.mapToGlobal(point))

    def _emit_annotation(self, kind: str, selected: str) -> None:
        note = ""
        if kind == AnnotationKind.NOTE.value:
            note, accepted = QInputDialog.getText(self, "添加便签", "内容：")
            if not accepted:
                return
        self.annotationRequested.emit(
            {
                "kind": kind,
                "quote": selected,
                "page": 0,
                "note": note,
                "rects": [],
            }
        )

    def apply_annotations(self, annotations: list[AnnotationRecord]) -> None:
        selections = []
        document = self.browser.document()
        for annotation in annotations:
            if not annotation.quote:
                continue
            cursor = document.find(annotation.quote)
            if cursor.isNull():
                continue
            extra = QTextBrowser.ExtraSelection()
            extra.cursor = cursor
            format_ = QTextCharFormat()
            color = QColor(annotation.color)
            if annotation.kind == AnnotationKind.UNDERLINE.value:
                format_.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
                format_.setUnderlineColor(color)
            else:
                format_.setBackground(color.lighter(130))
            extra.format = format_
            selections.append(extra)
        self.browser.setExtraSelections(selections)

    def search(self, term: str) -> None:
        if not term:
            return
        found = self.browser.find(term)
        if not found:
            cursor = self.browser.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self.browser.setTextCursor(cursor)
            self.browser.find(term)

    def jump_to_quote(self, quote: str) -> None:
        cursor = self.browser.document().find(quote)
        if not cursor.isNull():
            self.browser.setTextCursor(cursor)
            self.browser.ensureCursorVisible()


class PdfReaderPane(QWidget):
    annotationRequested = Signal(dict)
    translationRequested = Signal(dict)

    def __init__(self, descriptor: DocumentDescriptor, snapshot: DocumentSnapshot):
        super().__init__()
        self.document_id = descriptor.document_id
        self.descriptor = descriptor
        self.snapshot = snapshot
        self._loaded = False
        self._open_requested = False
        self.view = QuickPdfView()
        self.view.selectionContextMenuRequested.connect(self._open_selection_menu)
        self.view.documentLoadChanged.connect(self._set_view_ready)
        self.loading_overlay = QWidget(self)
        self.loading_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.loading_overlay.setStyleSheet("background: rgba(241, 244, 248, 0.92);")
        overlay_layout = QVBoxLayout(self.loading_overlay)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        self.loading_label = QLabel("正在载入 PDF…")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("color: #4c5d70; font-size: 12px;")
        overlay_layout.addWidget(self.loading_label)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)
        self._load_document()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.loading_overlay.setGeometry(self.rect())

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._loaded and not self._open_requested:
            QTimer.singleShot(0, self._try_open_document)

    def _load_document(self) -> None:
        if self._loaded or self._open_requested:
            return
        self.loading_label.setText("正在载入 PDF…")
        self.loading_overlay.show()
        self._try_open_document()

    def _try_open_document(self) -> None:
        if self._loaded or self._open_requested:
            return
        window = self.window()
        if not self.isVisible() or window is None or not window.isVisible():
            QTimer.singleShot(60, self._try_open_document)
            return
        self._open_requested = True
        self.view.open_pdf(self.descriptor.path)

    def apply_snapshot(self, snapshot: DocumentSnapshot) -> None:
        self.snapshot = snapshot
        self.view.request_state()

    def set_theme(self, mode: str) -> None:
        self.view.set_theme(mode)

    def close_document(self) -> None:
        try:
            self.view.clear_document()
        except Exception:
            pass
        self._loaded = False
        self._open_requested = False
        self.loading_label.setText("正在载入 PDF…")
        self.loading_overlay.show()

    def _set_view_ready(self, ok: bool) -> None:
        if ok:
            self._loaded = True
            self._open_requested = False
            QTimer.singleShot(700, self.loading_overlay.hide)
            QTimer.singleShot(0, self.view.request_state)
            return
        self._loaded = False
        self._open_requested = False
        self.loading_label.setText("PDF 载入失败。")
        self.loading_overlay.show()

    def _open_selection_menu(self, selected_text: str, global_pos) -> None:
        menu = QMenu(self)
        for kind in (AnnotationKind.HIGHLIGHT.value, AnnotationKind.UNDERLINE.value, AnnotationKind.NOTE.value):
            action = menu.addAction(f"添加{kind}")
            action.triggered.connect(
                lambda checked=False, item=kind: self._emit_annotation(item, selected_text)
            )
        menu.addSeparator()
        translate_action = menu.addAction("翻译选中内容")
        translate_action.triggered.connect(lambda checked=False: self.translationRequested.emit({"text": selected_text}))
        menu.exec(global_pos)

    def _emit_annotation(self, kind: str, selected_text: str) -> None:
        note = ""
        if kind == AnnotationKind.NOTE.value:
            note, accepted = QInputDialog.getText(self, "添加便签", "内容：")
            if not accepted:
                return
        self.annotationRequested.emit(
            {
                "kind": kind,
                "quote": selected_text,
                "page": max(0, self.view.current_page() - 1) if self.view.current_page() > 0 else None,
                "note": note,
                "rects": [],
            }
        )

    def apply_annotations(self, annotations: list[AnnotationRecord]) -> None:
        _ = annotations

    def search(self, term: str) -> None:
        if not self._loaded:
            return
        self.view.search(term)

    def jump_to_annotation(self, record: AnnotationRecord) -> None:
        if not self._loaded:
            return
        if record.page is not None:
            self.view.go_to_page(int(record.page) + 1)
            self.view.request_state()
            return
        if record.quote:
            self.view.search(record.quote)


@dataclass(slots=True)
class ReaderServices:
    annotation_store: object
    command_bus: object
    workspace: object
    render_coordinator: object
    window_registry: object
    open_reader_document: object
    cancel_reader_document: object
    translate_selection: object
    translate_document: object


class ReaderWindow(QMainWindow):
    requestedDetach = Signal(str)

    def __init__(self, services: ReaderServices, theme_mode: str = "light"):
        super().__init__()
        self.services = services
        self.theme_mode = theme_mode
        self.window_id = services.window_registry.register("reader", self)
        self.setWindowTitle("阅读")
        self.resize(1360, 900)
        self.setStyleSheet(base_stylesheet(theme_mode))

        self.tabs = DetachableTabWidget()
        self.tabs.detach_requested.connect(self._detach_tab)
        self.tabs.import_requested.connect(self._import_document)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._refresh_side_panels)
        self.setCentralWidget(self.tabs)

        self.outline_tree = QTreeWidget()
        self.outline_tree.setHeaderHidden(True)
        self.outline_tree.itemActivated.connect(self._jump_from_outline)
        install_auto_hide_scrollbars(self.outline_tree)

        self.thumbnail_list = QListWidget()
        self.thumbnail_list.setViewMode(QListWidget.ViewMode.IconMode)
        self.thumbnail_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.thumbnail_list.setMovement(QListWidget.Movement.Static)
        self.thumbnail_list.setSpacing(10)
        self.thumbnail_list.setIconSize(QPixmap(112, 150).size())
        self.thumbnail_list.itemActivated.connect(self._jump_from_thumbnail)
        install_auto_hide_scrollbars(self.thumbnail_list)

        self.annotation_list = QListWidget()
        self.annotation_list.itemActivated.connect(self._jump_from_annotation)
        self.annotation_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.annotation_list.customContextMenuRequested.connect(self._open_annotation_menu)
        install_auto_hide_scrollbars(self.annotation_list)
        self.translation_toolbar = QWidget()
        translation_toolbar_layout = QHBoxLayout(self.translation_toolbar)
        translation_toolbar_layout.setContentsMargins(8, 8, 8, 8)
        translation_toolbar_layout.setSpacing(8)
        self.translation_note_button = QPushButton("转为Note")
        self.translation_note_button.clicked.connect(self._translation_to_note)
        self.translation_note_button.setEnabled(False)
        self.translation_hint_label = QLabel("翻译结果可转为标注便签。")
        self.translation_hint_label.setStyleSheet("color: #708195;")
        translation_toolbar_layout.addWidget(self.translation_note_button)
        translation_toolbar_layout.addWidget(self.translation_hint_label, 1)
        self.translation_view = QTextBrowser()
        self.translation_view.setOpenExternalLinks(True)
        self.translation_view.setReadOnly(True)
        install_auto_hide_scrollbars(self.translation_view)
        self.translation_panel = QWidget()
        translation_panel_layout = QVBoxLayout(self.translation_panel)
        translation_panel_layout.setContentsMargins(0, 0, 0, 0)
        translation_panel_layout.setSpacing(0)
        translation_panel_layout.addWidget(self.translation_toolbar)
        translation_panel_layout.addWidget(self.translation_view, 1)

        self._tab_payloads: dict[str, dict] = {}
        self._fit_mode = "width"
        self._page_spread = "single"
        self._thumbnail_cache: dict[str, list[QListWidgetItem]] = {}
        self._state_timer = QTimer(self)
        self._state_timer.setInterval(240)
        self._state_timer.timeout.connect(self._poll_view_state)
        self._left_sidebar_open = True
        self._right_sidebar_open = True
        self._translation_payload: dict[str, str] = {}

        self._build_toolbar()
        self._build_docks()
        self._build_shortcuts()

        self.services.annotation_store.changed.connect(self._on_annotation_changed)

    def apply_theme(self, mode: str) -> None:
        self.theme_mode = mode
        self.setStyleSheet(base_stylesheet(mode))
        self._apply_toolbar_icons()
        widget = self.tabs.currentWidget()
        if isinstance(widget, PdfReaderPane):
            widget.set_theme(mode)

    def _tooltip_html(self, title: str, description: str) -> str:
        return (
            f"<div style='min-width:180px;'>"
            f"<div style='font-weight:700; margin-bottom:4px;'>{escape(title)}</div>"
            f"<div style='color:#4c5d70; line-height:1.45;'>{escape(description)}</div>"
            "</div>"
        )

    def _icon_meta(self, action_id: str) -> tuple[str, str]:
        return READER_TOOLBAR_META.get(action_id, (action_id, "执行该操作。"))

    def _set_toolbar_hint(self, widget, action_id: str) -> None:
        title, description = self._icon_meta(action_id)
        widget.setToolTip(self._tooltip_html(title, description))
        widget.setStatusTip(description)
        if hasattr(widget, "setAccessibleName"):
            widget.setAccessibleName(title)
        if hasattr(widget, "setToolButtonStyle"):
            widget.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        if hasattr(widget, "setAutoRaise"):
            widget.setAutoRaise(True)
        if hasattr(widget, "setFixedSize"):
            widget.setFixedSize(34, 30)
        if hasattr(widget, "setCursor"):
            widget.setCursor(Qt.CursorShape.PointingHandCursor)

    def _build_toolbar(self) -> None:
        toolbar = self.addToolBar("Reader")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.sidebar_toggle = QToolButton()
        self.sidebar_toggle.setText("")
        self._set_toolbar_hint(self.sidebar_toggle, "reader-left")
        self.sidebar_toggle.clicked.connect(self._toggle_left_sidebar)
        self.note_toggle = QToolButton()
        self.note_toggle.setText("")
        self._set_toolbar_hint(self.note_toggle, "reader-right")
        self.note_toggle.clicked.connect(self._toggle_right_sidebar)
        self.document_title_label = QLabel("阅读")
        self.document_title_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        self.translate_button = QToolButton()
        self.translate_button.setText("")
        self._set_toolbar_hint(self.translate_button, "reader-translate")
        self.translate_button.clicked.connect(self._translate_current_document)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索当前文档")
        self.search_edit.returnPressed.connect(self._search_current)
        self.fit_toggle_action = QAction("适应页面", self)
        self.fit_toggle_action.triggered.connect(self._toggle_fit_mode)
        self.spread_toggle = QToolButton()
        self.spread_toggle.setText("")
        self._set_toolbar_hint(self.spread_toggle, "reader-two-page")
        self.spread_toggle.clicked.connect(self._toggle_page_spread)
        self.page_edit = QLineEdit()
        self.page_edit.setFixedWidth(52)
        self.page_edit.setPlaceholderText("页码")
        self.page_edit.returnPressed.connect(self._jump_from_page_edit)
        self.page_total_label = QLabel("/ 0")
        self.zoom_minus = QToolButton()
        self.zoom_minus.setText("")
        self._set_toolbar_hint(self.zoom_minus, "zoom-out")
        self.zoom_minus.clicked.connect(lambda: self._nudge_zoom(-10))
        self.zoom_plus = QToolButton()
        self.zoom_plus.setText("")
        self._set_toolbar_hint(self.zoom_plus, "zoom-in")
        self.zoom_plus.clicked.connect(lambda: self._nudge_zoom(10))
        self.zoom_edit = QLineEdit("100%")
        self.zoom_edit.setFixedWidth(64)
        self.zoom_edit.returnPressed.connect(self._apply_zoom_edit)
        self._apply_toolbar_icons()
        toolbar.addWidget(self.sidebar_toggle)
        toolbar.addWidget(self.note_toggle)
        toolbar.addWidget(self.document_title_label)
        toolbar.addSeparator()
        toolbar.addAction(self.fit_toggle_action)
        toolbar.addWidget(self.spread_toggle)
        toolbar.addSeparator()
        toolbar.addWidget(self.page_edit)
        toolbar.addWidget(self.page_total_label)
        toolbar.addSeparator()
        toolbar.addWidget(self.zoom_minus)
        toolbar.addWidget(self.zoom_edit)
        toolbar.addWidget(self.zoom_plus)
        toolbar.addSeparator()
        toolbar.addWidget(self.search_edit)
        toolbar.addSeparator()
        toolbar.addWidget(self.translate_button)

    def _apply_toolbar_icons(self) -> None:
        self.sidebar_toggle.setIcon(themed_icon("reader-left", self.theme_mode, 18))
        self.sidebar_toggle.setIconSize(QPixmap(18, 18).size())
        self.note_toggle.setIcon(themed_icon("reader-right", self.theme_mode, 18))
        self.note_toggle.setIconSize(QPixmap(18, 18).size())
        self.translate_button.setIcon(themed_icon("reader-translate", self.theme_mode, 18))
        self.translate_button.setIconSize(QPixmap(18, 18).size())
        self.zoom_minus.setIcon(themed_icon("zoom-out", self.theme_mode, 18))
        self.zoom_minus.setIconSize(QPixmap(18, 18).size())
        self.zoom_plus.setIcon(themed_icon("zoom-in", self.theme_mode, 18))
        self.zoom_plus.setIconSize(QPixmap(18, 18).size())
        fit_action = "reader-fit-width" if self._fit_mode == "page" else "reader-fit-page"
        self.fit_toggle_action.setIcon(themed_icon(fit_action, self.theme_mode, 18))
        spread_action = "reader-two-page" if self._page_spread == "single" else "reader-one-page"
        self.spread_toggle.setIcon(themed_icon(spread_action, self.theme_mode, 18))
        self.spread_toggle.setIconSize(QPixmap(18, 18).size())
        self._set_toolbar_hint(self.spread_toggle, spread_action)
        title, description = self._icon_meta(fit_action)
        self.fit_toggle_action.setText(title)
        self.fit_toggle_action.setToolTip(self._tooltip_html(title, description))
        self.fit_toggle_action.setStatusTip(description)

    def _build_shortcuts(self) -> None:
        self.find_action = QAction(self)
        self.find_action.setShortcut(QKeySequence.StandardKey.Find)
        self.find_action.triggered.connect(self._focus_search)
        self.addAction(self.find_action)

    def _build_docks(self) -> None:
        self.left_tabs = QTabWidget()
        self.left_tabs.setDocumentMode(True)
        self.left_tabs.addTab(self.thumbnail_list, "缩略图")
        self.left_tabs.addTab(self.outline_tree, "目录")

        self.outline_dock = QDockWidget("导航", self)
        self.outline_dock.setWidget(self.left_tabs)
        self.outline_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.outline_dock.setMinimumWidth(240)
        self.outline_dock.setMaximumWidth(320)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.outline_dock)

        self.right_tabs = QTabWidget()
        self.right_tabs.setDocumentMode(True)
        self.right_tabs.addTab(self.annotation_list, "标注")
        self.right_tabs.addTab(self.translation_panel, "翻译")

        self.note_dock = QDockWidget("标注与翻译", self)
        self.note_dock.setWidget(self.right_tabs)
        self.note_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.note_dock.setMinimumWidth(260)
        self.note_dock.setMaximumWidth(420)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.note_dock)

    def closeEvent(self, event) -> None:
        while self.tabs.count() > 0:
            self._close_tab(0)
        self.services.window_registry.unregister(self.window_id)
        return super().closeEvent(event)

    def _empty_snapshot(self, descriptor: DocumentDescriptor) -> DocumentSnapshot:
        return DocumentSnapshot(document_id=descriptor.document_id, raw_text="", blocks=[], outline=[], page_count=0)

    def open_document(
        self,
        descriptor: DocumentDescriptor,
        snapshot: DocumentSnapshot | None,
        loading: bool = False,
        task_id: str = "",
    ) -> None:
        for index in range(self.tabs.count()):
            widget = self.tabs.widget(index)
            if getattr(widget, "document_id", "") == descriptor.document_id:
                self.tabs.setCurrentIndex(index)
                if snapshot is not None:
                    self.apply_document_snapshot(descriptor.document_id, snapshot)
                return
        effective_snapshot = snapshot or self._empty_snapshot(descriptor)
        pane = self._create_pane(descriptor, effective_snapshot)
        if isinstance(pane, PdfReaderPane):
            pane.set_theme(self.theme_mode)
        pane.document_id = descriptor.document_id
        pane.annotationRequested.connect(lambda payload, doc=descriptor: self._create_annotation(doc, payload))
        if hasattr(pane, "translationRequested"):
            pane.translationRequested.connect(lambda payload, doc=descriptor: self._request_selection_translation(doc, payload))
        index = self.tabs.addTab(pane, descriptor.title)
        self.tabs.setCurrentIndex(index)
        self._tab_payloads[descriptor.document_id] = {
            "descriptor": descriptor,
            "snapshot": effective_snapshot,
            "loading": loading,
            "load_error": "",
            "task_id": task_id,
        }
        if isinstance(pane, PdfReaderPane):
            pane.view.stateChanged.connect(self._update_view_state)
            pane.view.zoomPreviewChanged.connect(self._update_zoom_preview)
            self._state_timer.start()
            self._rebuild_thumbnails(descriptor)
        self.document_title_label.setText(descriptor.title)
        self.services.window_registry.attach_document(self.window_id, descriptor.document_id)
        self._refresh_side_panels()

    def apply_document_snapshot(self, document_id: str, snapshot: DocumentSnapshot) -> None:
        payload = self._tab_payloads.get(document_id)
        if not payload:
            return
        payload["snapshot"] = snapshot
        payload["loading"] = False
        payload["load_error"] = ""
        widget = self._widget_for_document(document_id)
        if isinstance(widget, PdfReaderPane):
            widget.apply_snapshot(snapshot)
        self._refresh_side_panels()

    def mark_document_load_failed(self, document_id: str, message: str) -> None:
        payload = self._tab_payloads.get(document_id)
        if not payload:
            return
        payload["loading"] = False
        payload["load_error"] = message
        self._refresh_side_panels()

    def _widget_for_document(self, document_id: str):
        for index in range(self.tabs.count()):
            widget = self.tabs.widget(index)
            if getattr(widget, "document_id", "") == document_id:
                return widget
        return None

    def _create_pane(self, descriptor: DocumentDescriptor, snapshot: DocumentSnapshot):
        if descriptor.kind == DocumentKind.PDF.value:
            return PdfReaderPane(descriptor, snapshot)
        return TextReaderPane(descriptor, snapshot)

    def _detach_tab(self, index: int, global_pos) -> None:
        widget = self.tabs.widget(index)
        if not widget:
            return
        document_id = getattr(widget, "document_id", "")
        self._dispose_document(document_id, widget, index)
        self.requestedDetach.emit(document_id)

    def _import_document(self, document_id: str) -> None:
        self.services.open_reader_document(document_id, target=self)

    def _close_tab(self, index: int) -> None:
        widget = self.tabs.widget(index)
        if widget:
            self._dispose_document(getattr(widget, "document_id", ""), widget, index)
        self._refresh_side_panels()

    def _dispose_document(self, document_id: str, widget, index: int) -> None:
        payload = self._tab_payloads.pop(document_id, None)
        if payload and payload.get("task_id"):
            self.services.cancel_reader_document(self.window_id, document_id, payload["task_id"])
        self.services.window_registry.detach_document(self.window_id, document_id)
        self.tabs.removeTab(index)
        if hasattr(widget, "close_document"):
            try:
                widget.close_document()
            except Exception:
                pass
        widget.setParent(None)
        widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        if self.tabs.count() == 0:
            self._state_timer.stop()
            self.document_title_label.setText("阅读")

    def _search_current(self) -> None:
        widget = self.tabs.currentWidget()
        if widget and hasattr(widget, "search"):
            widget.search(self.search_edit.text().strip())

    def _focus_search(self) -> None:
        self.search_edit.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.search_edit.selectAll()

    def _set_fit_mode(self, mode: str) -> None:
        self._fit_mode = "page" if mode == "page" else "width"
        self.fit_toggle_action.setText("适应宽度" if self._fit_mode == "page" else "适应页面")
        self._apply_toolbar_icons()
        widget = self.tabs.currentWidget()
        if isinstance(widget, PdfReaderPane):
            widget.view.set_scale_mode(self._fit_mode)
            QTimer.singleShot(180, widget.view.request_state)

    def _toggle_fit_mode(self) -> None:
        self._set_fit_mode("page" if self._fit_mode == "width" else "width")

    def _set_page_spread(self, mode: str) -> None:
        self._page_spread = "double" if mode == "double" else "single"
        self._apply_toolbar_icons()
        widget = self.tabs.currentWidget()
        if isinstance(widget, PdfReaderPane):
            widget.view.set_page_spread(self._page_spread)
            QTimer.singleShot(180, widget.view.request_state)

    def _toggle_page_spread(self) -> None:
        self._set_page_spread("double" if self._page_spread == "single" else "single")

    def _toggle_left_sidebar(self) -> None:
        self._left_sidebar_open = not self._left_sidebar_open
        self.outline_dock.setVisible(self._left_sidebar_open)

    def _toggle_right_sidebar(self) -> None:
        self._right_sidebar_open = not self._right_sidebar_open
        self.note_dock.setVisible(self._right_sidebar_open)

    def _jump_from_page_edit(self) -> None:
        widget = self.tabs.currentWidget()
        if not isinstance(widget, PdfReaderPane):
            return
        try:
            page = int(self.page_edit.text().strip())
        except Exception:
            return
        widget.view.go_to_page(page)
        QTimer.singleShot(180, widget.view.request_state)

    def _apply_zoom_edit(self) -> None:
        widget = self.tabs.currentWidget()
        if not isinstance(widget, PdfReaderPane):
            return
        text = self.zoom_edit.text().strip().replace("%", "")
        try:
            percent = int(float(text))
        except Exception:
            return
        widget.view.set_scale_percent(percent)
        QTimer.singleShot(180, widget.view.request_state)

    def _nudge_zoom(self, delta: int) -> None:
        text = self.zoom_edit.text().strip().replace("%", "")
        try:
            current = int(float(text))
        except Exception:
            current = 100
        self.zoom_edit.setText(f"{max(45, min(current + delta, 350))}%")
        self._apply_zoom_edit()

    def _poll_view_state(self) -> None:
        widget = self.tabs.currentWidget()
        if isinstance(widget, PdfReaderPane):
            widget.view.request_state()

    def _update_view_state(self, payload: dict) -> None:
        page = int(payload.get("page", 0) or 0)
        total = int(payload.get("totalPages", 0) or 0)
        scale = int(payload.get("scalePercent", 100) or 100)
        fit_mode = str(payload.get("fitMode", "width"))
        page_spread = str(payload.get("pageSpread", "single"))
        self.page_edit.setText(str(page) if page else "")
        self.page_total_label.setText(f"/ {total}")
        self.zoom_edit.setText(f"{scale}%")
        if fit_mode in {"page", "width"} and fit_mode != self._fit_mode:
            self._fit_mode = fit_mode
        if page_spread in {"single", "double"}:
            self._page_spread = page_spread
        self.fit_toggle_action.setText("适应宽度" if self._fit_mode == "page" else "适应页面")
        self._apply_toolbar_icons()

    def _update_zoom_preview(self, percent: int) -> None:
        self.zoom_edit.setText(f"{int(percent)}%")

    def _rebuild_thumbnails(self, descriptor: DocumentDescriptor) -> None:
        self.thumbnail_list.clear()
        if fitz is None:
            return
        items: list[QListWidgetItem] = []
        try:
            doc = fitz.open(descriptor.path)
            for index in range(doc.page_count):
                page = doc.load_page(index)
                pix = page.get_pixmap(matrix=fitz.Matrix(0.18, 0.18), alpha=False)
                image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888).copy()
                item = QListWidgetItem(QIcon(QPixmap.fromImage(image)), str(index + 1))
                item.setData(Qt.ItemDataRole.UserRole, index + 1)
                items.append(item)
        except Exception:
            items = []
        self._thumbnail_cache[descriptor.document_id] = items
        for item in items:
            self.thumbnail_list.addItem(item)

    def _jump_from_thumbnail(self, item: QListWidgetItem) -> None:
        widget = self.tabs.currentWidget()
        if isinstance(widget, PdfReaderPane):
            widget.view.go_to_page(int(item.data(Qt.ItemDataRole.UserRole) or 1))
            QTimer.singleShot(180, widget.view.request_state)

    def _create_annotation(self, descriptor: DocumentDescriptor, payload: dict) -> None:
        record = AnnotationRecord(
            annotation_id=short_id("anno"),
            document_id=descriptor.document_id,
            kind=payload["kind"],
            color=ANNOTATION_COLORS[payload["kind"]],
            page=payload.get("page"),
            quote=payload.get("quote", ""),
            note=payload.get("note", ""),
            rects=payload.get("rects", []),
            created_at=now_iso(),
        )
        self.services.command_bus.execute(AddAnnotationCommand(self.services.annotation_store, record))
        self._refresh_side_panels()

    def _request_selection_translation(self, descriptor: DocumentDescriptor, payload: dict) -> None:
        text = str(payload.get("text", "")).strip()
        if not text:
            return
        self.right_tabs.setCurrentWidget(self.translation_panel)
        self.note_dock.show()
        self._right_sidebar_open = True
        self.translation_view.setHtml("<p style='color:#708195;'>正在翻译选中内容…</p>")
        self.translation_note_button.setEnabled(False)
        self.translation_hint_label.setText("正在翻译选中内容…")
        self.services.translate_selection(
            descriptor.document_id,
            text,
            lambda result, source=text, title=descriptor.title: self._show_translation_result(
                descriptor.document_id,
                f"《{title}》选中翻译",
                source,
                result,
            ),
            lambda message, source=text: self._show_translation_error("选中翻译失败", source, message),
        )

    def _translate_current_document(self) -> None:
        widget = self.tabs.currentWidget()
        if not widget:
            return
        document_id = getattr(widget, "document_id", "")
        payload = self._tab_payloads.get(document_id)
        if not payload:
            return
        snapshot = payload.get("snapshot")
        source_text = getattr(snapshot, "raw_text", "").strip() if snapshot else ""
        if not source_text:
            self.translation_view.setHtml("<p style='color:#708195;'>当前文档还没有可翻译的文本内容。</p>")
            self.right_tabs.setCurrentWidget(self.translation_panel)
            self.note_dock.show()
            self._right_sidebar_open = True
            self.translation_note_button.setEnabled(False)
            self.translation_hint_label.setText("当前文档暂无可翻译正文。")
            return
        descriptor = payload.get("descriptor")
        title = getattr(descriptor, "title", "当前文档")
        self.translation_view.setHtml("<p style='color:#708195;'>正在翻译全文，请稍候…</p>")
        self.right_tabs.setCurrentWidget(self.translation_panel)
        self.note_dock.show()
        self._right_sidebar_open = True
        self.translation_note_button.setEnabled(False)
        self.translation_hint_label.setText("全文翻译将在后台生成新文件并自动入库。")
        self.services.translate_document(
            document_id,
            source_text,
            self._show_document_translation_result,
            lambda message, source=source_text: self._show_translation_error("全文翻译失败", source, message),
        )

    def _show_translation_result(self, document_id: str, heading: str, source_text: str, translated_text: str) -> None:
        current = self.tabs.currentWidget()
        if current and getattr(current, "document_id", "") != document_id:
            return
        self._translation_payload = {
            "document_id": document_id,
            "heading": heading,
            "source": source_text,
            "translated": translated_text,
            "mode": "selection",
        }
        html = (
            f"<h3>{escape(heading)}</h3>"
            "<h4>原文</h4>"
            f"<pre style='white-space:pre-wrap;font-family:Microsoft YaHei UI;'>{escape(source_text)}</pre>"
            "<h4>译文</h4>"
            f"<pre style='white-space:pre-wrap;font-family:Microsoft YaHei UI;'>{escape(translated_text)}</pre>"
        )
        self.translation_view.setHtml(html)
        self.right_tabs.setCurrentWidget(self.translation_panel)
        self.translation_note_button.setEnabled(True)
        self.translation_hint_label.setText("可一键把这段译文转成当前文档的 Note 标注。")

    def _show_document_translation_result(self, payload: dict) -> None:
        title = str(payload.get("title", "全文翻译")).strip()
        output_path = str(payload.get("output_path", "")).strip()
        translated_text = str(payload.get("translated_text", "")).strip()
        self._translation_payload = {
            "document_id": str(payload.get("document_id", "")),
            "heading": title,
            "source": "",
            "translated": translated_text,
            "mode": "document",
            "output_path": output_path,
        }
        excerpt = translated_text[:1500] + ("…" if len(translated_text) > 1500 else "")
        self.translation_view.setHtml(
            f"<h3>{escape(title)}</h3>"
            "<p>全文翻译已在后台完成，并已自动生成新文件加入资料库。</p>"
            f"<p><b>路径：</b>{escape(output_path)}</p>"
            "<h4>译文预览</h4>"
            f"<pre style='white-space:pre-wrap;font-family:Microsoft YaHei UI;'>{escape(excerpt)}</pre>"
        )
        self.right_tabs.setCurrentWidget(self.translation_panel)
        self.translation_note_button.setEnabled(False)
        self.translation_hint_label.setText("全文翻译已生成独立文件；Note 转换仅用于选中翻译。")

    def _show_translation_error(self, heading: str, source_text: str, message: str) -> None:
        self._translation_payload = {}
        self.translation_view.setHtml(
            f"<h3>{escape(heading)}</h3>"
            f"<p style='color:#8c5656;'>{escape(message)}</p>"
            "<h4>原文</h4>"
            f"<pre style='white-space:pre-wrap;font-family:Microsoft YaHei UI;'>{escape(source_text)}</pre>"
        )
        self.right_tabs.setCurrentWidget(self.translation_panel)
        self.translation_note_button.setEnabled(False)
        self.translation_hint_label.setText("翻译失败时无法转为 Note。")

    def _translation_to_note(self) -> None:
        payload = dict(self._translation_payload)
        if payload.get("mode") != "selection":
            return
        widget = self.tabs.currentWidget()
        if not widget:
            return
        document_id = getattr(widget, "document_id", "")
        source_text = str(payload.get("source", "")).strip()
        translated_text = str(payload.get("translated", "")).strip()
        if not document_id or not translated_text:
            return
        descriptor = self._tab_payloads.get(document_id, {}).get("descriptor")
        if descriptor is None:
            return
        page = 0
        try:
            current_page = int(self.page_edit.text().strip())
            page = max(0, current_page - 1)
        except Exception:
            page = 0
        self._create_annotation(
            descriptor,
            {
                "kind": AnnotationKind.NOTE.value,
                "quote": source_text,
                "note": translated_text,
                "page": page,
                "rects": [],
            },
        )
        self.translation_hint_label.setText("已转为 Note 标注。")

    def _on_annotation_changed(self, document_id: str) -> None:
        current = self.tabs.currentWidget()
        if current and getattr(current, "document_id", "") == document_id:
            self._refresh_side_panels()

    def _refresh_side_panels(self) -> None:
        self.outline_tree.clear()
        self.annotation_list.clear()
        widget = self.tabs.currentWidget()
        if not widget:
            return
        document_id = getattr(widget, "document_id", "")
        payload = self._tab_payloads.get(document_id)
        if not payload:
            return
        if payload.get("loading"):
            self.outline_tree.addTopLevelItem(QTreeWidgetItem(["正在整理目录与阅读快照…"]))
            self.annotation_list.addItem("标注区域已就绪，目录快照正在后台加载。")
            return
        if payload.get("load_error"):
            self.outline_tree.addTopLevelItem(QTreeWidgetItem([f"目录加载失败：{payload['load_error']}"]))
            self.annotation_list.addItem("读取失败，请重新打开文档。")
            return
        snapshot = payload["snapshot"]
        for item in snapshot.outline:
            self._append_outline_item(self.outline_tree.invisibleRootItem(), item)
        annotations = self.services.annotation_store.list_for_document(document_id)
        for annotation in annotations:
            label = annotation.quote[:40] or annotation.note[:40] or annotation.kind
            self.annotation_list.addItem(f"[{annotation.kind}] {label}")
        if hasattr(widget, "apply_annotations"):
            widget.apply_annotations(annotations)

    def _annotation_record_for_current_row(self) -> AnnotationRecord | None:
        widget = self.tabs.currentWidget()
        if not widget:
            return None
        annotations = self.services.annotation_store.list_for_document(getattr(widget, "document_id", ""))
        row = self.annotation_list.currentRow()
        if row < 0 or row >= len(annotations):
            return None
        return annotations[row]

    def _open_annotation_menu(self, point) -> None:
        record = self._annotation_record_for_current_row()
        if not record:
            return
        menu = QMenu(self)
        edit_action = None
        if record.kind == AnnotationKind.NOTE.value:
            edit_action = menu.addAction("编辑Note内容")
        delete_action = menu.addAction("删除标注")
        chosen = menu.exec(self.annotation_list.mapToGlobal(point))
        if chosen is edit_action:
            self._edit_annotation_note(record)
            return
        if chosen is delete_action:
            self.services.command_bus.execute(RemoveAnnotationCommand(self.services.annotation_store, record))
            self._refresh_side_panels()

    def _edit_annotation_note(self, record: AnnotationRecord) -> None:
        text, accepted = QInputDialog.getMultiLineText(
            self,
            "编辑 Note 内容",
            "内容：",
            record.note,
        )
        if not accepted:
            return
        updated = AnnotationRecord(
            annotation_id=record.annotation_id,
            document_id=record.document_id,
            kind=record.kind,
            color=record.color,
            page=record.page,
            anchor=record.anchor,
            quote=record.quote,
            note=text,
            rects=list(record.rects),
            linked_note_id=record.linked_note_id,
            created_at=record.created_at,
        )
        self.services.command_bus.execute(UpdateAnnotationCommand(self.services.annotation_store, record, updated))
        self._refresh_side_panels()

    def _append_outline_item(self, parent, item) -> None:
        node = QTreeWidgetItem([item.title])
        node.setData(0, Qt.ItemDataRole.UserRole, item.page if item.page is not None else item.anchor)
        parent.addChild(node)
        for child in item.children:
            self._append_outline_item(node, child)

    def _jump_from_outline(self, item: QTreeWidgetItem) -> None:
        widget = self.tabs.currentWidget()
        if isinstance(widget, PdfReaderPane):
            page = item.data(0, Qt.ItemDataRole.UserRole)
            if isinstance(page, int):
                widget.view.go_to_page(page + 1)
                QTimer.singleShot(180, widget.view.request_state)

    def _jump_from_annotation(self, *_args) -> None:
        widget = self.tabs.currentWidget()
        if not widget:
            return
        annotations = self.services.annotation_store.list_for_document(getattr(widget, "document_id", ""))
        row = self.annotation_list.currentRow()
        if row < 0 or row >= len(annotations):
            return
        record = annotations[row]
        if isinstance(widget, PdfReaderPane):
            widget.jump_to_annotation(record)
        elif isinstance(widget, TextReaderPane):
            widget.jump_to_quote(record.quote)
