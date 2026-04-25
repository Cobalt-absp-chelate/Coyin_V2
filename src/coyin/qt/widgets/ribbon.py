from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QToolButton, QVBoxLayout, QWidget

from coyin.qt.widgets.theme import palette_for


class RibbonGroup(QFrame):
    def __init__(self, title: str, min_width: int = 0):
        super().__init__()
        self.setObjectName("RibbonSurface")
        self.setProperty("ribbonRole", "group")
        if min_width > 0:
            self.setMinimumWidth(min_width)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 2)
        layout.setSpacing(4)

        top_host = QWidget()
        top_layout = QHBoxLayout(top_host)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)

        self.row_host = QWidget()
        self.row = QHBoxLayout(self.row_host)
        self.row.setContentsMargins(0, 0, 0, 0)
        self.row.setSpacing(6)
        self.row.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        top_layout.addWidget(self.row_host, 1)

        self.separator = QFrame()
        self.separator.setProperty("ribbonRole", "groupSeparator")
        self.separator.setFixedWidth(1)
        self.separator.setSizePolicy(self.separator.sizePolicy().horizontalPolicy(), self.separator.sizePolicy().verticalPolicy())
        top_layout.addWidget(self.separator, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(top_host)

        label = QLabel(title)
        label.setProperty("ribbonRole", "groupTitle")
        label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(label)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        reference_height = max(40, self.row_host.sizeHint().height(), self.row_host.height())
        self.separator.setFixedHeight(int(reference_height * 0.68))


class RibbonField(QFrame):
    def __init__(self, title: str, field: QWidget, min_width: int = 0):
        super().__init__()
        self.setObjectName("RibbonField")
        self.setProperty("ribbonRole", "fieldHost")
        if min_width > 0:
            self.setMinimumWidth(min_width)
        field.setProperty("ribbonRole", "field")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QLabel(title)
        label.setProperty("ribbonRole", "fieldTitle")
        layout.addWidget(label)
        layout.addWidget(field)

        self.field = field


def configure_ribbon_tool(button: QToolButton, variant: str = "command") -> None:
    button.setProperty("ribbonRole", variant)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    button.setAutoRaise(False)
    if variant == "menu":
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        button.setMinimumSize(110, 34)
    elif variant == "compact":
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        button.setMinimumSize(56, 54)
    elif variant == "icon":
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        button.setMinimumSize(34, 34)
    else:
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        button.setMinimumSize(66, 60)


def ribbon_stylesheet(mode: str) -> str:
    palette = palette_for(mode)
    return f"""
    QFrame#RibbonSurface[ribbonRole="group"] {{
        background: transparent;
        border: none;
        border-radius: 0px;
    }}
    QFrame[ribbonRole="groupSeparator"] {{
        background: {palette.border};
        border: none;
        min-width: 1px;
        max-width: 1px;
    }}
    QLabel[ribbonRole="groupTitle"] {{
        color: {palette.text_muted};
        font-size: 11px;
        padding-left: 6px;
        background: transparent;
    }}
    QFrame#RibbonField[ribbonRole="fieldHost"] {{
        background: transparent;
        border: none;
    }}
    QLabel[ribbonRole="fieldTitle"] {{
        color: {palette.text_muted};
        font-size: 11px;
        padding-left: 2px;
    }}
    QComboBox[ribbonRole="field"], QFontComboBox[ribbonRole="field"], QDoubleSpinBox[ribbonRole="stepper"] {{
        min-height: 30px;
        max-height: 30px;
        padding: 2px 24px 2px 8px;
        background: {palette.panel_raised};
        border: 1px solid {palette.border};
        border-radius: 4px;
        color: {palette.text};
    }}
    QComboBox[ribbonRole="field"]:hover, QFontComboBox[ribbonRole="field"]:hover, QDoubleSpinBox[ribbonRole="stepper"]:hover {{
        background: {palette.panel_hover};
        border: 1px solid {palette.border_strong};
    }}
    QComboBox[ribbonRole="field"]:focus, QFontComboBox[ribbonRole="field"]:focus, QDoubleSpinBox[ribbonRole="stepper"]:focus {{
        background: {palette.panel_focus};
        border: 1px solid {palette.accent_outline};
    }}
    QComboBox[ribbonRole="field"]::drop-down, QFontComboBox[ribbonRole="field"]::drop-down {{
        width: 16px;
        border: none;
        background: transparent;
        subcontrol-origin: padding;
        subcontrol-position: top right;
    }}
    QComboBox[ribbonRole="field"]::down-arrow, QFontComboBox[ribbonRole="field"]::down-arrow {{
        width: 7px;
        height: 7px;
    }}
    QToolButton[ribbonRole="command"], QToolButton[ribbonRole="compact"], QToolButton[ribbonRole="menu"] {{
        background: {palette.panel_raised};
        border: 1px solid transparent;
        border-radius: 5px;
        color: {palette.text};
        padding: 4px 6px;
    }}
    QToolButton[ribbonRole="icon"] {{
        background: transparent;
        border: 1px solid transparent;
        border-radius: 4px;
        color: {palette.text};
        padding: 2px;
    }}
    QToolButton[ribbonRole="comboArrow"] {{
        background: transparent;
        border: none;
        color: {palette.text_muted};
        font-size: 12px;
        padding: 0px;
    }}
    QToolButton[ribbonRole="command"]:hover, QToolButton[ribbonRole="compact"]:hover, QToolButton[ribbonRole="menu"]:hover {{
        background: {palette.panel_hover};
        border: 1px solid {palette.border};
    }}
    QToolButton[ribbonRole="icon"]:hover {{
        background: {palette.panel_hover};
        border: 1px solid {palette.border};
    }}
    QToolButton[ribbonRole="comboArrow"]:hover {{
        color: {palette.text};
    }}
    QToolButton[ribbonRole="command"]:pressed, QToolButton[ribbonRole="compact"]:pressed, QToolButton[ribbonRole="menu"]:pressed {{
        background: {palette.panel_focus};
        border: 1px solid {palette.accent_outline};
    }}
    QToolButton[ribbonRole="icon"]:pressed {{
        background: {palette.panel_focus};
        border: 1px solid {palette.accent_outline};
    }}
    QToolButton[ribbonRole="command"] {{
        min-width: 66px;
    }}
    QToolButton[ribbonRole="compact"] {{
        min-width: 58px;
        font-size: 11px;
    }}
    QToolButton[ribbonRole="menu"] {{
        min-width: 110px;
        font-size: 12px;
        text-align: left;
        padding: 6px 10px;
    }}
    QDoubleSpinBox[ribbonRole="stepper"]::up-button, QDoubleSpinBox[ribbonRole="stepper"]::down-button {{
        width: 16px;
        border: none;
        background: transparent;
        subcontrol-origin: padding;
    }}
    QDoubleSpinBox[ribbonRole="stepper"]::up-button {{
        subcontrol-position: top right;
    }}
    QDoubleSpinBox[ribbonRole="stepper"]::down-button {{
        subcontrol-position: bottom right;
    }}
    QDoubleSpinBox[ribbonRole="stepper"]::up-arrow, QDoubleSpinBox[ribbonRole="stepper"]::down-arrow {{
        width: 6px;
        height: 6px;
    }}
    """
