from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, Qt, QEvent, Signal
from PySide6.QtGui import QColor, QImage, QMouseEvent, QPainter, QPen, QPixmap, QWheelEvent
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

try:
    import fitz  # type: ignore[import-untyped]
except Exception:  # pragma: no cover
    fitz = None


@dataclass(slots=True)
class _SearchHit:
    page_index: int
    rects: list[tuple[float, float, float, float]]


class _PdfPageWidget(QWidget):
    doubleClicked = Signal(int, float, float)

    def __init__(self, page_index: int, parent: QWidget | None = None):
        super().__init__(parent)
        self.page_index = page_index
        self._pixmap = QPixmap()
        self._scale = 1.0
        self._page_width_points = 1.0
        self._page_height_points = 1.0
        self._highlight_rects: list[tuple[float, float, float, float]] = []
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

    def set_page_pixmap(
        self,
        pixmap: QPixmap,
        scale: float,
        page_width_points: float,
        page_height_points: float,
    ) -> None:
        self._pixmap = pixmap
        self._scale = max(0.01, float(scale))
        self._page_width_points = max(1.0, float(page_width_points))
        self._page_height_points = max(1.0, float(page_height_points))
        self.setFixedSize(self._pixmap.size())
        self.update()

    def set_highlight_rects(self, rects: list[tuple[float, float, float, float]]) -> None:
        self._highlight_rects = list(rects)
        self.update()

    def clear_highlights(self) -> None:
        self._highlight_rects = []
        self.update()

    def paintEvent(self, event) -> None:  # noqa: ANN001
        _ = event
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#ffffff"))
        if not self._pixmap.isNull():
            painter.drawPixmap(0, 0, self._pixmap)
        if self._highlight_rects:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(242, 220, 165, 120))
            for x0, y0, x1, y1 in self._highlight_rects:
                painter.drawRect(
                    int(x0 * self._scale),
                    int(y0 * self._scale),
                    max(1, int((x1 - x0) * self._scale)),
                    max(1, int((y1 - y0) * self._scale)),
                )
        border = QPen(QColor("#d5dde8"))
        border.setWidth(1)
        painter.setPen(border)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))
        painter.end()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        position = event.position()
        pdf_x = float(position.x()) / self._scale
        pdf_y = float(position.y()) / self._scale
        self.doubleClicked.emit(self.page_index + 1, pdf_x, pdf_y)
        super().mouseDoubleClickEvent(event)


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
        self._page_sizes: list[tuple[float, float]] = []
        self._page_widgets: list[_PdfPageWidget] = []
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
            width_points, height_points = self._page_sizes[index]
            widget.set_page_pixmap(
                self._render_page_pixmap(index),
                self._scale,
                width_points,
                height_points,
            )
        self._apply_search_highlights()
        self.request_state()

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
            "scalePercent": self.zoom_percent(),
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
            self._page_widgets = []
            for index, (width_points, height_points) in enumerate(self._page_sizes):
                widget = _PdfPageWidget(index)
                widget.doubleClicked.connect(self.inverseSyncRequested)
                self._page_widgets.append(widget)
            self._rebuild_layout()
            self._scale = self._fit_scale(self._fit_mode)
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
            self._scale = self._fit_scale(self._fit_mode)
            self._rerender_pages()

    def set_scale_percent(self, percent: int) -> None:
        self._fit_mode = "custom"
        self._scale = max(0.25, min(4.0, int(percent) / 100.0))
        if self._doc is not None:
            self._rerender_pages()

    def set_page_spread(self, mode: str) -> None:
        self._page_spread = "double" if mode == "double" else "single"
        self._rebuild_layout()
        if self._doc is not None and self._fit_mode != "custom":
            self._scale = self._fit_scale(self._fit_mode)
        if self._doc is not None:
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
            self._scale = max(0.25, min(4.0, float(zoom)))
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

    def current_page(self) -> int:
        return self._page_widget_at_viewport_center()

    def zoom_percent(self) -> int:
        return int(round(self._scale * 100))

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self.scroll_area.viewport() and isinstance(event, QWheelEvent):
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                old_scale = max(self._scale, 0.0001)
                target_scale = max(0.25, min(4.0, old_scale * (1.12 if event.angleDelta().y() > 0 else 1 / 1.12)))
                if abs(target_scale - old_scale) < 0.0001:
                    return True
                anchor = event.position().toPoint()
                content_x = self.scroll_area.horizontalScrollBar().value() + anchor.x()
                content_y = self.scroll_area.verticalScrollBar().value() + anchor.y()
                ratio = target_scale / old_scale
                self._fit_mode = "custom"
                self._scale = target_scale
                self._rerender_pages()
                self.scroll_area.horizontalScrollBar().setValue(int(content_x * ratio - anchor.x()))
                self.scroll_area.verticalScrollBar().setValue(int(content_y * ratio - anchor.y()))
                self.request_state()
                return True
        return super().eventFilter(watched, event)
