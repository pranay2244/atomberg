"""Home Assistant select for Atomberg fan timers."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import FanDevice, FanManager
from .entity import AtombergEntity, setup_device_entities
from .models import Capability
from .protocol import timer_hours_to_command_index

TIMER_OPTIONS = ("Off", "1 hour", "2 hours", "3 hours", "6 hours")
TIMER_VALUES = {"Off": 0, "1 hour": 1, "2 hours": 2, "3 hours": 3, "6 hours": 6}


class AtombergTimerSelect(AtombergEntity, SelectEntity):
    """Select for the fan auto-off timer."""

    _attr_options = list(TIMER_OPTIONS)

    @property
    def available(self) -> bool:
        """Require a reported timer state."""
        return super().available and self.device.timer is not None

    @property
    def current_option(self) -> str | None:
        """Return the reported timer value."""
        if self.device.timer is None:
            return None
        return {
            0: "Off",
            1: "1 hour",
            2: "2 hours",
            3: "3 hours",
            6: "6 hours",
        }.get(self.device.timer)

    async def async_select_option(self, option: str) -> None:
        """Set a validated timer option."""
        if option not in TIMER_VALUES:
            raise ValueError("Unsupported timer option")
        timer_index = timer_hours_to_command_index(TIMER_VALUES[option])
        self.manager.send_command(self.device, timer=timer_index)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[FanManager],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up timer selects only for supported models."""
    manager = entry.runtime_data

    def create_entity(
        manager: FanManager, device: FanDevice
    ) -> AtombergTimerSelect | None:
        if Capability.OFF_TIMER not in device.profile.capabilities:
            return None
        return AtombergTimerSelect(manager, device, "timer", "Off timer")

    setup_device_entities(manager, async_add_entities, create_entity)
