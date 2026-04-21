from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, Property, Signal, Slot

from coyin.native.bridge import load_shell_schema


@dataclass(frozen=True, slots=True)
class PageEntry:
    page_id: str
    title: str
    short: str = ""


class ShellChromeController(QObject):
    currentPageChanged = Signal()
    chromeChanged = Signal()

    def __init__(self):
        super().__init__()
        schema = load_shell_schema() or {}
        primary = schema.get("primaryPages", [])
        utility = schema.get("utilityPages", [])
        self._primary_entries = [PageEntry(**entry) for entry in primary] or [
            PageEntry("home", "工作台", "工"),
            PageEntry("library", "资料库", "库"),
            PageEntry("search", "搜索", "搜"),
            PageEntry("analysis", "分析", "析"),
        ]
        self._utility_entries = [PageEntry(**entry) for entry in utility] or [PageEntry("settings", "设置", "设")]
        self._entries = self._primary_entries + self._utility_entries
        self._page_titles = {entry.page_id: entry.title for entry in self._entries}
        self._page_order = [entry.page_id for entry in self._entries]
        self._current_page = "home"

    @Property(str, notify=currentPageChanged)
    def currentPage(self) -> str:
        return self._current_page

    @Property(int, notify=currentPageChanged)
    def currentIndex(self) -> int:
        return self._page_order.index(self._current_page)

    @Property(str, notify=currentPageChanged)
    def currentTitle(self) -> str:
        return self._page_titles.get(self._current_page, "工作台")

    @Property(str, notify=currentPageChanged)
    def currentSubtitle(self) -> str:
        return ""

    @Property("QVariantList", notify=currentPageChanged)
    def primaryPageEntries(self):
        return [
            {
                "page_id": entry.page_id,
                "title": entry.title,
                "short": entry.short or entry.title[:1],
            }
            for entry in self._primary_entries
        ]

    @Property("QVariantList", notify=currentPageChanged)
    def utilityPageEntries(self):
        return [{"page_id": entry.page_id, "title": entry.title} for entry in self._utility_entries]

    @Slot(int)
    def setCurrentIndex(self, index: int) -> None:
        if 0 <= index < len(self._page_order):
            self.setCurrentPage(self._page_order[index])

    @Slot(str)
    def setCurrentPage(self, page_id: str) -> None:
        if page_id not in self._page_order or page_id == self._current_page:
            return
        self._current_page = page_id
        self.currentPageChanged.emit()
        self.chromeChanged.emit()
