"""Home Assistant switches for supported Atomberg fan controls."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import FanDevice, FanManager
from .entity import AtombergEntity, setup_device_entities
from .models import Capability


class AtombergSleepSwitch(AtombergEntity, SwitchEntity):
    """Switch for the fan sleep mode."""

    @property
    def available(self) -> bool:
        """Require a reported sleep state."""
        return super().available and self.device.sleep is not None

    @property
    def is_on(self) -> bool:
        """Return the reported sleep setting."""
        return self.device.sleep is True

    async def async_turn_on(self, **_kwargs) -> None:
        """Enable sleep mode."""
        self.manager.send_command(self.device, sleep=True)

    async def async_turn_off(self, **_kwargs) -> None:
        """Disable sleep mode."""
        self.manager.send_command(self.device, sleep=False)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sleep switches only for supported models."""
    manager: FanManager = hass.data[DOMAIN][entry.entry_id]

    def create_entity(
        manager: FanManager, device: FanDevice
    ) -> AtombergSleepSwitch | None:
        if Capability.SLEEP_MODE not in device.profile.capabilities:
            return None
        return AtombergSleepSwitch(manager, device, "sleep", "Sleep mode")

    setup_device_entities(manager, async_add_entities, create_entity)
