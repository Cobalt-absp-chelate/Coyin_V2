from __future__ import annotations

from PySide6.QtCore import QEasingCurve, Property, QElapsedTimer, QTimer, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtQml import qmlRegisterType
from PySide6.QtQuick import QQuickPaintedItem


class SignalAccentItem(QQuickPaintedItem):
    activeChanged = Signal()
    hoveredChanged = Signal()
    pressedChanged = Signal()
    accentColorChanged = Signal()
    neutralColorChanged = Signal()
    edgeChanged = Signal()
    radiusChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAntialiasing(True)
        self._active = False
        self._hovered = False
        self._pressed = False
        self._edge = "left"
        self._radius = 6.0
        self._accent = QColor("#1f5a84")
        self._neutral = QColor("#dbe8f3")
        self._progress = 0.0
        self._from_progress = 0.0
        self._to_progress = 0.0
        self._duration_ms = 220
        self._curve = QEasingCurve(QEasingCurve.Type.InOutCubic)
        self._clock = QElapsedTimer()
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick_animation)

    def _tick_animation(self) -> None:
        if not self._clock.isValid():
            self._timer.stop()
            return
        progress = min(1.0, self._clock.elapsed() / float(self._duration_ms))
        eased = self._curve.valueForProgress(progress)
        self._progress = self._from_progress + (self._to_progress - self._from_progress) * eased
        self.update()
        if progress >= 1.0:
            self._timer.stop()
            self._progress = self._to_progress
            self.update()

    def _target(self) -> float:
        if self._pressed:
            return 1.0
        if self._active:
            return 0.92
        if self._hovered:
            return 0.58
        return 0.0

    def _animate(self) -> None:
        target = self._target()
        if abs(target - self._progress) < 0.001:
            self._progress = target
            self.update()
            return
        self._from_progress = self._progress
        self._to_progress = target
        self._clock.restart()
        if not self._timer.isActive():
            self._timer.start()

    def getActive(self) -> bool:
        return self._active

    def setActive(self, value: bool) -> None:
        if self._active == value:
            return
        self._active = value
        self.activeChanged.emit()
        self._animate()

    def getHovered(self) -> bool:
        return self._hovered

    def setHovered(self, value: bool) -> None:
        if self._hovered == value:
            return
        self._hovered = value
        self.hoveredChanged.emit()
        self._animate()

    def getPressed(self) -> bool:
        return self._pressed

    def setPressed(self, value: bool) -> None:
        if self._pressed == value:
            return
        self._pressed = value
        self.pressedChanged.emit()
        self._animate()

    def getAccentColor(self) -> QColor:
        return self._accent

    def setAccentColor(self, value) -> None:
        color = QColor(value)
        if self._accent == color:
            return
        self._accent = color
        self.accentColorChanged.emit()
        self.update()

    def getNeutralColor(self) -> QColor:
        return self._neutral

    def setNeutralColor(self, value) -> None:
        color = QColor(value)
        if self._neutral == color:
            return
        self._neutral = color
        self.neutralColorChanged.emit()
        self.update()

    def getEdge(self) -> str:
        return self._edge

    def setEdge(self, value: str) -> None:
        if self._edge == value:
            return
        self._edge = value
        self.edgeChanged.emit()
        self.update()

    def getRadius(self) -> float:
        return self._radius

    def setRadius(self, value: float) -> None:
        if abs(self._radius - value) < 0.01:
            return
        self._radius = value
        self.radiusChanged.emit()
        self.update()

    def paint(self, painter: QPainter) -> None:
        if self.width() <= 1 or self.height() <= 1:
            return
        rect = self.boundingRect().adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        path = QPainterPath()
        path.addRoundedRect(rect, self._radius, self._radius)

        if self._progress > 0.001:
            fill = QColor(self._neutral)
            fill.setAlphaF(0.12 + self._progress * 0.18)
            painter.fillPath(path, fill)

            border = QColor(self._accent)
            border.setAlphaF(0.1 + self._progress * 0.28)
            pen = QPen(border)
            pen.setWidthF(1.0)
            painter.setPen(pen)
            painter.drawPath(path)

            glow = self._edge_gradient(rect)
            if glow is not None:
                painter.fillPath(path, glow)

    def _edge_gradient(self, rect):
        accent = QColor(self._accent)
        accent.setAlphaF(0.16 + self._progress * 0.48)
        transparent = QColor(accent)
        transparent.setAlpha(0)

        if self._edge == "left":
            gradient = QLinearGradient(rect.left(), rect.top(), rect.left() + rect.width() * 0.38, rect.top())
            gradient.setColorAt(0.0, accent)
            gradient.setColorAt(0.42, QColor(accent.red(), accent.green(), accent.blue(), int(46 * self._progress)))
            gradient.setColorAt(1.0, transparent)
            return gradient
        if self._edge == "right":
            gradient = QLinearGradient(rect.right(), rect.top(), rect.right() - rect.width() * 0.38, rect.top())
            gradient.setColorAt(0.0, accent)
            gradient.setColorAt(0.42, QColor(accent.red(), accent.green(), accent.blue(), int(46 * self._progress)))
            gradient.setColorAt(1.0, transparent)
            return gradient
        if self._edge == "bottom":
            gradient = QLinearGradient(rect.left(), rect.bottom(), rect.left(), rect.top())
            gradient.setColorAt(0.0, accent)
            gradient.setColorAt(0.35, QColor(accent.red(), accent.green(), accent.blue(), int(42 * self._progress)))
            gradient.setColorAt(1.0, transparent)
            return gradient
        if self._edge == "top":
            gradient = QLinearGradient(rect.left(), rect.top(), rect.left(), rect.bottom())
            gradient.setColorAt(0.0, accent)
            gradient.setColorAt(0.35, QColor(accent.red(), accent.green(), accent.blue(), int(42 * self._progress)))
            gradient.setColorAt(1.0, transparent)
            return gradient
        gradient = QLinearGradient(rect.left(), rect.top(), rect.right(), rect.bottom())
        gradient.setColorAt(0.0, QColor(accent.red(), accent.green(), accent.blue(), int(88 * self._progress)))
        gradient.setColorAt(0.45, QColor(accent.red(), accent.green(), accent.blue(), int(26 * self._progress)))
        gradient.setColorAt(1.0, transparent)
        return gradient

    active = Property(bool, getActive, setActive, notify=activeChanged)
    hovered = Property(bool, getHovered, setHovered, notify=hoveredChanged)
    pressed = Property(bool, getPressed, setPressed, notify=pressedChanged)
    accentColor = Property(QColor, getAccentColor, setAccentColor, notify=accentColorChanged)
    neutralColor = Property(QColor, getNeutralColor, setNeutralColor, notify=neutralColorChanged)
    edge = Property(str, getEdge, setEdge, notify=edgeChanged)
    radius = Property(float, getRadius, setRadius, notify=radiusChanged)


class ShimmerRailItem(QQuickPaintedItem):
    runningChanged = Signal()
    accentColorChanged = Signal()
    baseColorChanged = Signal()
    radiusChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAntialiasing(True)
        self._running = True
        self._phase = 0.0
        self._radius = 6.0
        self._accent = QColor("#1f5a84")
        self._base = QColor("#dbe8f3")
        self._timer = QTimer(self)
        self._timer.setInterval(22)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self) -> None:
        if not self._running:
            return
        self._phase = (self._phase + 0.035) % 1.0
        self.update()

    def getRunning(self) -> bool:
        return self._running

    def setRunning(self, value: bool) -> None:
        if self._running == value:
            return
        self._running = value
        if value and not self._timer.isActive():
            self._timer.start()
        self.runningChanged.emit()
        self.update()

    def getAccentColor(self) -> QColor:
        return self._accent

    def setAccentColor(self, value) -> None:
        color = QColor(value)
        if self._accent == color:
            return
        self._accent = color
        self.accentColorChanged.emit()
        self.update()

    def getBaseColor(self) -> QColor:
        return self._base

    def setBaseColor(self, value) -> None:
        color = QColor(value)
        if self._base == color:
            return
        self._base = color
        self.baseColorChanged.emit()
        self.update()

    def getRadius(self) -> float:
        return self._radius

    def setRadius(self, value: float) -> None:
        if abs(self._radius - value) < 0.01:
            return
        self._radius = value
        self.radiusChanged.emit()
        self.update()

    def paint(self, painter: QPainter) -> None:
        rect = self.boundingRect().adjusted(0.5, 0.5, -0.5, -0.5)
        if rect.width() <= 1 or rect.height() <= 1:
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        clip = QPainterPath()
        clip.addRoundedRect(rect, self._radius, self._radius)
        painter.fillPath(clip, QColor(self._base))
        if not self._running:
            return
        for index in range(-1, 4):
            x = (self._phase * 1.3 + index * 0.28) * rect.width()
            gradient = QLinearGradient(x - 24, rect.top(), x + 44, rect.top())
            strong = QColor(self._accent)
            strong.setAlpha(160)
            soft = QColor(self._accent)
            soft.setAlpha(36)
            transparent = QColor(self._accent)
            transparent.setAlpha(0)
            gradient.setColorAt(0.0, transparent)
            gradient.setColorAt(0.25, soft)
            gradient.setColorAt(0.55, strong)
            gradient.setColorAt(1.0, transparent)
            painter.fillRect(x - 24, rect.top(), 68, rect.height(), gradient)

    running = Property(bool, getRunning, setRunning, notify=runningChanged)
    accentColor = Property(QColor, getAccentColor, setAccentColor, notify=accentColorChanged)
    baseColor = Property(QColor, getBaseColor, setBaseColor, notify=baseColorChanged)
    radius = Property(float, getRadius, setRadius, notify=radiusChanged)


def register_qml_types() -> None:
    qmlRegisterType(SignalAccentItem, "Coyin.Chrome", 1, 0, "SignalAccent")
    qmlRegisterType(ShimmerRailItem, "Coyin.Chrome", 1, 0, "ShimmerRail")
