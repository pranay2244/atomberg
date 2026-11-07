"""Home Assistant light entity for supported Atomberg fan lights."""

from __future__ import annotations

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import FanDevice, FanManager
from .entity import AtombergEntity, setup_device_entities
from .models import Capability
from .protocol import build_light_commands


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
        return Capability.LIGHT_BRIGHTNESS in self.device.profile.capabilities

    @property
    def effect_list(self) -> list[str] | None:
        """Return supported light modes when the series profile allows them."""
        if Capability.LIGHT_COLOR_MODE not in self.device.profile.capabilities:
            return None
        return ["warm", "cool", "daylight"]

    @property
    def effect(self) -> str | None:
        """Return the reported light mode."""
        return self.device.light_mode

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
        brightness = kwargs.get("brightness")
        brightness_percent = None
        if brightness is not None:
            if not self._supports_brightness:
                raise ValueError("Brightness is not supported by this fan")
            if not isinstance(brightness, int) or isinstance(brightness, bool):
                raise ValueError("Brightness must be an integer")
            if not 0 <= brightness <= 255:
                raise ValueError("Brightness must be between 0 and 255")
            brightness_percent = round(brightness * 100 / 255)
        effect = kwargs.get("effect")
        if effect is not None and (
            Capability.LIGHT_COLOR_MODE not in self.device.profile.capabilities
        ):
            raise ValueError("Light modes are not supported by this fan")
        commands = build_light_commands(
            turn_on=True,
            brightness=brightness_percent,
            light_mode=effect,
        )
        self.manager.send_commands(self.device, commands)

    async def async_turn_off(self, **_kwargs) -> None:
        """Turn off the LED."""
        self.manager.send_command(self.device, led=False)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[FanManager],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up light entities only for models with a light capability."""
    manager = entry.runtime_data

    def create_entity(
        manager: FanManager, device: FanDevice
    ) -> AtombergLight | None:
        if Capability.LIGHT_POWER not in device.profile.capabilities:
            return None
        return AtombergLight(manager, device, "light", "Light")

    setup_device_entities(manager, async_add_entities, create_entity)
