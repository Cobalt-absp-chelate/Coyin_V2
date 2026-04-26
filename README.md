# Coyin

Coyin is a Windows desktop workspace for reading papers, searching references, writing notes, and compiling LaTeX from one place. The UI is built with PySide6 and Qt Quick.

## Local run

```powershell
python run.py
```

The launcher will prefer the local virtual environment in `.coyin_env` when it exists.

## Packaging

```powershell
.\.coyin_env\Scripts\pyinstaller.exe Coyin.spec --noconfirm
```

The packaged app is written to `dist/Coyin/`.

## Bundled LaTeX runtime

`Coyin.spec` bundles a local MiKTeX runtime from `C:\MikTeX` into `latex_runtime\MiKTeX` when that directory is present. The packaged LaTeX window looks for the bundled runtime first, then falls back to a system install.

## Current release

`v0.1.4` tightens the top chrome structure so the banner, nav bar, and main content no longer leave the stray horizontal seams that showed up after the banner height increase.
