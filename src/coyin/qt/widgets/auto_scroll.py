from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPropertyAnimation, Qt, QTimer
from PySide6.QtWidgets import QAbstractScrollArea, QGraphicsOpacityEffect, QScrollBar


class _AutoHideBar(QObject):
    def __init__(self, area: QAbstractScrollArea, bar: QScrollBar, orientation: Qt.Orientation):
        super().__init__(area)
        self.area = area
        self.bar = bar
        self.orientation = orientation
        self._opacity = QGraphicsOpacityEffect(bar)
        self._opacity.setOpacity(0.0)
        self.bar.setGraphicsEffect(self._opacity)
        self._animation = QPropertyAnimation(self._opacity, b"opacity", self)
        self._animation.setDuration(180)
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(760)
        self._hide_timer.timeout.connect(self.hide_bar)
        self.bar.installEventFilter(self)
        self.area.viewport().installEventFilter(self)
        self.bar.valueChanged.connect(self.show_temporarily)
        self.bar.rangeChanged.connect(self._sync_visibility)
        self.bar.sliderPressed.connect(self.show_bar)
        self.bar.sliderReleased.connect(self.show_temporarily)
        self._sync_visibility()

    def _scroll_needed(self) -> bool:
        return self.bar.maximum() > self.bar.minimum()

    def _animate_to(self, value: float) -> None:
        self._animation.stop()
        self._animation.setStartValue(self._opacity.opacity())
        self._animation.setEndValue(value)
        self._animation.start()

    def _sync_visibility(self) -> None:
        needed = self._scroll_needed()
        self.bar.setVisible(needed)
        if not needed:
            self._hide_timer.stop()
            self._opacity.setOpacity(0.0)

    def _near_bar_edge(self, event) -> bool:
        position = event.position().toPoint() if hasattr(event, "position") else event.pos()
        rect = self.area.viewport().rect()
        margin = 18
        if self.orientation == Qt.Orientation.Vertical:
            return position.x() >= rect.right() - margin
        return position.y() >= rect.bottom() - margin

    def show_bar(self) -> None:
        if not self._scroll_needed():
            return
        self._hide_timer.stop()
        self._animate_to(1.0)

    def show_temporarily(self, *_args) -> None:
        if not self._scroll_needed():
            return
        self.show_bar()
        self._hide_timer.start()

    def hide_bar(self) -> None:
        if not self._scroll_needed():
            return
        if self.bar.underMouse():
            self._hide_timer.start()
            return
        self._animate_to(0.0)

    def eventFilter(self, watched, event) -> bool:
        if watched is self.bar:
            if event.type() in {QEvent.Type.Enter, QEvent.Type.HoverEnter, QEvent.Type.MouseMove, QEvent.Type.HoverMove}:
                self.show_bar()
            elif event.type() in {QEvent.Type.Leave, QEvent.Type.HoverLeave}:
                self._hide_timer.start()
            return False

        if watched is self.area.viewport():
            if event.type() in {QEvent.Type.Wheel, QEvent.Type.MouseButtonPress}:
                self.show_temporarily()
            elif event.type() == QEvent.Type.MouseMove:
                if self._near_bar_edge(event):
                    self.show_bar()
                else:
                    self._hide_timer.start()
            elif event.type() == QEvent.Type.Leave:
                self._hide_timer.start()
        return False


class AutoHideScrollbars(QObject):
    def __init__(self, area: QAbstractScrollArea):
        super().__init__(area)
        self.area = area
        self._bars = [
            _AutoHideBar(area, area.verticalScrollBar(), Qt.Orientation.Vertical),
            _AutoHideBar(area, area.horizontalScrollBar(), Qt.Orientation.Horizontal),
        ]


def install_auto_hide_scrollbars(area: QAbstractScrollArea) -> AutoHideScrollbars:
    helper = getattr(area, "_coyin_auto_hide_scrollbars", None)
    if helper is None:
        helper = AutoHideScrollbars(area)
        setattr(area, "_coyin_auto_hide_scrollbars", helper)
    return helper
