from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


class LatexHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.command_format = QTextCharFormat()
        self.command_format.setForeground(QColor("#2e5878"))
        self.command_format.setFontWeight(QFont.Weight.DemiBold)

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#7c8b99"))

        self.math_format = QTextCharFormat()
        self.math_format.setForeground(QColor("#9d5b1f"))

        self.patterns = [
            (r"\\[A-Za-z@]+", self.command_format),
            (r"%[^\n]*", self.comment_format),
            (r"\$[^$]+\$", self.math_format),
        ]

    def highlightBlock(self, text: str) -> None:
        import re

        for pattern, text_format in self.patterns:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), text_format)
