"""Dynamic plugin discovery and loading helpers."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pkgutil import walk_packages
from typing import Any


@dataclass(frozen=True)
class PluginDescriptor:
    plugin_id: str
    module: str
    qualname: str
    category: str


@dataclass(frozen=True)
class PluginDiscoveryIssue:
    module: str
    reason: str


def discover_plugins(
    root_package: str = "src.algotradeplan.plugins",
) -> tuple[dict[str, PluginDescriptor], list[PluginDiscoveryIssue]]:
    package = import_module(root_package)
    registry: dict[str, PluginDescriptor] = {}
    issues: list[PluginDiscoveryIssue] = []

    for module_info in walk_packages(package.__path__, f"{root_package}."):
        module_name = module_info.name
        module_parts = module_name.split(".")
        try:
            module = import_module(module_name)
        except Exception as exc:  # pragma: no cover - importability depends on optional extras
            issues.append(PluginDiscoveryIssue(module=module_name, reason=str(exc)))
            continue

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if not isinstance(attr, type):
                continue
            if getattr(attr, "__module__", "") != module_name:
                continue
            plugin_id = getattr(attr, "plugin_id", None)
            if not isinstance(plugin_id, str) or not plugin_id:
                continue

            category = module_parts[3] if len(module_parts) > 3 else "unknown"
            descriptor = PluginDescriptor(
                plugin_id=plugin_id,
                module=module_name,
                qualname=f"{module_name}.{attr.__name__}",
                category=category,
            )
            existing = registry.get(plugin_id)
            if existing and existing.qualname != descriptor.qualname:
                raise ValueError(
                    f"duplicate plugin_id '{plugin_id}' detected in {existing.qualname} and {descriptor.qualname}"
                )
            registry[plugin_id] = descriptor
    return registry, issues


def load_plugin_class(plugin_id: str, root_package: str = "src.algotradeplan.plugins") -> type[Any]:
    registry, _ = discover_plugins(root_package=root_package)
    descriptor = registry.get(plugin_id)
    if descriptor is None:
        raise KeyError(f"plugin_id '{plugin_id}' not found")
    module = import_module(descriptor.module)
    return getattr(module, descriptor.qualname.rsplit(".", 1)[-1])
