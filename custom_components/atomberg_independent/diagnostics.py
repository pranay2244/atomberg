"""Privacy-safe diagnostics for Atomberg Independent."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import __version__ as HOME_ASSISTANT_VERSION
from homeassistant.core import HomeAssistant

from .const import INTEGRATION_STATUS, INTEGRATION_VERSION


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, str | int | list[str]]:
    """Return readiness information without device or network identifiers."""
    return {
        "status": INTEGRATION_STATUS,
        "integration_version": INTEGRATION_VERSION,
        "config_entry_version": entry.version,
        "config_entry_minor_version": entry.minor_version,
        "home_assistant_version": HOME_ASSISTANT_VERSION,
        "verified_models": [],
        "implemented_transports": [],
    }
