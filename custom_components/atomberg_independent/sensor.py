"""Diagnostic sensors for discovered Atomberg fans."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import FanDevice, FanManager
from .entity import AtombergEntity


class AtombergConnectionSensor(AtombergEntity, SensorEntity):
    """Report the current local connection state."""

    _attr_translation_key = "connection"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["Wi-Fi", "Offline"]

    @property
    def native_value(self) -> str:
        """Return Wi-Fi when the device is heard, otherwise offline."""
        return "Wi-Fi" if self.device.available else "Offline"


class AtombergSeriesSensor(AtombergEntity, SensorEntity):
    """Report the fan's advertised series without guessing a retail model."""

    _attr_translation_key = "reported_series"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> str:
        """Return the series code or unknown."""
        return self.device.series or "Unknown"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[FanManager],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up diagnostic sensors for each discovered fan."""
    manager = entry.runtime_data
    entities: dict[str, list[AtombergEntity]] = {}

    def device_updated(device: FanDevice) -> None:
        current = entities.get(device.device_key)
        if current is None:
            current = [
                AtombergConnectionSensor(
                    manager, device, "connection", "Connection"
                ),
                AtombergSeriesSensor(manager, device, "series", "Reported series"),
            ]
            entities[device.device_key] = current
            async_add_entities(current)
            return
        for entity in current:
            entity.device = device
            entity.async_write_ha_state()

    manager.async_add_listener(device_updated)
