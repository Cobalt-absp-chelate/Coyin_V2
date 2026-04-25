from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from coyin.paths import app_root
from coyin.qt.widgets.theme import palette_for


ICON_DIR = app_root() / "assets" / "icons" / "material" / "outlined"

ACTION_ICON_NAMES = {
    "bold": "format_bold",
    "italic": "format_italic",
    "underline": "format_underlined",
    "highlight": "format_color_fill",
    "clear-format": "format_clear",
    "paste": "paste",
    "copy": "copy",
    "cut": "cut",
    "heading": "title",
    "body": "text_fields",
    "align-left": "format_align_left",
    "align-center": "format_align_center",
    "align-right": "format_align_right",
    "align-justify": "format_align_justify",
    "bullet-list": "format_list_bulleted",
    "number-list": "format_list_numbered",
    "analysis-summary": "summarize",
    "analysis-contrib": "checklist",
    "method-scaffold": "functions",
    "to-latex": "code",
    "insert-image": "add_photo_alternate",
    "insert-textbox": "short_text",
    "insert-shape": "rectangle",
    "insert-rule": "horizontal_rule",
    "insert-table": "table_chart",
    "insert-reference": "add_link",
    "insert-figure-caption": "image",
    "insert-table-caption": "table_rows",
    "insert-comment": "comment",
    "space-before": "line_weight",
    "space-after": "line_weight",
    "indent-increase": "format_indent_increase",
    "indent-decrease": "format_indent_decrease",
    "page-break": "insert_page_break",
    "reference-placeholder": "link",
    "reference-list": "subject",
    "export-pdf": "picture_as_pdf",
    "export-docx": "description",
    "export-markdown": "article",
    "find": "find_in_page",
    "zoom-in": "zoom_in",
    "zoom-out": "zoom_out",
    "font-family": "text_format",
    "font-size": "format_size",
    "line-spacing": "format_line_spacing",
    "page-layout": "article",
    "page-orientation": "article",
    "indent-left": "format_indent_decrease",
    "indent-right": "format_indent_increase",
    "toggle-inspector": "view_sidebar",
    "reader-left": "menu",
    "reader-right": "view_sidebar",
    "reader-fit-page": "fit_screen",
    "reader-fit-width": "width_full",
    "reader-one-page": "article",
    "reader-two-page": "view_sidebar",
    "reader-translate": "translate",
    "reader-note": "notes",
    "reader-delete": "delete",
    "reader-edit-note": "edit_note",
    "latex-compile": "article",
    "latex-sync": "view_sidebar",
    "latex-export": "picture_as_pdf",
    "latex-find": "find_in_page",
    "latex-reload": "menu",
    "latex-writer": "notes",
    "markdown-outline": "view_headline",
    "markdown-preview": "article",
    "markdown-quote": "comment",
    "markdown-task": "checklist",
    "markdown-link": "add_link",
    "markdown-code": "code",
    "more": "more_horiz",
}

_ICON_CACHE: dict[tuple[str, str, int], QIcon] = {}


def _svg_bytes(icon_name: str, color: QColor) -> bytes | None:
    path = ICON_DIR / f"{icon_name}.svg"
    if not path.exists():
        return None
    payload = path.read_text(encoding="utf-8")
    color_hex = color.name(QColor.NameFormat.HexRgb)
    if "<svg" in payload:
        payload = payload.replace("<svg ", f'<svg fill="{color_hex}" ', 1)
    return payload.encode("utf-8")


def themed_icon(action_id: str, theme_mode: str = "light", size: int = 22, accent: bool = True) -> QIcon:
    icon_name = ACTION_ICON_NAMES.get(action_id, action_id)
    palette = palette_for(theme_mode)
    color = QColor(palette.anchor if accent else palette.text_muted)
    for candidate in (icon_name, "more_horiz"):
        cache_key = (candidate, color.name(QColor.NameFormat.HexRgb), int(size))
        cached = _ICON_CACHE.get(cache_key)
        if cached is not None:
            return cached
        svg_bytes = _svg_bytes(candidate, color)
        if svg_bytes is None:
            continue
        renderer = QSvgRenderer(QByteArray(svg_bytes))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        icon = QIcon(pixmap)
        _ICON_CACHE[cache_key] = icon
        return icon
    return QIcon()
