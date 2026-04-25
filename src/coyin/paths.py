from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import sys


def app_root() -> Path:
    bundle_root = getattr(sys, "_MEIPASS", "")
    if bundle_root:
        return Path(bundle_root)
    return Path(__file__).resolve().parents[2]


def user_data_root() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
    return base / "Coyin"


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
    banner_assets: Path
    banner_custom: Path

    @classmethod
    def discover(cls) -> "AppPaths":
        root = app_root()
        runtime = user_data_root() if getattr(sys, "frozen", False) else root / "runtime"
        drafts = runtime / "drafts"
        exports = runtime / "exports"
        downloads = runtime / "downloads"
        latex_runs = runtime / "latex"
        banner_assets = (runtime / "default_banners") if getattr(sys, "frozen", False) else (root / "assets" / "banners")
        banner_custom = runtime / "banner" / "custom"
        for path in (runtime, drafts, exports, downloads, latex_runs, banner_assets, banner_custom):
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
            banner_assets=banner_assets,
            banner_custom=banner_custom,
        )
