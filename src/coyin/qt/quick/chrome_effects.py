from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QObject, Property, QElapsedTimer, QTimer, Signal, Slot, Qt
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtQml import qmlRegisterType
from PySide6.QtQuick import QQuickItem, QQuickPaintedItem


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
        self._duration_ms = 180
        self._curve = QEasingCurve(QEasingCurve.Type.OutCubic)
        self._clock = QElapsedTimer()
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick_animation)
        self._window = None
        self.windowChanged.connect(self._on_window_changed)
        self.visibleChanged.connect(self._on_visible_or_enabled_changed)
        self.enabledChanged.connect(self._on_visible_or_enabled_changed)

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
        if not self.isVisible() or not self.isEnabled():
            self._clear_interaction()
            return
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

    def _clear_interaction(self) -> None:
        self._hovered = False
        self._pressed = False
        if not self._active:
            self._progress = 0.0
        self._timer.stop()
        self.update()

    def _on_window_changed(self, window) -> None:
        if self._window is window:
            return
        if self._window is not None:
            try:
                self._window.activeChanged.disconnect(self._on_window_active_changed)
            except Exception:
                pass
        self._window = window
        if self._window is not None:
            self._window.activeChanged.connect(self._on_window_active_changed)

    def _on_window_active_changed(self) -> None:
        if self.window() is not None and not self.window().isActive():
            self._clear_interaction()

    def _on_visible_or_enabled_changed(self) -> None:
        if not self.isVisible() or not self.isEnabled():
            self._clear_interaction()

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
        if value and (not self.isVisible() or not self.isEnabled()):
            value = False
        if self._hovered == value:
            return
        self._hovered = value
        self.hoveredChanged.emit()
        self._animate()

    def getPressed(self) -> bool:
        return self._pressed

    def setPressed(self, value: bool) -> None:
        if value and (not self.isVisible() or not self.isEnabled()):
            value = False
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

    def itemChange(self, change, value) -> None:
        super().itemChange(change, value)
        watched_changes = {
            getattr(QQuickItem.ItemChange, "ItemVisibleHasChanged", None),
            getattr(QQuickItem.ItemChange, "ItemEnabledHasChanged", None),
        }
        if change in watched_changes and (not self.isVisible() or not self.isEnabled()):
            self._clear_interaction()

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


class InteractionStateItem(QQuickItem):
    resolvedStateChanged = Signal()
    activeChanged = Signal()
    hoveredChanged = Signal()
    pressedChanged = Signal()
    focusedChanged = Signal()
    hoverProgressChanged = Signal()
    pressProgressChanged = Signal()
    focusProgressChanged = Signal()
    selectionProgressChanged = Signal()
    busyProgressChanged = Signal()
    engageProgressChanged = Signal()
    visualProgressChanged = Signal()
    enabledInputChanged = Signal()
    visibleInputChanged = Signal()
    hoveredInputChanged = Signal()
    pressedInputChanged = Signal()
    focusedInputChanged = Signal()
    busyInputChanged = Signal()
    selectedInputChanged = Signal()
    targetItemChanged = Signal()
    resetTokenChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._enabled_input = True
        self._visible_input = True
        self._hovered_input = False
        self._pressed_input = False
        self._focused_input = False
        self._busy_input = False
        self._selected_input = False
        self._resolved_state = "normal"
        self._target_item = None
        self._reset_token = 0
        self._window = None
        self._hover_progress = 0.0
        self._hover_from = 0.0
        self._hover_to = 0.0
        self._press_progress = 0.0
        self._press_from = 0.0
        self._press_to = 0.0
        self._focus_progress = 0.0
        self._focus_from = 0.0
        self._focus_to = 0.0
        self._selection_progress = 0.0
        self._selection_from = 0.0
        self._selection_to = 0.0
        self._busy_progress = 0.0
        self._busy_from = 0.0
        self._busy_to = 0.0
        self._engage_progress = 0.0
        self._engage_from = 0.0
        self._engage_to = 0.0
        self._channel_durations_ms = {
            "hover": 150,
            "press": 126,
            "focus": 188,
            "selection": 192,
            "busy": 206,
            "engage": 182,
        }
        self._animation_curve = QEasingCurve(QEasingCurve.Type.OutCubic)
        self._animation_clock = QElapsedTimer()
        self._animation_timer = QTimer(self)
        self._animation_timer.setInterval(16)
        self._animation_timer.timeout.connect(self._tick_animation)
        self._verification_timer = QTimer(self)
        self._verification_timer.setInterval(24)
        self._verification_timer.timeout.connect(self._verify_transient_state)
        self.windowChanged.connect(self._on_window_changed)
        self.visibleChanged.connect(self._on_visible_or_enabled_changed)
        self.enabledChanged.connect(self._on_visible_or_enabled_changed)

    def _on_window_changed(self, window) -> None:
        if self._window is window:
            return
        if self._window is not None:
            try:
                self._window.activeChanged.disconnect(self._update_state)
            except Exception:
                pass
        self._window = window
        if self._window is not None:
            self._window.activeChanged.connect(self._update_state)
        self._update_state()

    def _window_active(self) -> bool:
        if self._window is None:
            return True
        try:
            return self._window.isActive()
        except RuntimeError:
            self._window = None
            return False

    def _reference_item(self):
        return self._target_item if self._target_item is not None else self.parentItem()

    def _cursor_inside_target(self) -> bool:
        target_item = self._reference_item()
        if target_item is None or self._window is None:
            return True
        try:
            window_pos = self._window.mapFromGlobal(QCursor.pos())
            scene_pos = QPointF(float(window_pos.x()), float(window_pos.y()))
            local_pos = target_item.mapFromScene(scene_pos)
            return target_item.boundingRect().contains(local_pos)
        except Exception:
            return True

    def _pointer_pressed(self) -> bool:
        try:
            return bool(QGuiApplication.mouseButtons() & Qt.MouseButton.LeftButton)
        except Exception:
            return self._pressed_input

    def _interaction_flags(self) -> dict[str, bool]:
        interactive = self._enabled_input and self._visible_input and self._window_active()
        return {
            "hovered": interactive and self._hovered_input,
            "pressed": interactive and self._pressed_input,
            "focused": interactive and self._focused_input,
            "active": interactive and (
                self._pressed_input or self._busy_input or self._selected_input or self._focused_input
            ),
        }

    def _emit_flag_changes(self, previous: dict[str, bool]) -> None:
        current = self._interaction_flags()
        if previous.get("hovered") != current["hovered"]:
            self.hoveredChanged.emit()
        if previous.get("pressed") != current["pressed"]:
            self.pressedChanged.emit()
        if previous.get("focused") != current["focused"]:
            self.focusedChanged.emit()
        if previous.get("active") != current["active"]:
            self.activeChanged.emit()

    def _clear_transient_inputs(self, clear_focus: bool = False) -> None:
        cleared_hover = self._hovered_input
        cleared_press = self._pressed_input
        cleared_focus = clear_focus and self._focused_input
        self._hovered_input = False
        self._pressed_input = False
        if clear_focus:
            self._focused_input = False
        if cleared_hover:
            self.hoveredInputChanged.emit()
        if cleared_press:
            self.pressedInputChanged.emit()
        if cleared_focus:
            self.focusedInputChanged.emit()

    def _compute_state(self) -> str:
        if not self._enabled_input:
            return "disabled"
        if not self._visible_input or not self._window_active():
            return "normal"
        if self._pressed_input:
            return "pressed"
        if self._busy_input:
            return "busy"
        if self._selected_input:
            return "selected"
        if self._focused_input:
            return "focused"
        if self._hovered_input:
            return "hover"
        return "normal"

    def _update_state(self) -> None:
        previous_flags = self._interaction_flags()
        previous_state = self._resolved_state
        self._coerce_transient_inputs()

        next_state = self._compute_state()
        if next_state != previous_state:
            self._resolved_state = next_state
            self.resolvedStateChanged.emit()
        self._emit_flag_changes(previous_flags)
        self._animate_progresses()
        self._sync_verification_timer()

    def _coerce_transient_inputs(self) -> None:
        if not self._visible_input or not self._enabled_input or not self._window_active():
            self._clear_transient_inputs()
            return

        if self._hovered_input and not self._cursor_inside_target():
            self._hovered_input = False
            self.hoveredInputChanged.emit()
        if self._pressed_input and not self._pointer_pressed():
            self._pressed_input = False
            self.pressedInputChanged.emit()

    def _sync_verification_timer(self) -> None:
        engaged = (
            self._hovered_input
            or self._pressed_input
            or self._focused_input
            or self._animation_timer.isActive()
            or self._hover_progress > 0.001
            or self._press_progress > 0.001
            or self._focus_progress > 0.001
        )
        if engaged:
            if not self._verification_timer.isActive():
                self._verification_timer.start()
        elif self._verification_timer.isActive():
            self._verification_timer.stop()

    def _step_channel(self, current: float, start: float, end: float, elapsed_ms: int, duration_key: str) -> float:
        duration_ms = max(1, int(self._channel_durations_ms.get(duration_key, 170)))
        progress = min(1.0, elapsed_ms / float(duration_ms))
        eased = self._animation_curve.valueForProgress(progress)
        return start + (end - start) * eased

    @Slot()
    def clearTransientState(self) -> None:
        previous_flags = self._interaction_flags()
        previous_state = self._resolved_state
        self._clear_transient_inputs()
        next_state = self._compute_state()
        if next_state != previous_state:
            self._resolved_state = next_state
            self.resolvedStateChanged.emit()
        self._emit_flag_changes(previous_flags)
        self._animate_progresses()
        self._sync_verification_timer()

    def _verify_transient_state(self) -> None:
        self._update_state()

    def _animate_progresses(self) -> None:
        interactive = self._enabled_input and self._visible_input and self._window_active()
        hover_target = 1.0 if interactive and self._hovered_input else 0.0
        press_target = 1.0 if interactive and self._pressed_input else 0.0
        focus_target = 1.0 if interactive and self._focused_input else 0.0
        selection_target = 1.0 if interactive and self._selected_input else 0.0
        busy_target = 1.0 if interactive and self._busy_input else 0.0
        engage_target = max(
            max(hover_target * 0.62, focus_target * 0.78),
            max(press_target, max(selection_target * 0.86, busy_target * 0.90)),
        )

        changed = any(
            abs(current - target) > 0.0001
            for current, target in (
                (self._hover_to, hover_target),
                (self._press_to, press_target),
                (self._focus_to, focus_target),
                (self._selection_to, selection_target),
                (self._busy_to, busy_target),
                (self._engage_to, engage_target),
            )
        )
        if not changed:
            return

        self._hover_from = self._hover_progress
        self._hover_to = hover_target
        self._press_from = self._press_progress
        self._press_to = press_target
        self._focus_from = self._focus_progress
        self._focus_to = focus_target
        self._selection_from = self._selection_progress
        self._selection_to = selection_target
        self._busy_from = self._busy_progress
        self._busy_to = busy_target
        self._engage_from = self._engage_progress
        self._engage_to = engage_target
        self._animation_clock.restart()
        if not self._animation_timer.isActive():
            self._animation_timer.start()

    def _update_channel(self, start: float, end: float, current: float, eased: float, signal: Signal) -> float:
        next_value = start + (end - start) * eased
        if abs(next_value - current) > 0.0001:
            signal.emit()
        return next_value

    def _tick_animation(self) -> None:
        if not self._animation_clock.isValid():
            self._animation_timer.stop()
            return

        elapsed_ms = self._animation_clock.elapsed()

        next_hover = self._step_channel(self._hover_progress, self._hover_from, self._hover_to, elapsed_ms, "hover")
        if abs(next_hover - self._hover_progress) > 0.0001:
            self._hover_progress = next_hover
            self.hoverProgressChanged.emit()

        next_press = self._step_channel(self._press_progress, self._press_from, self._press_to, elapsed_ms, "press")
        if abs(next_press - self._press_progress) > 0.0001:
            self._press_progress = next_press
            self.pressProgressChanged.emit()

        next_focus = self._step_channel(self._focus_progress, self._focus_from, self._focus_to, elapsed_ms, "focus")
        if abs(next_focus - self._focus_progress) > 0.0001:
            self._focus_progress = next_focus
            self.focusProgressChanged.emit()

        next_selection = self._step_channel(
            self._selection_progress,
            self._selection_from,
            self._selection_to,
            elapsed_ms,
            "selection",
        )
        if abs(next_selection - self._selection_progress) > 0.0001:
            self._selection_progress = next_selection
            self.selectionProgressChanged.emit()

        next_busy = self._step_channel(self._busy_progress, self._busy_from, self._busy_to, elapsed_ms, "busy")
        if abs(next_busy - self._busy_progress) > 0.0001:
            self._busy_progress = next_busy
            self.busyProgressChanged.emit()

        next_engage = self._step_channel(
            self._engage_progress,
            self._engage_from,
            self._engage_to,
            elapsed_ms,
            "engage",
        )
        if abs(next_engage - self._engage_progress) > 0.0001:
            self._engage_progress = next_engage
            self.engageProgressChanged.emit()

        self.visualProgressChanged.emit()

        if elapsed_ms >= max(self._channel_durations_ms.values()):
            self._animation_timer.stop()

            if abs(self._hover_progress - self._hover_to) > 0.0001:
                self._hover_progress = self._hover_to
                self.hoverProgressChanged.emit()
            if abs(self._press_progress - self._press_to) > 0.0001:
                self._press_progress = self._press_to
                self.pressProgressChanged.emit()
            if abs(self._focus_progress - self._focus_to) > 0.0001:
                self._focus_progress = self._focus_to
                self.focusProgressChanged.emit()
            if abs(self._selection_progress - self._selection_to) > 0.0001:
                self._selection_progress = self._selection_to
                self.selectionProgressChanged.emit()
            if abs(self._busy_progress - self._busy_to) > 0.0001:
                self._busy_progress = self._busy_to
                self.busyProgressChanged.emit()
            if abs(self._engage_progress - self._engage_to) > 0.0001:
                self._engage_progress = self._engage_to
                self.engageProgressChanged.emit()

            self.visualProgressChanged.emit()
            self._sync_verification_timer()

    def getResolvedState(self) -> str:
        return self._resolved_state

    def getActive(self) -> bool:
        return self._interaction_flags()["active"]

    def getHovered(self) -> bool:
        return self._interaction_flags()["hovered"]

    def getPressed(self) -> bool:
        return self._interaction_flags()["pressed"]

    def getFocused(self) -> bool:
        return self._interaction_flags()["focused"]

    def getEnabledInput(self) -> bool:
        return self._enabled_input

    def setEnabledInput(self, value: bool) -> None:
        if self._enabled_input == value:
            return
        self._enabled_input = value
        self.enabledInputChanged.emit()
        self._update_state()

    def getVisibleInput(self) -> bool:
        return self._visible_input

    def setVisibleInput(self, value: bool) -> None:
        if self._visible_input == value:
            return
        self._visible_input = value
        self.visibleInputChanged.emit()
        self._update_state()

    def getHoveredInput(self) -> bool:
        return self._hovered_input

    def setHoveredInput(self, value: bool) -> None:
        if self._hovered_input == value:
            return
        self._hovered_input = value
        self.hoveredInputChanged.emit()
        self._update_state()

    def getPressedInput(self) -> bool:
        return self._pressed_input

    def setPressedInput(self, value: bool) -> None:
        if self._pressed_input == value:
            return
        self._pressed_input = value
        self.pressedInputChanged.emit()
        self._update_state()

    def getFocusedInput(self) -> bool:
        return self._focused_input

    def setFocusedInput(self, value: bool) -> None:
        if self._focused_input == value:
            return
        self._focused_input = value
        self.focusedInputChanged.emit()
        self._update_state()

    def getBusyInput(self) -> bool:
        return self._busy_input

    def setBusyInput(self, value: bool) -> None:
        if self._busy_input == value:
            return
        self._busy_input = value
        self.busyInputChanged.emit()
        self._update_state()

    def getSelectedInput(self) -> bool:
        return self._selected_input

    def setSelectedInput(self, value: bool) -> None:
        if self._selected_input == value:
            return
        self._selected_input = value
        self.selectedInputChanged.emit()
        self._update_state()

    def _detach_target_item(self) -> None:
        if self._target_item is None:
            return
        for signal_name in ("visibleChanged", "enabledChanged", "destroyed"):
            try:
                getattr(self._target_item, signal_name).disconnect(self._update_state)
            except Exception:
                pass
        try:
            self._target_item.destroyed.disconnect(self._on_target_destroyed)
        except Exception:
            pass

    def _attach_target_item(self) -> None:
        if self._target_item is None:
            return
        for signal_name in ("visibleChanged", "enabledChanged"):
            try:
                getattr(self._target_item, signal_name).connect(self._update_state)
            except Exception:
                continue
        try:
            self._target_item.destroyed.connect(self._on_target_destroyed)
        except Exception:
            pass

    def _on_target_destroyed(self, *_args) -> None:
        self._target_item = None
        self.targetItemChanged.emit()
        self.clearTransientState()

    def getTargetItem(self):
        return self._target_item

    def setTargetItem(self, value) -> None:
        if self._target_item is value:
            return
        self._detach_target_item()
        self._target_item = value
        self._attach_target_item()
        self.targetItemChanged.emit()
        self._update_state()

    def getResetToken(self) -> int:
        return self._reset_token

    def setResetToken(self, value: int) -> None:
        next_value = int(value)
        if self._reset_token == next_value:
            return
        self._reset_token = next_value
        self.resetTokenChanged.emit()
        self.clearTransientState()

    def _on_visible_or_enabled_changed(self) -> None:
        if not self.isVisible() or not self.isEnabled():
            self.clearTransientState()
        else:
            self._update_state()

    def getHoverProgress(self) -> float:
        return self._hover_progress

    def getPressProgress(self) -> float:
        return self._press_progress

    def getFocusProgress(self) -> float:
        return self._focus_progress

    def getSelectionProgress(self) -> float:
        return self._selection_progress

    def getBusyProgress(self) -> float:
        return self._busy_progress

    def getEngageProgress(self) -> float:
        return self._engage_progress

    def getAccentStrength(self) -> float:
        return max(
            0.0,
            min(
                1.0,
                self._hover_progress * 0.22
                + self._focus_progress * 0.34
                + self._press_progress * 0.54
                + self._selection_progress * 0.40
                + self._busy_progress * 0.46,
            ),
        )

    def getFrameStrength(self) -> float:
        return max(
            0.0,
            min(
                1.0,
                self._hover_progress * 0.16
                + self._focus_progress * 0.32
                + self._press_progress * 0.42
                + self._selection_progress * 0.24
                + self._busy_progress * 0.28,
            ),
        )

    def getTextStrength(self) -> float:
        return max(
            0.0,
            min(
                1.0,
                self._hover_progress * 0.16
                + self._focus_progress * 0.24
                + self._press_progress * 0.12
                + self._selection_progress * 0.18
                + self._busy_progress * 0.14,
            ),
        )

    def getSettleStrength(self) -> float:
        return max(
            max(self._focus_progress * 0.82, self._selection_progress * 0.92),
            self._busy_progress * 0.95,
        )

    resolvedState = Property(str, getResolvedState, notify=resolvedStateChanged)
    active = Property(bool, getActive, notify=activeChanged)
    hovered = Property(bool, getHovered, notify=hoveredChanged)
    pressed = Property(bool, getPressed, notify=pressedChanged)
    focused = Property(bool, getFocused, notify=focusedChanged)
    hoverProgress = Property(float, getHoverProgress, notify=hoverProgressChanged)
    pressProgress = Property(float, getPressProgress, notify=pressProgressChanged)
    focusProgress = Property(float, getFocusProgress, notify=focusProgressChanged)
    selectionProgress = Property(float, getSelectionProgress, notify=selectionProgressChanged)
    busyProgress = Property(float, getBusyProgress, notify=busyProgressChanged)
    engageProgress = Property(float, getEngageProgress, notify=engageProgressChanged)
    accentStrength = Property(float, getAccentStrength, notify=visualProgressChanged)
    frameStrength = Property(float, getFrameStrength, notify=visualProgressChanged)
    textStrength = Property(float, getTextStrength, notify=visualProgressChanged)
    settleStrength = Property(float, getSettleStrength, notify=visualProgressChanged)
    enabledInput = Property(bool, getEnabledInput, setEnabledInput, notify=enabledInputChanged)
    visibleInput = Property(bool, getVisibleInput, setVisibleInput, notify=visibleInputChanged)
    hoveredInput = Property(bool, getHoveredInput, setHoveredInput, notify=hoveredInputChanged)
    pressedInput = Property(bool, getPressedInput, setPressedInput, notify=pressedInputChanged)
    focusedInput = Property(bool, getFocusedInput, setFocusedInput, notify=focusedInputChanged)
    busyInput = Property(bool, getBusyInput, setBusyInput, notify=busyInputChanged)
    selectedInput = Property(bool, getSelectedInput, setSelectedInput, notify=selectedInputChanged)
    targetItem = Property(QObject, getTargetItem, setTargetItem, notify=targetItemChanged)
    resetToken = Property(int, getResetToken, setResetToken, notify=resetTokenChanged)


class DisclosureMotionItem(QQuickItem):
    expandedChanged = Signal()
    progressChanged = Signal()
    durationChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._expanded = False
        self._progress = 0.0
        self._from_progress = 0.0
        self._to_progress = 0.0
        self._duration_ms = 190
        self._curve = QEasingCurve(QEasingCurve.Type.InOutCubic)
        self._clock = QElapsedTimer()
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._tick)

    def _tick(self) -> None:
        if not self._clock.isValid():
            self._timer.stop()
            return
        progress = min(1.0, self._clock.elapsed() / float(self._duration_ms))
        eased = self._curve.valueForProgress(progress)
        next_value = self._from_progress + (self._to_progress - self._from_progress) * eased
        if abs(next_value - self._progress) > 0.0001:
            self._progress = next_value
            self.progressChanged.emit()
        if progress >= 1.0:
            self._timer.stop()
            if abs(self._progress - self._to_progress) > 0.0001:
                self._progress = self._to_progress
                self.progressChanged.emit()

    def _animate(self) -> None:
        target = 1.0 if self._expanded else 0.0
        if abs(target - self._progress) < 0.0001:
            if abs(self._progress - target) > 0.0:
                self._progress = target
                self.progressChanged.emit()
            return
        self._from_progress = self._progress
        self._to_progress = target
        self._clock.restart()
        if not self._timer.isActive():
            self._timer.start()

    def getExpanded(self) -> bool:
        return self._expanded

    def setExpanded(self, value: bool) -> None:
        if self._expanded == value:
            return
        self._expanded = value
        self.expandedChanged.emit()
        self._animate()

    def getProgress(self) -> float:
        return self._progress

    def getDuration(self) -> int:
        return self._duration_ms

    def setDuration(self, value: int) -> None:
        if self._duration_ms == value:
            return
        self._duration_ms = max(60, int(value))
        self.durationChanged.emit()

    expanded = Property(bool, getExpanded, setExpanded, notify=expandedChanged)
    progress = Property(float, getProgress, notify=progressChanged)
    duration = Property(int, getDuration, setDuration, notify=durationChanged)


def register_qml_types() -> None:
    qmlRegisterType(SignalAccentItem, "Coyin.Chrome", 1, 0, "SignalAccent")
    qmlRegisterType(ShimmerRailItem, "Coyin.Chrome", 1, 0, "ShimmerRail")
    qmlRegisterType(InteractionStateItem, "Coyin.Chrome", 1, 0, "InteractionState")
    qmlRegisterType(DisclosureMotionItem, "Coyin.Chrome", 1, 0, "DisclosureMotion")
