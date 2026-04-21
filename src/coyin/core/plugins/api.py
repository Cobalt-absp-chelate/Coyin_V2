from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class PluginManifest:
    plugin_id: str
    name: str
    version: str
    author: str
    description: str
    builtin: bool = False
    default_enabled: bool = False
    capabilities: list[str] = field(default_factory=list)
    config_schema: dict[str, Any] = field(default_factory=dict)
    module: str = "plugin"


class PluginContext:
    def __init__(self, services: dict[str, Any]):
        self.services = services
        self.commands: dict[str, Callable[..., Any]] = {}
        self.analysis_postprocessors: list[Callable[[dict[str, Any]], dict[str, Any]]] = []
        self.search_postprocessors: list[Callable[[list[dict[str, Any]]], list[dict[str, Any]]]] = []
        self.writer_action_factories: list[Callable[[], list[dict[str, Any]]]] = []
        self.document_import_hooks: list[Callable[[dict[str, Any]], None]] = []

    def register_command(self, name: str, handler: Callable[..., Any]) -> None:
        self.commands[name] = handler

    def register_analysis_postprocessor(self, handler: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        self.analysis_postprocessors.append(handler)

    def register_search_postprocessor(self, handler: Callable[[list[dict[str, Any]]], list[dict[str, Any]]]) -> None:
        self.search_postprocessors.append(handler)

    def register_writer_actions(self, handler: Callable[[], list[dict[str, Any]]]) -> None:
        self.writer_action_factories.append(handler)

    def register_document_import_hook(self, handler: Callable[[dict[str, Any]], None]) -> None:
        self.document_import_hooks.append(handler)
