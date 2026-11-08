"""Tests for the native Atomberg fan entity."""

from __future__ import annotations

import asyncio
import json
import unittest

from ha_test_stubs import ensure_homeassistant_modules

ensure_homeassistant_modules()

from homeassistant.components.fan import FanEntityFeature

from custom_components.atomberg_independent.coordinator import FanDevice
from custom_components.atomberg_independent.fan import AtombergFan
from custom_components.atomberg_independent.models import (
    Capability,
    resolve_model_profile,
)
from custom_components.atomberg_independent.protocol import encode_command


class FakeManager:
    def __init__(self) -> None:
        self.payloads: list[bytes] = []

    def send_command(self, _device: object, **fields: bool | int | str) -> None:
        self.payloads.append(encode_command(**fields))


def make_fan(
    *, power: bool | None = True, speed: int | None = 1, series: str = "I5"
) -> tuple[AtombergFan, FakeManager]:
    manager = FakeManager()
    device = FanDevice(
        device_id="020000000001",
        device_key="a" * 64,
        host="192.168.1.10",
        series=series,
        profile=resolve_model_profile(series),
        last_seen=1,
        power=power,
        speed=speed,
    )
    return AtombergFan(manager, device, "fan", "Fan"), manager


def sent_commands(manager: FakeManager) -> list[dict[str, object]]:
    return [json.loads(payload) for payload in manager.payloads]


class FanFeatureTests(unittest.TestCase):
    def test_native_fan_advertises_only_supported_features_and_six_speeds(self) -> None:
        fan, _manager = make_fan()

        self.assertEqual(
            fan.supported_features,
            FanEntityFeature.SET_SPEED
            | FanEntityFeature.TURN_ON
            | FanEntityFeature.TURN_OFF,
        )
        self.assertEqual(fan._attr_speed_count, 6)

        unsupported, _manager = make_fan(series="unknown")
        self.assertEqual(unsupported.supported_features, FanEntityFeature(0))

    def test_profile_features_are_gated_independently(self) -> None:
        fan, _manager = make_fan()
        fan.device.profile = fan.device.profile.__class__(
            identifier="power-only",
            name="Power only",
            capabilities=frozenset({Capability.FAN_POWER}),
        )
        self.assertEqual(
            fan.supported_features,
            FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF,
        )


class FanCommandTests(unittest.TestCase):
    def test_turn_on_and_off_send_power_commands_without_changing_reported_state(self) -> None:
        fan, manager = make_fan(power=False, speed=4)

        asyncio.run(fan.async_turn_on())
        self.assertEqual(sent_commands(manager), [{"power": True}])
        self.assertFalse(fan.is_on)
        self.assertEqual(fan.percentage, 0)

        asyncio.run(fan.async_turn_off())
        self.assertEqual(sent_commands(manager)[-1], {"power": False})
        self.assertFalse(fan.is_on)

    def test_percentage_zero_turns_off_and_speeds_select_the_canonical_level(self) -> None:
        fan, manager = make_fan()

        asyncio.run(fan.async_set_percentage(0))
        for percentage in (16, 33, 50, 66, 83, 100):
            asyncio.run(fan.async_set_percentage(percentage))

        self.assertEqual(
            sent_commands(manager),
            [{"power": False}]
            + [
                {"boost": False, "power": True, "speed": speed}
                for speed in range(1, 7)
            ],
        )
        self.assertTrue(fan.is_on)
        self.assertEqual(fan.percentage, 16)

    def test_turn_on_with_percentage_sets_speed_but_zero_turns_off(self) -> None:
        fan, manager = make_fan(power=False, speed=None)

        asyncio.run(fan.async_turn_on(percentage=66))
        asyncio.run(fan.async_turn_on(percentage=0))

        self.assertEqual(
            sent_commands(manager),
            [
                {"boost": False, "power": True, "speed": 4},
                {"power": False},
            ],
        )


class FanStepTests(unittest.TestCase):
    def test_increase_and_decrease_walk_each_physical_level(self) -> None:
        fan, manager = make_fan(power=False, speed=None)
        asyncio.run(fan.async_increase_speed())
        self.assertEqual(sent_commands(manager), [{"boost": False, "power": True, "speed": 1}])
        self.assertFalse(fan.is_on)
        self.assertEqual(fan.percentage, 0)

        for speed in range(1, 7):
            fan.device.power = True
            fan.device.speed = speed
            asyncio.run(fan.async_increase_speed())
            self.assertEqual(fan.percentage, speed * 100 // 6)
        self.assertEqual(
            sent_commands(manager),
            [
                {"boost": False, "power": True, "speed": 1},
                *[
                    {"boost": False, "power": True, "speed": speed}
                    for speed in range(2, 7)
                ],
            ],
        )

        manager.payloads.clear()
        for speed in range(6, 0, -1):
            fan.device.power = True
            fan.device.speed = speed
            asyncio.run(fan.async_decrease_speed())
        self.assertEqual(
            sent_commands(manager),
            [
                {"boost": False, "power": True, "speed": speed}
                for speed in range(5, 0, -1)
            ]
            + [{"power": False}],
        )

    def test_boundaries_and_unknown_reported_state_do_not_send_commands(self) -> None:
        fan, manager = make_fan(power=True, speed=6)
        asyncio.run(fan.async_increase_speed())
        fan.device.power = False
        asyncio.run(fan.async_decrease_speed())
        asyncio.run(fan.async_decrease_speed())
        fan.device.power = True
        fan.device.speed = None
        asyncio.run(fan.async_increase_speed())
        asyncio.run(fan.async_decrease_speed())
        fan.device.power = None
        asyncio.run(fan.async_increase_speed())

        self.assertEqual(manager.payloads, [])

    def test_percentage_steps_translate_to_multiple_hardware_levels(self) -> None:
        fan, manager = make_fan(power=True, speed=2)
        asyncio.run(fan.async_increase_speed(percentage_step=50))
        self.assertEqual(
            sent_commands(manager),
            [{"boost": False, "power": True, "speed": 5}],
        )

        manager.payloads.clear()
        fan.device.speed = 2
        asyncio.run(fan.async_decrease_speed(percentage_step=50))
        self.assertEqual(sent_commands(manager), [{"power": False}])

        manager.payloads.clear()
        asyncio.run(fan.async_increase_speed(percentage_step=0))
        self.assertEqual(manager.payloads, [])


if __name__ == "__main__":
    unittest.main()
