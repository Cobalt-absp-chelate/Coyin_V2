from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
LOCAL_PYTHON = ROOT / ".coyin_env" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")


def _reexec_into_local_runtime() -> None:
    if getattr(sys, "frozen", False):
        return
    if os.environ.get("COYIN_LOCAL_RUNTIME") == "1":
        return
    if not LOCAL_PYTHON.exists():
        return
    current = Path(sys.executable).resolve()
    target = LOCAL_PYTHON.resolve()
    if current == target:
        os.environ["COYIN_LOCAL_RUNTIME"] = "1"
        return
    env = dict(os.environ)
    env["COYIN_LOCAL_RUNTIME"] = "1"
    raise SystemExit(subprocess.call([str(target), str(ROOT / "run.py")], env=env, cwd=str(ROOT)))


_reexec_into_local_runtime()

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from coyin.main import main


if __name__ == "__main__":
    raise SystemExit(main())
