"""Set up the Atomberg integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.const import EVENT_HOMEASSISTANT_STOP

from .const import INTEGRATION_VERSION, NAME, PLATFORMS, STATE_PORT

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from .coordinator import FanManager

LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry[FanManager]
) -> bool:
    """Start local UDP state reception and forward supported platforms."""
    from homeassistant.exceptions import ConfigEntryNotReady

    from .coordinator import FanManager

    LOGGER.info(
        "Setting up %s integration (version=%s)",
        NAME,
        INTEGRATION_VERSION,
    )
    if entry.title != NAME:
        hass.config_entries.async_update_entry(entry, title=NAME)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    manager = FanManager(hass)
    try:
        await manager.async_start()
    except OSError as err:
        LOGGER.exception(
            "Unable to bind Atomberg UDP listener on port %d",
            STATE_PORT,
        )
        raise ConfigEntryNotReady("Unable to listen for local fan state") from err

    entry.runtime_data = manager
    platforms_loaded = False
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        platforms_loaded = True
    finally:
        if not platforms_loaded:
            LOGGER.warning(
                "Atomberg platform setup incomplete; stopping UDP listener"
            )
            await manager.async_stop()

    async def _handle_homeassistant_stop(_event: object) -> None:
        LOGGER.info("Home Assistant shutdown detected; stopping Atomberg")
        await manager.async_stop()

    remove_stop_listener = hass.bus.async_listen_once(
        EVENT_HOMEASSISTANT_STOP,
        _handle_homeassistant_stop,
    )
    entry.async_on_unload(remove_stop_listener)
    LOGGER.info(
        "Atomberg integration setup completed (platforms=%s)",
        ", ".join(PLATFORMS),
    )
    return True


async def _async_options_updated(
    hass: HomeAssistant, entry: ConfigEntry[FanManager]
) -> None:
    """Reload platform entities when the configured light mapping changes."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(
    hass: HomeAssistant, entry: ConfigEntry[FanManager]
) -> bool:
    """Stop the listener after Home Assistant unloads the platforms."""
    LOGGER.info("Unloading Atomberg integration")
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        LOGGER.warning(
            "Unable to unload Atomberg platforms; UDP listener remains active"
        )
        return False
    await entry.runtime_data.async_stop()
    LOGGER.info("Atomberg integration unloaded")
    return True
