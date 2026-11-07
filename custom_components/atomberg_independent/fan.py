"""Home Assistant fan entity for locally discovered Atomberg fans."""

from __future__ import annotations

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import FanDevice, FanManager
from .entity import AtombergEntity, setup_device_entities
from .models import Capability
from .protocol import percentage_to_speed, speed_to_percentage


class AtombergFan(AtombergEntity, FanEntity):
    """Discrete six-speed fan entity."""

    _attr_speed_count = 6

    @property
    def supported_features(self) -> FanEntityFeature:
        """Expose fan controls only when the series profile supports them."""
        features = FanEntityFeature(0)
        if Capability.FAN_SPEED in self.device.profile.capabilities:
            features |= FanEntityFeature.SET_SPEED
        if Capability.FAN_POWER in self.device.profile.capabilities:
            features |= FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
        return features

    @property
    def available(self) -> bool:
        """Require a confirmed power state before reporting the fan as available."""
        return super().available and self.device.power is not None

    @property
    def is_on(self) -> bool:
        """Return reported power state."""
        return self.device.power is True

    @property
    def percentage(self) -> int | None:
        """Return reported speed as a Home Assistant percentage."""
        if self.device.power is False:
            return 0
        if self.device.speed is None:
            return None
        return speed_to_percentage(self.device.speed)

    async def async_turn_on(
        self, percentage: int | None = None, **_kwargs
    ) -> None:
        """Turn on, optionally selecting a speed."""
        if percentage is None:
            self.manager.send_command(self.device, power=True)
            return
        if percentage == 0:
            self.manager.send_command(self.device, power=False)
            return
        speed = percentage_to_speed(percentage)
        self.manager.send_command(self.device, power=True, speed=speed, boost=False)

    async def async_turn_off(self, **_kwargs) -> None:
        """Turn off the fan."""
        self.manager.send_command(self.device, power=False)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set a discrete speed level."""
        if percentage == 0:
            self.manager.send_command(self.device, power=False)
            return
        speed = percentage_to_speed(percentage)
        self.manager.send_command(
            self.device, power=True, speed=speed, boost=False
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[FanManager],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up fan entities as fans are discovered."""
    manager = entry.runtime_data

    def create_entity(manager: FanManager, device: FanDevice) -> AtombergFan:
        return AtombergFan(manager, device, "fan", "Fan")

    setup_device_entities(manager, async_add_entities, create_entity)
