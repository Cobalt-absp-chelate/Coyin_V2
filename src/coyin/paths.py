from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    root: Path
    assets: Path
    qml: Path
    plugins: Path
    templates: Path
    runtime: Path
    workspace_file: Path
    drafts: Path
    exports: Path
    downloads: Path
    latex_runs: Path

    @classmethod
    def discover(cls) -> "AppPaths":
        root = Path(__file__).resolve().parents[2]
        runtime = root / "runtime"
        drafts = runtime / "drafts"
        exports = runtime / "exports"
        downloads = runtime / "downloads"
        latex_runs = runtime / "latex"
        for path in (runtime, drafts, exports, downloads, latex_runs):
            path.mkdir(parents=True, exist_ok=True)
        return cls(
            root=root,
            assets=root / "assets",
            qml=root / "src" / "coyin" / "qt" / "qml",
            plugins=root / "plugins",
            templates=root / "templates",
            runtime=runtime,
            workspace_file=runtime / "workspace.json",
            drafts=drafts,
            exports=exports,
            downloads=downloads,
            latex_runs=latex_runs,
        )
