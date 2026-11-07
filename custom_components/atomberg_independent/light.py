"""Home Assistant light entity for supported Atomberg fan lights."""

from __future__ import annotations

from typing import Callable

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import FanDevice, FanManager
from .entity import AtombergEntity, setup_device_entities
from .models import Capability


class AtombergLight(AtombergEntity, LightEntity):
    """Fan under-light with only the reported supported controls."""

    @property
    def supported_color_modes(self) -> set[ColorMode]:
        """Expose brightness only for series with that capability."""
        if self._supports_brightness:
            return {ColorMode.BRIGHTNESS}
        return {ColorMode.ONOFF}

    @property
    def _supports_brightness(self) -> bool:
        return (
            Capability.LIGHT_BRIGHTNESS in self.device.profile.capabilities
            and self.device.brightness is not None
        )

    @property
    def color_mode(self) -> ColorMode:
        """Return the single supported light color mode."""
        if self._supports_brightness:
            return ColorMode.BRIGHTNESS
        return ColorMode.ONOFF

    @property
    def available(self) -> bool:
        """Require a reported LED state before exposing this entity as available."""
        return super().available and self.device.led is not None

    @property
    def is_on(self) -> bool:
        """Return reported LED state."""
        return self.device.led is True

    @property
    def brightness(self) -> int | None:
        """Return brightness in Home Assistant's 0-255 scale."""
        if self.device.brightness is None:
            return None
        return round(self.device.brightness * 255 / 100)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on the LED and optionally set its brightness."""
        fields: dict[str, bool | int] = {"led": True}
        brightness = kwargs.get("brightness")
        if brightness is not None:
            if not self._supports_brightness:
                raise ValueError("Brightness is not supported by this fan")
            if not isinstance(brightness, int) or isinstance(brightness, bool):
                raise ValueError("Brightness must be an integer")
            if not 0 <= brightness <= 255:
                raise ValueError("Brightness must be between 0 and 255")
            fields["brightness"] = round(brightness * 100 / 255)
        self.manager.send_command(self.device, **fields)

    async def async_turn_off(self, **_kwargs) -> None:
        """Turn off the LED."""
        self.manager.send_command(self.device, led=False)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up light entities only for models with a light capability."""
    manager: FanManager = hass.data[DOMAIN][entry.entry_id]

    def create_entity(
        manager: FanManager, device: FanDevice
    ) -> AtombergLight | None:
        if Capability.LIGHT_POWER not in device.profile.capabilities:
            return None
        return AtombergLight(manager, device, "light", "Light")

    setup_device_entities(manager, async_add_entities, create_entity)
