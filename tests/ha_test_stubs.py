"""Minimal Home Assistant modules for exercising entities without HA installed."""

from __future__ import annotations

import importlib.util
import sys
from enum import Enum, IntFlag
from types import ModuleType
from typing import Callable


def ensure_homeassistant_modules() -> None:
    """Install import-compatible stubs only when Home Assistant is unavailable."""
    if "homeassistant" in sys.modules:
        return
    try:
        if importlib.util.find_spec("homeassistant") is not None:
            return
    except (ImportError, ValueError):
        return

    homeassistant = ModuleType("homeassistant")
    homeassistant.__path__ = []
    core = ModuleType("homeassistant.core")
    core.HomeAssistant = type("HomeAssistant", (), {})

    helpers = ModuleType("homeassistant.helpers")
    helpers.__path__ = []
    event = ModuleType("homeassistant.helpers.event")
    event.async_track_time_interval = lambda *_args, **_kwargs: lambda: None
    device_registry = ModuleType("homeassistant.helpers.device_registry")
    device_registry.DeviceInfo = dict
    entity = ModuleType("homeassistant.helpers.entity")

    class Entity:
        def async_write_ha_state(self) -> None:
            pass

    entity.Entity = Entity
    entity_platform = ModuleType("homeassistant.helpers.entity_platform")
    entity_platform.AddEntitiesCallback = Callable

    components = ModuleType("homeassistant.components")
    components.__path__ = []
    light = ModuleType("homeassistant.components.light")

    class ColorMode(str, Enum):
        ONOFF = "onoff"
        BRIGHTNESS = "brightness"

    class LightEntityFeature(IntFlag):
        EFFECT = 1

    class LightEntity:
        pass

    light.ColorMode = ColorMode
    light.LightEntity = LightEntity
    light.LightEntityFeature = LightEntityFeature

    config_entries = ModuleType("homeassistant.config_entries")
    config_entries.ConfigEntry = type("ConfigEntry", (), {})
    exceptions = ModuleType("homeassistant.exceptions")

    class ConfigEntryNotReady(Exception):
        pass

    exceptions.ConfigEntryNotReady = ConfigEntryNotReady

    homeassistant.core = core
    homeassistant.helpers = helpers
    homeassistant.components = components
    helpers.event = event
    helpers.device_registry = device_registry
    helpers.entity = entity
    helpers.entity_platform = entity_platform
    components.light = light
    homeassistant.config_entries = config_entries
    homeassistant.exceptions = exceptions

    sys.modules.update(
        {
            "homeassistant": homeassistant,
            "homeassistant.core": core,
            "homeassistant.helpers": helpers,
            "homeassistant.helpers.event": event,
            "homeassistant.helpers.device_registry": device_registry,
            "homeassistant.helpers.entity": entity,
            "homeassistant.helpers.entity_platform": entity_platform,
            "homeassistant.components": components,
            "homeassistant.components.light": light,
            "homeassistant.config_entries": config_entries,
            "homeassistant.exceptions": exceptions,
        }
    )
