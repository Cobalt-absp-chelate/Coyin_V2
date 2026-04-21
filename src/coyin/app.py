from __future__ import annotations

import os
import sys

from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from coyin.bootstrap import build_services
from coyin.paths import AppPaths
from coyin.qt.controllers.main_controller import MainController
from coyin.qt.controllers.shell_state import ShellChromeController
from coyin.qt.quick.chrome_effects import register_qml_types


def main() -> int:
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
    app = QApplication(sys.argv)
    app.setApplicationName("Coyin")

    paths = AppPaths.discover()
    icon_path = paths.assets / "icons" / "coyin_mark.svg"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    services = build_services(paths)
    controller = MainController(services)
    shell_controller = ShellChromeController()
    controller.setParent(app)
    shell_controller.setParent(app)

    register_qml_types()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("mainController", controller)
    engine.rootContext().setContextProperty("shellController", shell_controller)
    engine.load(str(paths.qml / "Main.qml"))

    if not engine.rootObjects():
        return 1
    return app.exec()
