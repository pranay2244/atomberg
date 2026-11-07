"""Set up the Atomberg Independent integration foundation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

LOGGER = logging.getLogger(__name__)


async def async_setup(_hass: HomeAssistant, _config: dict) -> bool:
    """Set up the integration from YAML (not supported)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Start local UDP state reception and forward supported platforms."""
    from homeassistant.exceptions import ConfigEntryNotReady

    from .const import DOMAIN, PLATFORMS
    from .coordinator import FanManager

    manager = FanManager(hass)
    try:
        await manager.async_start()
    except OSError as err:
        LOGGER.exception("Unable to start the Atomberg local UDP listener")
        raise ConfigEntryNotReady("Unable to listen for local fan state") from err

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = manager
    platforms_loaded = False
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        platforms_loaded = True
    finally:
        if not platforms_loaded:
            await manager.async_stop()
            hass.data[DOMAIN].pop(entry.entry_id, None)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Stop the listener after Home Assistant unloads the platforms."""
    from .const import DOMAIN, PLATFORMS

    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    manager = hass.data[DOMAIN].pop(entry.entry_id)
    await manager.async_stop()
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)
    return True
