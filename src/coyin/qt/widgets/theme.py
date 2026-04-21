from __future__ import annotations

from dataclasses import dataclass

from coyin.native.bridge import load_theme


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


LIGHT = ThemePalette(
    background="#e7ebf0",
    workspace="#f1f4f8",
    workspace_tint="#e8eef5",
    chrome="#f7f9fb",
    chrome_alt="#e9eef4",
    panel="#fbfcfe",
    panel_alt="#f3f6fa",
    panel_raised="#ffffff",
    panel_inset="#ecf1f6",
    panel_hover="#eef4fa",
    panel_focus="#e4edf7",
    text="#122033",
    text_muted="#4c5d70",
    text_soft="#708195",
    border="#d5dde8",
    border_strong="#b9c6d8",
    accent="#1f5a84",
    anchor="#164e74",
    accent_hover="#2d6b98",
    accent_soft="#dbe8f3",
    accent_surface="#edf4fa",
    accent_panel="#e4edf7",
    accent_outline="#88a6c1",
    selection="#e9dfc9",
    success="#506d5e",
    warning="#8b6c3d",
    danger="#8c5656",
    note="#efe6d4",
    shadow="#10243712",
)

DARK = ThemePalette(
    background="#10161d",
    workspace="#141b24",
    workspace_tint="#182231",
    chrome="#18212b",
    chrome_alt="#1f2a36",
    panel="#1c2530",
    panel_alt="#243040",
    panel_raised="#202b37",
    panel_inset="#16202a",
    panel_hover="#283649",
    panel_focus="#314156",
    text="#eef3f8",
    text_muted="#a7b4c1",
    text_soft="#7f8e9d",
    border="#304254",
    border_strong="#486078",
    accent="#7ba8d0",
    anchor="#8eb9de",
    accent_hover="#93badb",
    accent_soft="#203044",
    accent_surface="#1d2c3c",
    accent_panel="#24384b",
    accent_outline="#5f84a7",
    selection="#5a4b34",
    success="#6d8e7b",
    warning="#b48d59",
    danger="#bb7c7c",
    note="#4a3f30",
    shadow="#00000040",
)


def palette_for(mode: str) -> ThemePalette:
    return DARK if mode == "dark" else LIGHT


def qml_tokens(mode: str) -> dict[str, str]:
    native = load_theme(mode)
    if native:
        return native
    palette = palette_for(mode)
    return {
        "background": palette.background,
        "workspace": palette.workspace,
        "workspaceTint": palette.workspace_tint,
        "chrome": palette.chrome,
        "chromeAlt": palette.chrome_alt,
        "panel": palette.panel,
        "panelAlt": palette.panel_alt,
        "panelRaised": palette.panel_raised,
        "panelInset": palette.panel_inset,
        "panelHover": palette.panel_hover,
        "panelFocus": palette.panel_focus,
        "text": palette.text,
        "textMuted": palette.text_muted,
        "textSoft": palette.text_soft,
        "border": palette.border,
        "borderStrong": palette.border_strong,
        "accent": palette.accent,
        "anchor": palette.anchor,
        "accentHover": palette.accent_hover,
        "accentSoft": palette.accent_soft,
        "accentSurface": palette.accent_surface,
        "accentPanel": palette.accent_panel,
        "accentOutline": palette.accent_outline,
        "selection": palette.selection,
        "success": palette.success,
        "warning": palette.warning,
        "danger": palette.danger,
        "note": palette.note,
        "shadow": palette.shadow,
        "mode": mode,
    }


def base_stylesheet(mode: str) -> str:
    palette = palette_for(mode)
    return f"""
    QWidget {{
        background: {palette.workspace};
        color: {palette.text};
        font-family: 'Microsoft YaHei UI';
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
        padding: 4px 8px;
        border-radius: 4px;
        background: {palette.panel_raised};
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
    """
