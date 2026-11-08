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
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **_kwargs,
    ) -> None:
        """Turn on, optionally selecting a speed."""
        if percentage is None:
            self.manager.send_command(self.device, power=True)
            return
        self._send_percentage_command(percentage)

    async def async_turn_off(self, **_kwargs) -> None:
        """Turn off the fan."""
        self.manager.send_command(self.device, power=False)

    async def async_set_percentage(self, percentage: int) -> None:
        """Set a discrete speed level."""
        self._send_percentage_command(percentage)

    def _send_percentage_command(self, percentage: int) -> None:
        """Send a target percentage as a fan power or speed command."""
        if percentage == 0:
            self.manager.send_command(self.device, power=False)
            return
        speed = percentage_to_speed(percentage)
        self.manager.send_command(
            self.device, power=True, speed=speed, boost=False
        )

    async def async_increase_speed(
        self, percentage_step: int | None = None
    ) -> None:
        """Increase the reported fan speed by one or more physical levels."""
        if percentage_step is not None:
            step = self._validate_percentage_step(percentage_step)
            if step == 0:
                return
            if self.device.power is False:
                current_percentage = 0
            elif self.device.power is True:
                current_percentage = self.percentage
                if current_percentage is None:
                    return
            else:
                return
            self._send_percentage_step_target(
                min(100, current_percentage + step)
            )
            return

        if self.device.power is False:
            self.manager.send_command(
                self.device, power=True, speed=1, boost=False
            )
            return
        current_speed = self.device.speed
        if (
            self.device.power is not True
            or isinstance(current_speed, bool)
            or not isinstance(current_speed, int)
            or not 1 <= current_speed <= 6
        ):
            return

        speed = min(6, current_speed + 1)
        if speed != current_speed:
            self.manager.send_command(
                self.device, power=True, speed=speed, boost=False
            )

    async def async_decrease_speed(
        self, percentage_step: int | None = None
    ) -> None:
        """Decrease the reported fan speed by one or more physical levels."""
        if percentage_step is not None:
            step = self._validate_percentage_step(percentage_step)
            if step == 0 or self.device.power is not True:
                return
            current_percentage = self.percentage
            if current_percentage is None:
                return
            self._send_percentage_step_target(
                max(0, current_percentage - step)
            )
            return

        current_speed = self.device.speed
        if (
            self.device.power is not True
            or isinstance(current_speed, bool)
            or not isinstance(current_speed, int)
            or not 1 <= current_speed <= 6
        ):
            return

        speed = current_speed - 1
        if speed <= 0:
            self.manager.send_command(self.device, power=False)
        else:
            self.manager.send_command(
                self.device, power=True, speed=speed, boost=False
            )

    @staticmethod
    def _validate_percentage_step(percentage_step: int) -> int:
        """Validate a percentage-point change requested by Home Assistant."""
        if (
            isinstance(percentage_step, bool)
            or not isinstance(percentage_step, int)
            or percentage_step < 0
        ):
            raise ValueError("percentage_step must be a non-negative integer")
        return percentage_step

    def _send_percentage_step_target(self, percentage: int) -> None:
        """Avoid sending a command if rounding leaves the fan at its current speed."""
        target_speed = percentage_to_speed(percentage) if percentage > 0 else None
        current_speed = self.device.speed
        if (
            target_speed is not None
            and self.device.power is True
            and isinstance(current_speed, int)
            and not isinstance(current_speed, bool)
            and current_speed == target_speed
        ):
            return
        self._send_percentage_command(percentage)


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
