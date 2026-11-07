"""Privacy-safe diagnostics for Atomberg Independent."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import __version__ as HOME_ASSISTANT_VERSION
from homeassistant.core import HomeAssistant

from .const import INTEGRATION_STATUS, INTEGRATION_VERSION
from .coordinator import FanManager


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry[FanManager]
) -> dict[str, Any]:
    """Return readiness information without raw identifiers or network addresses."""
    manager = getattr(entry, "runtime_data", None)
    devices = manager.devices.values() if manager else ()
    return {
        "status": INTEGRATION_STATUS,
        "integration_version": INTEGRATION_VERSION,
        "config_entry_version": entry.version,
        "config_entry_minor_version": entry.minor_version,
        "home_assistant_version": HOME_ASSISTANT_VERSION,
        "device_count": len(manager.devices) if manager else 0,
        "devices": [
            {
                "series": device.series or "unknown",
                "available": device.available,
                "profile_hint": device.profile.name,
            }
            for device in devices
        ],
        "implemented_transports": ["Wi-Fi UDP"],
    }
