from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor, QTextCharFormat, QTextCursor, QTextDocument, QTextFormat
from PySide6.QtPdf import QPdfDocument, QPdfSearchModel
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
    QVBoxLayout,
    QWidget,
)

from markdown_it import MarkdownIt

from coyin.core.common import now_iso, short_id
from coyin.core.commands.annotation_commands import AddAnnotationCommand
from coyin.core.documents.models import (
    AnnotationKind,
    AnnotationRecord,
    DocumentDescriptor,
    DocumentKind,
    DocumentSnapshot,
)
from coyin.qt.widgets.detachable_tabs import DetachableTabWidget
from coyin.qt.widgets.pdf_view import SyncPdfView
from coyin.qt.widgets.theme import base_stylesheet


ANNOTATION_COLORS = {
    AnnotationKind.HIGHLIGHT.value: "#e2c48b",
    AnnotationKind.UNDERLINE.value: "#9fb6cb",
    AnnotationKind.NOTE.value: "#c6b28d",
}


class TextReaderPane(QWidget):
    annotationRequested = Signal(dict)

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

    def __init__(self, descriptor: DocumentDescriptor, snapshot: DocumentSnapshot):
        super().__init__()
        self.document_id = descriptor.document_id
        self.descriptor = descriptor
        self.snapshot = snapshot
        self.pdf_document = QPdfDocument(self)
        self.pdf_document.load(descriptor.path)
        self.search_model = QPdfSearchModel(self)
        self.search_model.setDocument(self.pdf_document)
        self.view = SyncPdfView()
        self.view.setDocument(self.pdf_document)
        self.view.setSearchModel(self.search_model)
        self.view.selectionReady.connect(self._open_selection_menu)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)

    def apply_snapshot(self, snapshot: DocumentSnapshot) -> None:
        self.snapshot = snapshot

    def _open_selection_menu(self, selected_text: str, page: int, rects: list, global_pos) -> None:
        menu = QMenu(self)
        for kind in (AnnotationKind.HIGHLIGHT.value, AnnotationKind.UNDERLINE.value, AnnotationKind.NOTE.value):
            action = menu.addAction(f"添加{kind}")
            action.triggered.connect(
                lambda checked=False, item=kind: self._emit_annotation(item, selected_text, page, rects)
            )
        menu.exec(global_pos)

    def _emit_annotation(self, kind: str, selected_text: str, page: int, rects: list) -> None:
        note = ""
        if kind == AnnotationKind.NOTE.value:
            note, accepted = QInputDialog.getText(self, "添加便签", "内容：")
            if not accepted:
                return
        self.annotationRequested.emit(
            {
                "kind": kind,
                "quote": selected_text,
                "page": page,
                "note": note,
                "rects": [{"x": rect.x(), "y": rect.y(), "w": rect.width(), "h": rect.height()} for rect in rects],
            }
        )

    def apply_annotations(self, annotations: list[AnnotationRecord]) -> None:
        page_to_rects: dict[int, list[tuple]] = {}
        for annotation in annotations:
            if annotation.page is None:
                continue
            page_to_rects.setdefault(annotation.page, [])
            for rect in annotation.rects:
                page_to_rects[annotation.page].append(
                    (
                        self._rect_from_dict(rect),
                        QColor(annotation.color),
                    )
                )
        self.view.set_annotation_rects(page_to_rects)

    def _rect_from_dict(self, rect: dict) -> object:
        from PySide6.QtCore import QRectF

        return QRectF(rect["x"], rect["y"], rect["w"], rect["h"])

    def search(self, term: str) -> None:
        self.search_model.setSearchString(term)
        self.view.setCurrentSearchResultIndex(0)

    def jump_to_annotation(self, record: AnnotationRecord) -> None:
        if record.page is None:
            return
        point = None
        if record.rects:
            first = record.rects[0]
            from PySide6.QtCore import QPointF

            point = QPointF(first["x"], first["y"])
        if point is None:
            from PySide6.QtCore import QPointF

            point = QPointF(0.0, 0.0)
        self.view.pageNavigator().jump(record.page, point, self.view.zoomFactor())


@dataclass(slots=True)
class ReaderServices:
    annotation_store: object
    command_bus: object
    workspace: object
    render_coordinator: object
    window_registry: object
    open_reader_document: object


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

        self.annotation_list = QListWidget()
        self.annotation_list.itemActivated.connect(self._jump_from_annotation)

        self._tab_payloads: dict[str, dict] = {}

        self._build_toolbar()
        self._build_docks()

        self.services.annotation_store.changed.connect(self._on_annotation_changed)

    def apply_theme(self, mode: str) -> None:
        self.theme_mode = mode
        self.setStyleSheet(base_stylesheet(mode))

    def _build_toolbar(self) -> None:
        toolbar = self.addToolBar("Reader")
        toolbar.setMovable(False)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索当前文档")
        self.search_edit.returnPressed.connect(self._search_current)
        fit_width = QAction("适配宽度", self)
        fit_width.triggered.connect(lambda: self._set_fit_mode("width"))
        fit_page = QAction("适配页面", self)
        fit_page.triggered.connect(lambda: self._set_fit_mode("page"))
        toolbar.addAction(fit_width)
        toolbar.addAction(fit_page)
        toolbar.addWidget(self.search_edit)

    def _build_docks(self) -> None:
        outline_dock = QDockWidget("目录", self)
        outline_dock.setWidget(self.outline_tree)
        outline_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, outline_dock)

        note_dock = QDockWidget("标注", self)
        note_dock.setWidget(self.annotation_list)
        note_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, note_dock)

    def closeEvent(self, event) -> None:
        self.services.window_registry.unregister(self.window_id)
        return super().closeEvent(event)

    def _empty_snapshot(self, descriptor: DocumentDescriptor) -> DocumentSnapshot:
        return DocumentSnapshot(document_id=descriptor.document_id, raw_text="", blocks=[], outline=[], page_count=0)

    def open_document(
        self,
        descriptor: DocumentDescriptor,
        snapshot: DocumentSnapshot | None,
        loading: bool = False,
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
        pane.document_id = descriptor.document_id
        pane.annotationRequested.connect(lambda payload, doc=descriptor: self._create_annotation(doc, payload))
        index = self.tabs.addTab(pane, descriptor.title)
        self.tabs.setCurrentIndex(index)
        self._tab_payloads[descriptor.document_id] = {
            "descriptor": descriptor,
            "snapshot": effective_snapshot,
            "loading": loading,
            "load_error": "",
        }
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
        self.tabs.removeTab(index)
        self.services.window_registry.detach_document(self.window_id, document_id)
        self.requestedDetach.emit(document_id)

    def _import_document(self, document_id: str) -> None:
        self.services.open_reader_document(document_id, target=self)

    def _close_tab(self, index: int) -> None:
        widget = self.tabs.widget(index)
        if widget:
            self.services.window_registry.detach_document(self.window_id, getattr(widget, "document_id", ""))
        self.tabs.removeTab(index)
        self._refresh_side_panels()

    def _search_current(self) -> None:
        widget = self.tabs.currentWidget()
        if widget and hasattr(widget, "search"):
            widget.search(self.search_edit.text().strip())

    def _set_fit_mode(self, mode: str) -> None:
        widget = self.tabs.currentWidget()
        if isinstance(widget, PdfReaderPane):
            widget.view.set_fit_mode(mode)

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
                from PySide6.QtCore import QPointF

                widget.view.pageNavigator().jump(page, QPointF(0, 0), widget.view.zoomFactor())

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
