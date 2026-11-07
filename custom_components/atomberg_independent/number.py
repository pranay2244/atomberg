"""Discrete light intensity number for compatible Atomberg fans."""

from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_LIGHT_HIGH_BRIGHTNESS, CONF_LIGHT_LOW_BRIGHTNESS
from .coordinator import FanDevice, FanManager
from .entity import AtombergEntity, setup_device_entities
from .models import Capability
from .protocol import validate_light_stage_brightness

LOGGER = logging.getLogger(__name__)


class AtombergLightIntensity(AtombergEntity, NumberEntity):
    """Off/low/high light control whose state follows fan broadcasts."""

    _attr_native_min_value = 0
    _attr_native_max_value = 2
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self,
        manager: FanManager,
        device: FanDevice,
        low_brightness: int,
        high_brightness: int,
    ) -> None:
        super().__init__(manager, device, "light_intensity", "Light intensity")
        self._low_brightness = low_brightness
        self._high_brightness = high_brightness

    @property
    def native_value(self) -> float | None:
        """Return only a stage established by the latest device state."""
        if self.device.led is False:
            return 0
        if self.device.led is not True:
            return None
        if self.device.brightness == self._low_brightness:
            return 1
        if self.device.brightness == self._high_brightness:
            return 2
        return None

    @property
    def available(self) -> bool:
        """Require a fan state that maps unambiguously to a configured stage."""
        return super().available and self.native_value is not None

    async def async_set_native_value(self, value: float) -> None:
        """Send a stage command without changing displayed state optimistically."""
        if isinstance(value, bool) or value not in (0, 1, 2):
            raise ValueError("Light intensity must be 0 (off), 1 (low), or 2 (high)")
        if not self.device.available:
            raise RuntimeError("The Atomberg fan is not available on the local network")
        if value == 0:
            self.manager.send_command(self.device, led=False)
            return
        brightness = self._low_brightness if value == 1 else self._high_brightness
        self.manager.send_command(self.device, brightness=brightness)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[FanManager],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up stage controls only when protocol values are configured."""
    manager = entry.runtime_data
    try:
        mapping = validate_light_stage_brightness(
            entry.options.get(CONF_LIGHT_LOW_BRIGHTNESS),
            entry.options.get(CONF_LIGHT_HIGH_BRIGHTNESS),
        )
    except ValueError:
        LOGGER.error("Invalid configured Atomberg light intensity mapping")
        return
    if mapping is None:
        return
    low_brightness, high_brightness = mapping

    def create_entity(
        manager: FanManager, device: FanDevice
    ) -> AtombergLightIntensity | None:
        if Capability.LIGHT_DISCRETE_INTENSITY not in device.profile.capabilities:
            return None
        return AtombergLightIntensity(
            manager,
            device,
            low_brightness,
            high_brightness,
        )

    setup_device_entities(manager, async_add_entities, create_entity)
