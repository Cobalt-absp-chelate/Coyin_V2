from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QEvent, QPoint, QPointF, QRect, QRectF, Qt, Signal, QTimer
from PySide6.QtGui import QColor, QImage, QMouseEvent, QPainter, QPen, QPixmap, QWheelEvent
from PySide6.QtWidgets import QFrame, QGridLayout, QScrollArea, QVBoxLayout, QWidget

from coyin.core.documents.models import AnnotationRecord, AnnotationKind

try:
    import fitz  # type: ignore[import-untyped]
except Exception:  # pragma: no cover
    fitz = None


@dataclass(slots=True)
class _SearchHit:
    page_index: int
    rects: list[tuple[float, float, float, float]]


@dataclass(slots=True)
class _WordBox:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    order: int
    block_no: int
    line_no: int
    word_no: int


@dataclass(slots=True)
class _AnnotationOverlay:
    kind: str
    color: QColor
    rects: list[tuple[float, float, float, float]]


class _PdfPageWidget(QWidget):
    doubleClicked = Signal(int, float, float)
    selectionChanged = Signal(int, str, QPoint)

    def __init__(self, page_index: int, parent: QWidget | None = None):
        super().__init__(parent)
        self.page_index = page_index
        self._pixmap = QPixmap()
        self._render_scale = 1.0
        self._display_scale = 1.0
        self._highlight_rects: list[tuple[float, float, float, float]] = []
        self._annotation_overlays: list[_AnnotationOverlay] = []
        self._selection_rects: list[tuple[float, float, float, float]] = []
        self._selected_text = ""
        self._word_boxes: list[_WordBox] = []
        self._drag_origin: QPoint | None = None
        self._drag_current: QPoint | None = None
        self._anchor_word_index: int | None = None
        self._focus_word_index: int | None = None
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setMouseTracking(True)

    def set_page_pixmap(self, pixmap: QPixmap, render_scale: float) -> None:
        self._pixmap = pixmap
        self._render_scale = max(0.01, float(render_scale))
        self._display_scale = 1.0
        self._apply_size()
        self.update()

    def set_display_scale(self, display_scale: float) -> None:
        self._display_scale = max(0.2, float(display_scale))
        self._apply_size()
        self.update()

    def _apply_size(self) -> None:
        if self._pixmap.isNull():
            return
        self.setFixedSize(
            max(1, int(round(self._pixmap.width() * self._display_scale))),
            max(1, int(round(self._pixmap.height() * self._display_scale))),
        )

    def set_word_boxes(self, word_boxes: list[_WordBox]) -> None:
        self._word_boxes = list(word_boxes)

    def set_highlight_rects(self, rects: list[tuple[float, float, float, float]]) -> None:
        self._highlight_rects = list(rects)
        self.update()

    def set_annotation_overlays(self, overlays: list[_AnnotationOverlay]) -> None:
        self._annotation_overlays = list(overlays)
        self.update()

    def clear_highlights(self) -> None:
        self._highlight_rects = []
        self.update()

    def clear_selection(self) -> None:
        self._selection_rects = []
        self._selected_text = ""
        self._drag_origin = None
        self._drag_current = None
        self._anchor_word_index = None
        self._focus_word_index = None
        self.update()

    def selected_text(self) -> str:
        return self._selected_text

    def _effective_scale(self) -> float:
        return self._render_scale * self._display_scale

    def _point_to_pdf(self, point: QPoint) -> QPointF:
        effective = max(0.0001, self._effective_scale())
        return QPointF(point.x() / effective, point.y() / effective)

    def _nearest_word_index(self, point: QPoint) -> int | None:
        if not self._word_boxes:
            return None
        pdf_point = self._point_to_pdf(point)
        best_index = None
        best_score = None
        for index, word in enumerate(self._word_boxes):
            rect = QRectF(word.x0, word.y0, word.x1 - word.x0, word.y1 - word.y0)
            if rect.contains(pdf_point):
                return index
            dx = 0.0
            if pdf_point.x() < rect.left():
                dx = rect.left() - pdf_point.x()
            elif pdf_point.x() > rect.right():
                dx = pdf_point.x() - rect.right()
            dy = 0.0
            if pdf_point.y() < rect.top():
                dy = rect.top() - pdf_point.y()
            elif pdf_point.y() > rect.bottom():
                dy = pdf_point.y() - rect.bottom()
            score = dx * dx + dy * dy * 1.6
            if best_score is None or score < best_score:
                best_score = score
                best_index = index
        return best_index

    def _update_selection_from_drag(self) -> None:
        if self._anchor_word_index is None or self._focus_word_index is None:
            return
        start = min(self._anchor_word_index, self._focus_word_index)
        end = max(self._anchor_word_index, self._focus_word_index)
        picked = self._word_boxes[start : end + 1]
        self._selection_rects = [(word.x0, word.y0, word.x1, word.y1) for word in picked]
        self._selected_text = " ".join(word.text for word in picked).strip()
        self.update()

    def paintEvent(self, event) -> None:  # noqa: ANN001
        _ = event
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#ffffff"))
        if not self._pixmap.isNull():
            painter.drawPixmap(self.rect(), self._pixmap)

        if self._annotation_overlays:
            for overlay in self._annotation_overlays:
                if overlay.kind == AnnotationKind.UNDERLINE.value:
                    pen = QPen(overlay.color)
                    pen.setWidth(3)
                    painter.setPen(pen)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    for x0, y0, x1, y1 in overlay.rects:
                        left = int(x0 * self._effective_scale())
                        right = int(x1 * self._effective_scale())
                        baseline = int(y1 * self._effective_scale()) - 2
                        painter.drawLine(left, baseline, right, baseline)
                else:
                    painter.setPen(Qt.PenStyle.NoPen)
                    color = QColor(overlay.color)
                    color.setAlpha(110 if overlay.kind == AnnotationKind.HIGHLIGHT.value else 85)
                    painter.setBrush(color)
                    for x0, y0, x1, y1 in overlay.rects:
                        painter.drawRect(
                            int(x0 * self._effective_scale()),
                            int(y0 * self._effective_scale()),
                            max(1, int((x1 - x0) * self._effective_scale())),
                            max(1, int((y1 - y0) * self._effective_scale())),
                        )

        if self._highlight_rects:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(242, 220, 165, 120))
            for x0, y0, x1, y1 in self._highlight_rects:
                painter.drawRect(
                    int(x0 * self._effective_scale()),
                    int(y0 * self._effective_scale()),
                    max(1, int((x1 - x0) * self._effective_scale())),
                    max(1, int((y1 - y0) * self._effective_scale())),
                )

        if self._selection_rects:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(210, 198, 160, 150))
            for x0, y0, x1, y1 in self._selection_rects:
                painter.drawRect(
                    int(x0 * self._effective_scale()),
                    int(y0 * self._effective_scale()),
                    max(1, int((x1 - x0) * self._effective_scale())),
                    max(1, int((y1 - y0) * self._effective_scale())),
                )

        if self._drag_origin is not None and self._drag_current is not None:
            selection_pen = QPen(QColor("#88a6c1"))
            selection_pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(selection_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRect(self._drag_origin, self._drag_current).normalized())

        border = QPen(QColor("#d5dde8"))
        border.setWidth(1)
        painter.setPen(border)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        painter.end()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        position = event.position()
        pdf_x = float(position.x()) / self._effective_scale()
        pdf_y = float(position.y()) / self._effective_scale()
        self.doubleClicked.emit(self.page_index + 1, pdf_x, pdf_y)
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_origin = event.position().toPoint()
            self._drag_current = self._drag_origin
            self._selection_rects = []
            self._selected_text = ""
            self._anchor_word_index = self._nearest_word_index(self._drag_origin)
            self._focus_word_index = self._anchor_word_index
            self._update_selection_from_drag()
            self.update()
        elif event.button() == Qt.MouseButton.RightButton and self._selected_text:
            self.selectionChanged.emit(self.page_index, self._selected_text, event.globalPosition().toPoint())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_origin is not None and (event.buttons() & Qt.MouseButton.LeftButton):
            self._drag_current = event.position().toPoint()
            self._focus_word_index = self._nearest_word_index(self._drag_current)
            self._update_selection_from_drag()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._drag_origin is not None:
            self._drag_current = event.position().toPoint()
            self._focus_word_index = self._nearest_word_index(self._drag_current)
            self._update_selection_from_drag()
            self._drag_origin = None
            self._drag_current = None
            self._anchor_word_index = None
            self._focus_word_index = None
            self.update()
        super().mouseReleaseEvent(event)


class QuickPdfView(QWidget):
    selectionContextMenuRequested = Signal(str, QPoint)
    documentLoadChanged = Signal(bool)
    stateChanged = Signal(dict)
    zoomPreviewChanged = Signal(int)
    inverseSyncRequested = Signal(int, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._doc = None
        self._pdf_path = ""
        self._theme_mode = "light"
        self._fit_mode = "width"
        self._page_spread = "single"
        self._scale = 1.0
        self._target_scale = 1.0
        self._page_sizes: list[tuple[float, float]] = []
        self._page_widgets: list[_PdfPageWidget] = []
        self._page_word_boxes: list[list[_WordBox]] = []
        self._annotation_by_page: dict[int, list[_AnnotationOverlay]] = {}
        self._search_hits: list[_SearchHit] = []
        self._search_index = -1
        self._last_state: dict = {
            "page": 0,
            "totalPages": 0,
            "scalePercent": 100,
            "fitMode": "width",
            "pageSpread": "single",
        }

        self.setAutoFillBackground(True)
        self.setStyleSheet("background: #eef2f6;")

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.viewport().installEventFilter(self)
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.request_state)
        self.scroll_area.horizontalScrollBar().valueChanged.connect(self.request_state)

        self.content = QWidget()
        self.scroll_area.setWidget(self.content)
        self._layout: QVBoxLayout | QGridLayout | None = None
        self._rebuild_layout()

        self._rerender_timer = QTimer(self)
        self._rerender_timer.setSingleShot(True)
        self._rerender_timer.setInterval(120)
        self._rerender_timer.timeout.connect(self._commit_pending_rerender)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self.scroll_area)

    def _rebuild_layout(self) -> None:
        if self._layout is not None:
            while self._layout.count():
                item = self._layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
            QWidget().setLayout(self._layout)
        if self._page_spread == "double":
            layout = QGridLayout()
            layout.setContentsMargins(14, 14, 14, 14)
            layout.setHorizontalSpacing(16)
            layout.setVerticalSpacing(10)
        else:
            layout = QVBoxLayout()
            layout.setContentsMargins(14, 14, 14, 14)
            layout.setSpacing(10)
        self.content.setLayout(layout)
        self._layout = layout
        for index, widget in enumerate(self._page_widgets):
            self._add_page_widget(widget, index)

    def _add_page_widget(self, widget: _PdfPageWidget, index: int) -> None:
        if isinstance(self._layout, QGridLayout):
            self._layout.addWidget(widget, index // 2, index % 2, alignment=Qt.AlignmentFlag.AlignTop)
        else:
            self._layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

    def _clear_pages(self) -> None:
        self._page_widgets = []
        self._page_sizes = []
        self._page_word_boxes = []
        self._annotation_by_page = {}
        self._search_hits = []
        self._search_index = -1
        self._rebuild_layout()

    def _render_page_pixmap(self, page_index: int) -> QPixmap:
        page = self._doc.load_page(page_index)
        pix = page.get_pixmap(matrix=fitz.Matrix(self._scale, self._scale), alpha=False)
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888).copy()
        return QPixmap.fromImage(image)

    def _rerender_pages(self) -> None:
        if self._doc is None:
            return
        for index, widget in enumerate(self._page_widgets):
            widget.set_page_pixmap(self._render_page_pixmap(index), self._scale)
            if index < len(self._page_word_boxes):
                widget.set_word_boxes(self._page_word_boxes[index])
            widget.set_annotation_overlays(self._annotation_by_page.get(index, []))
        self._apply_search_highlights()
        self.request_state()

    def _apply_preview_scale(self, target_scale: float) -> None:
        if self._doc is None:
            return
        preview_ratio = max(0.2, float(target_scale) / max(0.0001, self._scale))
        for widget in self._page_widgets:
            widget.set_display_scale(preview_ratio)
        self.zoomPreviewChanged.emit(int(round(target_scale * 100)))

    def _commit_pending_rerender(self) -> None:
        if self._doc is None:
            return
        self._scale = self._target_scale
        self._rerender_pages()

    def _fit_scale(self, mode: str) -> float:
        if not self._page_sizes:
            return 1.0
        max_width = max(width for width, _ in self._page_sizes)
        max_height = max(height for _, height in self._page_sizes)
        available_width = max(1, self.scroll_area.viewport().width() - 28)
        available_height = max(1, self.scroll_area.viewport().height() - 28)
        pages_per_row = 2 if self._page_spread == "double" else 1
        spread_width = max_width * pages_per_row + (pages_per_row - 1) * 16
        if mode == "page":
            return max(0.25, min(4.0, min(available_width / spread_width, available_height / max_height)))
        return max(0.25, min(4.0, available_width / spread_width))

    def _emit_state(self) -> None:
        self._last_state = {
            "page": self.current_page(),
            "totalPages": len(self._page_widgets),
            "scalePercent": int(round(self._target_scale * 100)),
            "fitMode": self._fit_mode,
            "pageSpread": self._page_spread,
        }
        self.zoomPreviewChanged.emit(self._last_state["scalePercent"])
        self.stateChanged.emit(dict(self._last_state))

    def _page_widget_at_viewport_center(self) -> int:
        if not self._page_widgets:
            return 0
        viewport_center = self.scroll_area.viewport().rect().center()
        global_center = self.scroll_area.viewport().mapToGlobal(viewport_center)
        content_point = self.content.mapFromGlobal(global_center)
        best_index = 0
        best_score = None
        for index, widget in enumerate(self._page_widgets):
            rect = widget.geometry()
            if rect.contains(content_point):
                return index + 1
            center = rect.center()
            dx = center.x() - content_point.x()
            dy = center.y() - content_point.y()
            score = dx * dx + dy * dy
            if best_score is None or score < best_score:
                best_score = score
                best_index = index
        return best_index + 1

    def _apply_search_highlights(self) -> None:
        for widget in self._page_widgets:
            widget.clear_highlights()
        if 0 <= self._search_index < len(self._search_hits):
            hit = self._search_hits[self._search_index]
            self._page_widgets[hit.page_index].set_highlight_rects(hit.rects)

    def open_pdf(self, pdf_path: str) -> None:
        self.clear_document()
        if fitz is None:
            self.documentLoadChanged.emit(False)
            return
        try:
            self._pdf_path = str(Path(pdf_path))
            self._doc = fitz.open(self._pdf_path)
            self._page_sizes = [(float(page.rect.width), float(page.rect.height)) for page in self._doc]
            self._page_word_boxes = []
            self._page_widgets = []
            for index, _size in enumerate(self._page_sizes):
                page = self._doc.load_page(index)
                words = page.get_text("words")
                word_boxes = [
                    _WordBox(
                        x0=float(word[0]),
                        y0=float(word[1]),
                        x1=float(word[2]),
                        y1=float(word[3]),
                        text=str(word[4]),
                        order=order,
                        block_no=int(word[5]) if len(word) > 5 else 0,
                        line_no=int(word[6]) if len(word) > 6 else 0,
                        word_no=int(word[7]) if len(word) > 7 else order,
                    )
                    for order, word in enumerate(words)
                    if len(word) >= 5 and str(word[4]).strip()
                ]
                self._page_word_boxes.append(word_boxes)
                widget = _PdfPageWidget(index)
                widget.doubleClicked.connect(self.inverseSyncRequested)
                widget.selectionChanged.connect(self._emit_selection_context_menu)
                self._page_widgets.append(widget)
            self._rebuild_layout()
            self._scale = self._fit_scale(self._fit_mode)
            self._target_scale = self._scale
            self._rerender_pages()
            self.documentLoadChanged.emit(True)
        except Exception:
            self.clear_document()
            self.documentLoadChanged.emit(False)

    def clear_document(self) -> None:
        if self._doc is not None:
            try:
                self._doc.close()
            except Exception:
                pass
        self._doc = None
        self._pdf_path = ""
        self._scale = 1.0
        self._target_scale = 1.0
        self._clear_pages()
        self._emit_state()

    def request_state(self) -> None:
        self._emit_state()

    def set_theme(self, mode: str) -> None:
        self._theme_mode = "dark" if mode == "dark" else "light"
        self.setStyleSheet("background: #141b24;" if self._theme_mode == "dark" else "background: #eef2f6;")

    def set_scale_mode(self, mode: str) -> None:
        self._fit_mode = "page" if mode == "page" else "width"
        if self._doc is not None:
            self._target_scale = self._fit_scale(self._fit_mode)
            self._scale = self._target_scale
            self._rerender_pages()

    def set_scale_percent(self, percent: int) -> None:
        self._fit_mode = "custom"
        self._target_scale = max(0.25, min(4.0, int(percent) / 100.0))
        if self._doc is not None:
            self._scale = self._target_scale
            self._rerender_pages()

    def set_page_spread(self, mode: str) -> None:
        self._page_spread = "double" if mode == "double" else "single"
        self._rebuild_layout()
        if self._doc is not None and self._fit_mode != "custom":
            self._target_scale = self._fit_scale(self._fit_mode)
        if self._doc is not None:
            self._scale = self._target_scale
            self._rerender_pages()

    def page_spread(self) -> str:
        return self._page_spread

    def go_to_page(self, page_number: int) -> None:
        self.go_to_page_index(int(page_number) - 1)

    def go_to_page_index(self, page_index: int) -> None:
        if 0 <= page_index < len(self._page_widgets):
            self.scroll_area.ensureWidgetVisible(self._page_widgets[page_index], 20, 20)
            self.request_state()

    def go_to_location_index(self, page_index: int, x: float, y: float, zoom: float = 0.0) -> None:
        if not (0 <= page_index < len(self._page_widgets)):
            return
        if zoom > 0:
            self._fit_mode = "custom"
            self._target_scale = max(0.25, min(4.0, float(zoom)))
            self._scale = self._target_scale
            self._rerender_pages()
        widget = self._page_widgets[page_index]
        self.scroll_area.ensureWidgetVisible(widget, 20, 20)
        self.scroll_area.horizontalScrollBar().setValue(
            max(0, widget.x() + int(float(x) * self._scale) - self.scroll_area.viewport().width() // 2)
        )
        self.scroll_area.verticalScrollBar().setValue(
            max(0, widget.y() + int(float(y) * self._scale) - self.scroll_area.viewport().height() // 2)
        )
        self.request_state()

    def search(self, term: str) -> None:
        self._search_hits = []
        self._search_index = -1
        if self._doc is None or not term.strip():
            self._apply_search_highlights()
            self.request_state()
            return
        for page_index, page in enumerate(self._doc):
            rects = page.search_for(term)
            if rects:
                self._search_hits.append(
                    _SearchHit(
                        page_index=page_index,
                        rects=[(rect.x0, rect.y0, rect.x1, rect.y1) for rect in rects],
                    )
                )
        if self._search_hits:
            self._search_index = 0
            first = self._search_hits[0]
            self.go_to_location_index(first.page_index, first.rects[0][0], first.rects[0][1], 0.0)
        self._apply_search_highlights()
        self.request_state()

    def set_annotations(self, annotations: list[AnnotationRecord]) -> None:
        self._annotation_by_page = {}
        if not annotations or not self._page_word_boxes:
            for widget in self._page_widgets:
                widget.set_annotation_overlays([])
            return
        for annotation in annotations:
            page = annotation.page
            quote = " ".join((annotation.quote or "").split())
            if page is None or page < 0 or page >= len(self._page_word_boxes) or not quote:
                continue
            rects = self._match_quote_rects(self._page_word_boxes[page], quote)
            if not rects:
                continue
            overlay = _AnnotationOverlay(kind=annotation.kind, color=QColor(annotation.color), rects=rects)
            self._annotation_by_page.setdefault(page, []).append(overlay)
        for index, widget in enumerate(self._page_widgets):
            widget.set_annotation_overlays(self._annotation_by_page.get(index, []))

    def _match_quote_rects(self, word_boxes: list[_WordBox], quote: str) -> list[tuple[float, float, float, float]]:
        target = [part.lower() for part in quote.split() if part.strip()]
        if not target:
            return []
        lowered = [word.text.lower() for word in word_boxes]
        window = len(target)
        for start in range(0, max(0, len(word_boxes) - window + 1)):
            if lowered[start : start + window] == target:
                return [(word.x0, word.y0, word.x1, word.y1) for word in word_boxes[start : start + window]]
        return []

    def current_page(self) -> int:
        return self._page_widget_at_viewport_center()

    def zoom_percent(self) -> int:
        return int(round(self._target_scale * 100))

    def _emit_selection_context_menu(self, page_index: int, text: str, global_pos: QPoint) -> None:
        _ = page_index
        if text.strip():
            self.selectionContextMenuRequested.emit(text, global_pos)

    def eventFilter(self, watched: object, event: QEvent) -> bool:
        if watched is self.scroll_area.viewport() and isinstance(event, QWheelEvent):
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                old_scale = max(self._target_scale, 0.0001)
                target_scale = max(0.25, min(4.0, old_scale * (1.12 if event.angleDelta().y() > 0 else 1 / 1.12)))
                if abs(target_scale - old_scale) < 0.0001:
                    return True
                anchor = event.position().toPoint()
                content_x = self.scroll_area.horizontalScrollBar().value() + anchor.x()
                content_y = self.scroll_area.verticalScrollBar().value() + anchor.y()
                ratio = target_scale / old_scale
                self._fit_mode = "custom"
                self._target_scale = target_scale
                self._apply_preview_scale(target_scale)
                self.scroll_area.horizontalScrollBar().setValue(int(content_x * ratio - anchor.x()))
                self.scroll_area.verticalScrollBar().setValue(int(content_y * ratio - anchor.y()))
                self._rerender_timer.start()
                self.request_state()
                return True
        return super().eventFilter(watched, event)
