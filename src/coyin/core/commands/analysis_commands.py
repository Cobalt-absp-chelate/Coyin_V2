from __future__ import annotations

import shutil
from copy import deepcopy
from pathlib import Path

from PySide6.QtGui import QUndoCommand

from coyin.core.common import now_iso
from coyin.core.workspace.service import WorkspaceService
from coyin.core.workspace.state import AnalysisReportState, LatexSessionState, ResearchNote


class SaveAnalysisToNoteCommand(QUndoCommand):
    def __init__(self, workspace: WorkspaceService, report: AnalysisReportState):
        super().__init__("保存分析到研究笔记")
        self.workspace = workspace
        self.report = deepcopy(report)
        self.note: ResearchNote | None = None
        self._link_id = ""

    def redo(self) -> None:
        if self.note is None:
            self.note = self.workspace.add_note(
                title=f"{self.report.title} 阅读笔记",
                content=self.report.reading_note or self.report.summary,
                linked_document_id=self.report.document_id,
                linked_report_id=self.report.report_id,
            )
            link = self.workspace.link_artifacts(
                source_kind="analysis_report",
                source_id=self.report.report_id,
                target_kind="note",
                target_id=self.note.note_id,
                relation_kind="analysis_to_note",
                label="分析转研究笔记",
            )
            self._link_id = link.link_id
        else:
            self.workspace.state.notes.insert(0, deepcopy(self.note))
            if self._link_id:
                link = self.workspace.link_artifacts(
                    source_kind="analysis_report",
                    source_id=self.report.report_id,
                    target_kind="note",
                    target_id=self.note.note_id,
                    relation_kind="analysis_to_note",
                    label="分析转研究笔记",
                    meta={"restored_from": self._link_id},
                )
                self._link_id = link.link_id
            self.workspace.persist()

    def undo(self) -> None:
        if self.note:
            self.workspace.remove_note(self.note.note_id)
        if self._link_id:
            self.workspace.remove_link(self._link_id)


class CreateLatexSessionCommand(QUndoCommand):
    def __init__(
        self,
        workspace: WorkspaceService,
        session: LatexSessionState,
        initial_text: str,
        link_specs: list[dict] | None = None,
        text: str = "创建 LaTeX 草稿",
    ):
        super().__init__(text)
        self.workspace = workspace
        self.session = deepcopy(session)
        self.initial_text = initial_text
        self.link_specs = list(link_specs or [])
        self._link_ids: list[str] = []

    def redo(self) -> None:
        work_dir = Path(self.session.path)
        work_dir.mkdir(parents=True, exist_ok=True)
        tex_path = work_dir / "main.tex"
        if not tex_path.exists():
            tex_path.write_text(self.initial_text, encoding="utf-8")
        session = self.workspace.register_latex_session(
            title=self.session.title,
            template=self.session.template,
            path=self.session.path,
            linked_document_id=self.session.linked_document_id,
            linked_report_id=self.session.linked_report_id,
            linked_draft_id=self.session.linked_draft_id,
        )
        self.session = deepcopy(session)
        if not self._link_ids:
            for spec in self.link_specs:
                link = self.workspace.link_artifacts(
                    source_kind=spec["source_kind"],
                    source_id=spec["source_id"],
                    target_kind="latex_session",
                    target_id=self.session.session_id,
                    relation_kind=spec["relation_kind"],
                    label=spec.get("label", ""),
                    meta=spec.get("meta", {}),
                )
                self._link_ids.append(link.link_id)
        else:
            restored = []
            for spec, link_id in zip(self.link_specs, self._link_ids):
                link = self.workspace.link_artifacts(
                    source_kind=spec["source_kind"],
                    source_id=spec["source_id"],
                    target_kind="latex_session",
                    target_id=self.session.session_id,
                    relation_kind=spec["relation_kind"],
                    label=spec.get("label", ""),
                    meta={**spec.get("meta", {}), "restored_from": link_id},
                )
                restored.append(link.link_id)
            self._link_ids = restored

    def undo(self) -> None:
        self.workspace.remove_latex_session(self.session.session_id)
        if self._link_ids:
            self.workspace.remove_links(self._link_ids)
        work_dir = Path(self.session.path)
        if work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)
