from __future__ import annotations

from dataclasses import dataclass

from coyin.core.analysis.service import AnalysisService
from coyin.core.annotations.store import AnnotationStore
from coyin.core.commands.bus import CommandBus
from coyin.core.documents.adapters import DocumentAdapterRegistry
from coyin.core.documents.repository import DocumentRepository
from coyin.core.exporters.base import DraftExporter
from coyin.core.plugins.manager import PluginManager
from coyin.core.render.coordinator import RenderCoordinator
from coyin.core.resources.catalog import ResourceCatalog
from coyin.core.search.service import SearchService
from coyin.core.tasks import TaskCenter, WorkSchedulerCore
from coyin.core.workspace.service import WorkspaceService
from coyin.core.workspace.window_registry import WindowRegistry
from coyin.paths import AppPaths


@dataclass(slots=True)
class ServiceHub:
    paths: AppPaths
    workspace: WorkspaceService
    repository: DocumentRepository
    annotation_store: AnnotationStore
    command_bus: CommandBus
    render_coordinator: RenderCoordinator
    resource_catalog: ResourceCatalog
    search_service: SearchService
    plugin_manager: PluginManager
    analysis_service: AnalysisService
    exporter: DraftExporter
    task_center: TaskCenter
    scheduler: WorkSchedulerCore
    window_registry: WindowRegistry


def build_services(paths: AppPaths) -> ServiceHub:
    workspace = WorkspaceService(paths.workspace_file)
    repository = DocumentRepository(DocumentAdapterRegistry())
    annotation_store = AnnotationStore(paths.runtime / "annotations.json")
    command_bus = CommandBus()
    render_coordinator = RenderCoordinator()
    resource_catalog = ResourceCatalog(paths.runtime / "resources.json")
    search_service = SearchService()
    task_center = TaskCenter()
    scheduler = WorkSchedulerCore()
    window_registry = WindowRegistry()
    plugin_manager = PluginManager(
        paths.plugins,
        workspace,
        services={
            "workspace": workspace,
            "search_service": search_service,
            "resource_catalog": resource_catalog,
        },
    )
    plugin_manager.discover()
    for state in workspace.state.plugin_states:
        if state.enabled:
            plugin_manager.enable(state.plugin_id)
    analysis_service = AnalysisService(plugin_manager)
    exporter = DraftExporter()
    return ServiceHub(
        paths=paths,
        workspace=workspace,
        repository=repository,
        annotation_store=annotation_store,
        command_bus=command_bus,
        render_coordinator=render_coordinator,
        resource_catalog=resource_catalog,
        search_service=search_service,
        plugin_manager=plugin_manager,
        analysis_service=analysis_service,
        exporter=exporter,
        task_center=task_center,
        scheduler=scheduler,
        window_registry=window_registry,
    )
