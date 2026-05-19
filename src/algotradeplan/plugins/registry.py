"""Dynamic plugin discovery and loading helpers."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib import import_module
from pkgutil import walk_packages
from typing import Any, Protocol


@dataclass(frozen=True)
class PluginDescriptor:
    plugin_id: str
    module: str
    qualname: str
    class_name: str
    category: str


@dataclass(frozen=True)
class PluginDiscoveryIssue:
    module: str
    reason: str


class PluginClass(Protocol):
    plugin_id: str


_CATEGORY_ALIASES = {
    "strategies": "strategy",
    "connectors": "execution_connector",
}


def _resolve_category(module_parts: list[str]) -> str:
    raw = module_parts[3] if len(module_parts) > 3 else "unknown"
    return _CATEGORY_ALIASES.get(raw, raw)


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
        except ImportError as exc:  # pragma: no cover - importability depends on optional extras
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

            category = _resolve_category(module_parts)
            descriptor = PluginDescriptor(
                plugin_id=plugin_id,
                module=module_name,
                qualname=f"{module_name}.{attr.__name__}",
                class_name=attr.__name__,
                category=category,
            )
            existing = registry.get(plugin_id)
            if existing and existing.qualname != descriptor.qualname:
                raise ValueError(
                    f"duplicate plugin_id '{plugin_id}' detected in {existing.qualname} and {descriptor.qualname}"
                )
            registry[plugin_id] = descriptor
    return registry, issues


@lru_cache(maxsize=None)
def _cached_discovery_result(
    root_package: str,
) -> tuple[dict[str, PluginDescriptor], tuple[PluginDiscoveryIssue, ...]]:
    registry, issues = discover_plugins(root_package=root_package)
    return registry, tuple(issues)


def discovery_issues(root_package: str = "src.algotradeplan.plugins") -> list[PluginDiscoveryIssue]:
    _, issues = _cached_discovery_result(root_package)
    return list(issues)


def clear_discovery_cache() -> None:
    _cached_discovery_result.cache_clear()


def load_plugin_class(
    plugin_id: str,
    root_package: str = "src.algotradeplan.plugins",
) -> type[PluginClass]:
    registry, _ = _cached_discovery_result(root_package)
    descriptor = registry.get(plugin_id)
    if descriptor is None:
        raise KeyError(f"plugin_id '{plugin_id}' not found")
    module = import_module(descriptor.module)
    plugin_class = getattr(module, descriptor.class_name, None)
    if plugin_class is None:
        raise KeyError(
            f"class '{descriptor.class_name}' for plugin_id '{plugin_id}' not found in {descriptor.module}"
        )
    return plugin_class
