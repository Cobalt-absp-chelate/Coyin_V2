from __future__ import annotations

from dataclasses import dataclass

from coyin.config import theme_tokens as load_theme_tokens


@dataclass(frozen=True)
class ThemePalette:
    background: str
    workspace: str
    workspace_tint: str
    chrome: str
    chrome_alt: str
    panel: str
    panel_alt: str
    panel_raised: str
    panel_inset: str
    panel_hover: str
    panel_focus: str
    text: str
    text_muted: str
    text_soft: str
    border: str
    border_strong: str
    accent: str
    anchor: str
    accent_hover: str
    accent_soft: str
    accent_surface: str
    accent_panel: str
    accent_outline: str
    selection: str
    success: str
    warning: str
    danger: str
    note: str
    shadow: str


def _palette_from_tokens(mode: str) -> ThemePalette:
    payload = load_theme_tokens(mode)
    return ThemePalette(
        background=str(payload["background"]),
        workspace=str(payload["workspace"]),
        workspace_tint=str(payload["workspaceTint"]),
        chrome=str(payload["chrome"]),
        chrome_alt=str(payload["chromeAlt"]),
        panel=str(payload["panel"]),
        panel_alt=str(payload["panelAlt"]),
        panel_raised=str(payload["panelRaised"]),
        panel_inset=str(payload["panelInset"]),
        panel_hover=str(payload["panelHover"]),
        panel_focus=str(payload["panelFocus"]),
        text=str(payload["text"]),
        text_muted=str(payload["textMuted"]),
        text_soft=str(payload["textSoft"]),
        border=str(payload["border"]),
        border_strong=str(payload["borderStrong"]),
        accent=str(payload["accent"]),
        anchor=str(payload["anchor"]),
        accent_hover=str(payload["accentHover"]),
        accent_soft=str(payload["accentSoft"]),
        accent_surface=str(payload["accentSurface"]),
        accent_panel=str(payload["accentPanel"]),
        accent_outline=str(payload["accentOutline"]),
        selection=str(payload["selection"]),
        success=str(payload["success"]),
        warning=str(payload["warning"]),
        danger=str(payload["danger"]),
        note=str(payload["note"]),
        shadow=str(payload["shadow"]),
    )


def palette_for(mode: str) -> ThemePalette:
    return _palette_from_tokens(mode)


def qml_tokens(mode: str) -> dict[str, str]:
    return load_theme_tokens(mode)


def base_stylesheet(mode: str) -> str:
    palette = palette_for(mode)
    return f"""
    QWidget {{
        background: {palette.workspace};
        color: {palette.text};
        font-family: 'Microsoft YaHei UI', 'Microsoft YaHei', 'Segoe UI';
        font-size: 13px;
    }}
    QMainWindow, QDockWidget {{
        background: {palette.workspace};
    }}
    QStatusBar {{
        background: {palette.chrome};
        border-top: 1px solid {palette.border};
    }}
    QToolBar, QTabWidget::pane, QLineEdit, QTextEdit, QPlainTextEdit, QListWidget,
    QTreeWidget, QTableWidget, QComboBox, QTabBar::tab, QPushButton, QScrollArea {{
        border: 1px solid {palette.border};
    }}
    QLineEdit, QTextEdit, QPlainTextEdit, QListWidget, QTreeWidget, QTableWidget, QComboBox {{
        background: {palette.panel_raised};
        selection-background-color: {palette.selection};
        selection-color: {palette.text};
        placeholder-text-color: {palette.text_soft};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus, QFontComboBox:focus {{
        border: 1px solid {palette.accent_outline};
        background: {palette.panel_focus};
    }}
    QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QFontComboBox:disabled {{
        color: {palette.text_soft};
        background: {palette.panel};
    }}
    QToolBar {{
        background: {palette.chrome};
        spacing: 4px;
        padding: 4px;
        border: none;
        border-bottom: 1px solid {palette.border};
    }}
    QTabWidget::pane {{
        background: {palette.chrome};
        border: none;
        border-bottom: 1px solid {palette.border};
    }}
    QTabBar::tab {{
        background: {palette.chrome_alt};
        border-radius: 4px;
        padding: 6px 12px;
        margin-right: 4px;
        color: {palette.text_muted};
    }}
    QTabBar::tab:selected {{
        background: {palette.accent_panel};
        color: {palette.anchor};
        border: 1px solid {palette.accent_outline};
    }}
    QPushButton, QToolButton {{
        background: {palette.panel_raised};
        border-radius: 4px;
        padding: 6px 10px;
        color: {palette.text};
    }}
    QPushButton:hover, QToolButton:hover {{
        background: {palette.panel_hover};
    }}
    QPushButton:pressed, QToolButton:pressed {{
        background: {palette.panel_focus};
    }}
    QPushButton:focus, QToolButton:focus {{
        border: 1px solid {palette.accent_outline};
        background: {palette.accent_panel};
        color: {palette.anchor};
    }}
    QPushButton:disabled, QToolButton:disabled {{
        color: {palette.text_soft};
        background: {palette.panel_inset};
    }}
    QFrame#RibbonSurface, QFrame#PageSheet, QFrame#InspectorPanel, QFrame#LogPanel {{
        background: {palette.panel};
        border: 1px solid {palette.border};
    }}
    QFrame#PageSheet {{
        border-radius: 6px;
    }}
    QComboBox, QSpinBox, QFontComboBox {{
        padding: 2px 8px;
        border-radius: 3px;
        min-height: 26px;
        background: {palette.panel_raised};
        border: 1px solid {palette.border};
    }}
    QComboBox::drop-down, QSpinBox::up-button, QSpinBox::down-button {{
        width: 16px;
        border: none;
        background: transparent;
        subcontrol-origin: padding;
    }}
    QComboBox::down-arrow, QSpinBox::up-arrow, QSpinBox::down-arrow {{
        width: 7px;
        height: 7px;
    }}
    QComboBox:hover, QSpinBox:hover, QFontComboBox:hover {{
        border: 1px solid {palette.border_strong};
        background: {palette.panel_hover};
    }}
    QComboBox:on, QSpinBox:focus, QFontComboBox:focus {{
        border: 1px solid {palette.accent_outline};
        background: {palette.panel_focus};
    }}
    QHeaderView::section {{
        background: {palette.chrome_alt};
        border: none;
        border-bottom: 1px solid {palette.border};
        padding: 6px;
    }}
    QListWidget, QTreeWidget, QTableWidget {{
        alternate-background-color: {palette.panel_alt};
    }}
    QSplitter::handle {{
        background: {palette.chrome_alt};
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 12px;
        margin: 2px;
        border: none;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 12px;
        margin: 2px;
        border: none;
    }}
    QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
        background: {palette.anchor};
        border-radius: 3px;
        min-height: 34px;
        min-width: 34px;
    }}
    QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
        background: {palette.accent_hover};
    }}
    QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{
        background: transparent;
        border: none;
    }}
    QToolTip {{
        background: {palette.panel_raised};
        color: {palette.text};
        border: 1px solid {palette.accent_outline};
        padding: 8px 10px;
        border-radius: 6px;
    }}
    """
