from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AnalysisReport:
    title: str
    summary: str
    contributions: list[str] = field(default_factory=list)
    experiments: list[dict[str, str]] = field(default_factory=list)
    method_steps: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    comparison_rows: list[dict[str, str]] = field(default_factory=list)
    reading_note: str = ""
    latex_snippet: str = ""
    raw_fields: dict[str, str] = field(default_factory=dict)
