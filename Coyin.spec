# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

project_root = Path.cwd()
local_miktex = Path(r"C:\MikTeX")
datas = [
    ('assets', 'assets'),
    ('templates', 'templates'),
    ('plugins', 'plugins'),
    ('src/coyin/qt/qml', 'src/coyin/qt/qml'),
]
if local_miktex.exists():
    datas.append((str(local_miktex), 'latex_runtime\\MiKTeX'))


a = Analysis(
    ['run.py'],
    pathex=['src'],
    binaries=[('native\\build\\Release\\coyin_native.dll', 'build\\native-qt\\Release')],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Coyin',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\icons\\coyin_mark.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Coyin',
)
