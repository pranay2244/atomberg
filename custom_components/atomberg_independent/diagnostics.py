"""Privacy-safe diagnostics for Atomberg Independent."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import INTEGRATION_STATUS


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, str | list[str]]:
    """Return readiness information without device or network identifiers."""
    return {
        "status": INTEGRATION_STATUS,
        "verified_models": [],
        "implemented_transports": [],
    }
