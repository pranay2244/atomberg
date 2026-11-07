"""Shared Home Assistant entity behavior for discovered Atomberg fans."""

from __future__ import annotations

from collections.abc import Callable
from typing import Optional

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import FanDevice, FanManager
from .identity import device_display_name


class AtombergEntity(Entity):
    """Base entity bound to one discovered fan."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self, manager: FanManager, device: FanDevice, entity_key: str, name: str
    ) -> None:
        self.manager = manager
        self.device = device
        self._attr_unique_id = f"{device.device_key}_{entity_key}"
        self._attr_name = name

    @property
    def available(self) -> bool:
        """Return whether the fan has reported recently."""
        return self.device.available

    @property
    def device_info(self) -> DeviceInfo:
        """Expose series as a hint without asserting the retail model."""
        model = "Atomberg fan"
        if self.device.series:
            model += f" (reported series {self.device.series})"
        return DeviceInfo(
            identifiers={(DOMAIN, self.device.device_key)},
            manufacturer="Atomberg",
            name=device_display_name(
                self.device.device_key,
                self.device.series,
            ),
            model=model,
            sw_version=self.device.firmware,
        )


EntityFactory = Callable[[FanManager, FanDevice], Optional[AtombergEntity]]


def setup_device_entities(
    manager: FanManager,
    async_add_entities: AddEntitiesCallback,
    entity_factory: EntityFactory,
) -> None:
    """Add entities for discovered fans and handle registry removal."""
    entities: dict[str, AtombergEntity] = {}

    def remove_cached_entity(
        device_key: str, removed_entity: AtombergEntity
    ) -> None:
        """Forget an entity when Home Assistant removes it."""
        if entities.get(device_key) is removed_entity:
            entities.pop(device_key, None)

    def device_updated(device: FanDevice) -> None:
        """Create or update the entity for a discovered fan."""
        entity = entities.get(device.device_key)
        if entity is None:
            entity = entity_factory(manager, device)
            if entity is None:
                return
            entities[device.device_key] = entity
            entity.async_on_remove(
                lambda key=device.device_key, removed=entity: remove_cached_entity(
                    key, removed
                )
            )
            async_add_entities([entity])
            return
        entity.device = device
        entity.async_write_ha_state()

    manager.async_add_listener(device_updated)
