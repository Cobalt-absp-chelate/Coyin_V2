from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QPolygonF
from PySide6.QtPdf import QPdfDocument, QPdfSelection
from PySide6.QtPdfWidgets import QPdfView


@dataclass(slots=True)
class PageLocation:
    page: int
    point: QPointF


class SyncPdfView(QPdfView):
    selectionReady = Signal(str, int, list, QPoint)
    inverseSyncRequested = Signal(int, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPageMode(QPdfView.PageMode.MultiPage)
        self.setPageSpacing(12)
        self.setZoomMode(QPdfView.ZoomMode.Custom)
        self._fit_mode = "width"
        self._drag_start: QPoint | None = None
        self._drag_end: QPoint | None = None
        self._selection_page: int | None = None
        self._selection: QPdfSelection | None = None
        self._annotation_rects: dict[int, list[tuple[QRectF, QColor]]] = {}

    def set_fit_mode(self, fit_mode: str) -> None:
        self._fit_mode = fit_mode
        self.recompute_zoom()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.recompute_zoom()

    def recompute_zoom(self) -> None:
        document = self.document()
        if not isinstance(document, QPdfDocument) or document.pageCount() == 0:
            return
        max_width = max(document.pagePointSize(index).width() for index in range(document.pageCount()))
        max_height = max(document.pagePointSize(index).height() for index in range(document.pageCount()))
        if max_width <= 0 or max_height <= 0:
            return
        viewport_rect = self.viewport().rect()
        if self._fit_mode == "page":
            zoom = min((viewport_rect.width() - 24) / max_width, (viewport_rect.height() - 24) / max_height)
        else:
            zoom = (viewport_rect.width() - 36) / max_width
        self.setZoomFactor(max(0.35, min(zoom, 3.0)))

    def set_annotation_rects(self, page_to_rects: dict[int, list[tuple[QRectF, QColor]]]) -> None:
        self._annotation_rects = page_to_rects
        self.viewport().update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.position().toPoint()
            self._drag_end = None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_start is not None and (event.buttons() & Qt.MouseButton.LeftButton):
            self._drag_end = event.position().toPoint()
            self.viewport().update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._drag_start is not None and self._drag_end is not None:
            start = self._view_to_pdf(self._drag_start)
            end = self._view_to_pdf(self._drag_end)
            if start and end and start.page == end.page:
                selection = self.document().getSelection(start.page, start.point, end.point)
                if selection.isValid() and selection.text().strip():
                    self._selection = selection
                    self._selection_page = start.page
                    rects = [polygon.boundingRect() for polygon in selection.bounds()]
                    self.selectionReady.emit(selection.text(), start.page, rects, event.globalPosition().toPoint())
            self._drag_start = None
            self._drag_end = None
            self.viewport().update()
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        location = self._view_to_pdf(event.position().toPoint())
        if location:
            self.inverseSyncRequested.emit(location.page + 1, location.point.x(), location.point.y())
        super().mouseDoubleClickEvent(event)

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        for page, entries in self._annotation_rects.items():
            for rect, color in entries:
                view_rect = self._pdf_rect_to_view(page, rect)
                if not view_rect.isValid():
                    continue
                painter.fillRect(view_rect, QColor(color).lighter(130))
                pen = QPen(QColor(color).darker(110))
                pen.setWidthF(1.2)
                painter.setPen(pen)
                painter.drawRect(view_rect)
        if self._selection and self._selection_page is not None:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(210, 184, 140, 100))
            for polygon in self._selection.bounds():
                view_poly = QPolygonF([self._pdf_point_to_view(self._selection_page, point) for point in polygon])
                painter.drawPolygon(view_poly)
        painter.end()

    def _content_layout_rect(self, page: int) -> QRectF:
        document = self.document()
        size = document.pagePointSize(page)
        zoom = self.zoomFactor()
        page_width = size.width() * zoom
        page_height = size.height() * zoom
        y = 12.0
        for index in range(page):
            previous = document.pagePointSize(index)
            y += previous.height() * zoom + self.pageSpacing()
        x = max(12.0, (self.viewport().width() - page_width) / 2) + self.horizontalScrollBar().value()
        y += self.verticalScrollBar().value()
        return QRectF(x, y, page_width, page_height)

    def _view_to_pdf(self, point: QPoint) -> PageLocation | None:
        document = self.document()
        if not isinstance(document, QPdfDocument):
            return None
        content_point = QPointF(
            point.x() + self.horizontalScrollBar().value(),
            point.y() + self.verticalScrollBar().value(),
        )
        for page in range(document.pageCount()):
            rect = self._content_layout_rect(page)
            if rect.contains(content_point):
                local = content_point - rect.topLeft()
                return PageLocation(page=page, point=QPointF(local.x() / self.zoomFactor(), local.y() / self.zoomFactor()))
        return None

    def _pdf_point_to_view(self, page: int, point: QPointF) -> QPointF:
        rect = self._content_layout_rect(page)
        content_point = QPointF(rect.left() + point.x() * self.zoomFactor(), rect.top() + point.y() * self.zoomFactor())
        return QPointF(
            content_point.x() - self.horizontalScrollBar().value(),
            content_point.y() - self.verticalScrollBar().value(),
        )

    def _pdf_rect_to_view(self, page: int, rect: QRectF) -> QRectF:
        top_left = self._pdf_point_to_view(page, rect.topLeft())
        size = rect.size() * self.zoomFactor()
        return QRectF(top_left, size)
