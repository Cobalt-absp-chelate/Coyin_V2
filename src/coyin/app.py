from __future__ import annotations

import os
import sys

from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from coyin.bootstrap import build_services
from coyin.native.bridge import register_qml_types_native
from coyin.paths import AppPaths
from coyin.qt.controllers.main_controller import MainController
from coyin.qt.controllers.shell_state import ShellChromeController
from coyin.qt.quick.chrome_effects import register_qml_types
from coyin.qt.widgets.parallax_banner import ensure_default_banner_assets, register_qml_types as register_banner_qml_types


def _native_chrome_enabled() -> bool:
    disable = os.environ.get("COYIN_DISABLE_NATIVE_CHROME", "").strip().lower()
    if disable in {"1", "true", "yes", "on"}:
        return False

    enable = os.environ.get("COYIN_ENABLE_NATIVE_CHROME", "").strip().lower()
    if enable in {"1", "true", "yes", "on"}:
        return True

    # The current native scenegraph shader path is unstable on Windows/D3D11.
    # Keep the non-visual native helpers available, but default the QML chrome
    # items to the Python fallback until the shader packaging/runtime path is fixed.
    return sys.platform != "win32"


def main() -> int:
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
    os.environ.setdefault("QML_XHR_ALLOW_FILE_READ", "1")
    os.environ.setdefault(
        "QT_LOGGING_RULES",
        "qt.qpa.mime.debug=false;qt.qpa.mime.info=false;qt.qpa.mime.warning=false",
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Coyin")
    app.setOrganizationName("Coyin")
    app.setQuitOnLastWindowClosed(False)

    paths = AppPaths.discover()
    icon_candidates = [
        paths.assets / "icons" / "coyin_mark.ico",
        paths.assets / "icons" / "coyin_mark.png",
        paths.assets / "icons" / "coyin_mark.svg",
    ]
    for icon_path in icon_candidates:
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
            break

    services = build_services(paths)
    ensure_default_banner_assets(paths.banner_assets)
    controller = MainController(services)
    shell_controller = ShellChromeController()
    controller.setParent(app)
    shell_controller.setParent(app)

    if _native_chrome_enabled() and register_qml_types_native():
        pass
    else:
        register_qml_types()
    register_banner_qml_types()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("mainController", controller)
    engine.rootContext().setContextProperty("shellController", shell_controller)
    engine.load(str(paths.qml / "Main.qml"))

    if not engine.rootObjects():
        return 1
    for root in engine.rootObjects():
        try:
            root.destroyed.connect(app.quit)
        except Exception:
            continue
    return app.exec()
