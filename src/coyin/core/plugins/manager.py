from __future__ import annotations

import importlib.util
import json
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal

from coyin.core.plugins.api import PluginContext, PluginManifest
from coyin.core.workspace.service import WorkspaceService


class PluginManager(QObject):
    changed = Signal()

    def __init__(self, plugin_root: Path, workspace: WorkspaceService, services: dict[str, Any]):
        super().__init__()
        self.plugin_root = plugin_root
        self.workspace = workspace
        self.services = services
        self.context = PluginContext(services)
        self._manifests: list[PluginManifest] = []
        self._instances: dict[str, Any] = {}
        self._errors: dict[str, str] = {}

    def discover(self) -> list[PluginManifest]:
        manifests: list[PluginManifest] = []
        for manifest_path in self.plugin_root.glob("builtin/*/manifest.json"):
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifests.append(PluginManifest(**payload))
        self._manifests = sorted(manifests, key=lambda item: item.name.lower())
        return list(self._manifests)

    def manifests(self) -> list[PluginManifest]:
        return list(self._manifests)

    def enable(self, plugin_id: str) -> tuple[bool, str]:
        manifest = next((item for item in self._manifests if item.plugin_id == plugin_id), None)
        if not manifest:
            return False, "插件未找到"
        if plugin_id in self._instances:
            return True, ""
        plugin_dir = self.plugin_root / "builtin" / plugin_id
        entry = plugin_dir / f"{manifest.module}.py"
        try:
            spec = importlib.util.spec_from_file_location(f"coyin_plugin_{plugin_id}", entry)
            if not spec or not spec.loader:
                raise RuntimeError("无法加载插件入口")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            plugin = module.create_plugin()
            plugin.on_load(self.context)
            plugin.on_enable(self.context)
            self._instances[plugin_id] = plugin
            self._errors.pop(plugin_id, None)
            self.workspace.set_plugin_enabled(plugin_id, True)
            self.changed.emit()
            return True, ""
        except Exception as exc:
            message = f"{exc}\n{traceback.format_exc(limit=3)}"
            self._errors[plugin_id] = message
            self.workspace.set_plugin_enabled(plugin_id, False, load_error=message)
            self.changed.emit()
            return False, message

    def disable(self, plugin_id: str) -> None:
        plugin = self._instances.pop(plugin_id, None)
        if plugin:
            try:
                plugin.on_disable(self.context)
            except Exception:
                pass
        self.workspace.set_plugin_enabled(plugin_id, False)
        self.changed.emit()

    def error_for(self, plugin_id: str) -> str:
        return self._errors.get(plugin_id, "")

    def is_enabled(self, plugin_id: str) -> bool:
        return plugin_id in self._instances

    def analysis_postprocessors(self):
        return list(self.context.analysis_postprocessors)

    def search_postprocessors(self):
        return list(self.context.search_postprocessors)

    def writer_action_factories(self):
        return list(self.context.writer_action_factories)
