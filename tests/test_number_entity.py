"""Tests for the discrete fan-light intensity control."""

from __future__ import annotations

import asyncio
import json
import unittest
from types import SimpleNamespace

from ha_test_stubs import ensure_homeassistant_modules

ensure_homeassistant_modules()

from homeassistant.components.number import NumberMode

from custom_components.atomberg_independent.const import (
    CONF_LIGHT_HIGH_BRIGHTNESS,
    CONF_LIGHT_LOW_BRIGHTNESS,
)
from custom_components.atomberg_independent.coordinator import FanDevice
from custom_components.atomberg_independent.models import resolve_model_profile
from custom_components.atomberg_independent.number import (
    AtombergLightIntensity,
    async_setup_entry,
)
from custom_components.atomberg_independent.protocol import encode_command


class FakeManager:
    def __init__(self) -> None:
        self.payloads: list[bytes] = []
        self.listeners = []

    def async_add_listener(self, callback) -> None:
        self.listeners.append(callback)

    def send_command(self, _device: object, **fields: bool | int | str) -> None:
        self.payloads.append(encode_command(**fields))


def make_device(series: str = "M1") -> FanDevice:
    return FanDevice(
        device_id="020000000001",
        device_key="a" * 64,
        host="192.168.1.10",
        series=series,
        profile=resolve_model_profile(series),
        last_seen=1,
        led=False,
        brightness=10,
    )


class LightIntensityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = FakeManager()
        self.device = make_device()
        self.entity = AtombergLightIntensity(
            self.manager,
            self.device,
            low_brightness=10,
            high_brightness=20,
        )

    def test_control_is_a_three_position_slider(self) -> None:
        self.assertEqual(self.entity._attr_native_min_value, 0)
        self.assertEqual(self.entity._attr_native_max_value, 2)
        self.assertEqual(self.entity._attr_native_step, 1)
        self.assertEqual(self.entity._attr_mode, NumberMode.SLIDER)

    def test_off_low_high_off_transitions_follow_reported_state(self) -> None:
        self.assertEqual(self.entity.native_value, 0)

        asyncio.run(self.entity.async_set_native_value(1))
        self.assertEqual(json.loads(self.manager.payloads[-1]), {"brightness": 10})
        self.assertEqual(self.entity.native_value, 0)
        self.device.led = True
        self.device.brightness = 10
        self.assertEqual(self.entity.native_value, 1)

        asyncio.run(self.entity.async_set_native_value(2))
        self.assertEqual(json.loads(self.manager.payloads[-1]), {"brightness": 20})
        self.assertEqual(self.entity.native_value, 1)
        self.device.brightness = 20
        self.assertEqual(self.entity.native_value, 2)

        asyncio.run(self.entity.async_set_native_value(0))
        self.assertEqual(json.loads(self.manager.payloads[-1]), {"led": False})
        self.assertEqual(self.entity.native_value, 2)
        self.device.led = False
        self.assertEqual(self.entity.native_value, 0)

    def test_unavailable_or_unrecognized_state_is_not_reported_as_a_stage(self) -> None:
        self.device.available = False
        self.assertFalse(self.entity.available)
        with self.assertRaises(RuntimeError):
            asyncio.run(self.entity.async_set_native_value(1))
        self.assertEqual(self.manager.payloads, [])

        self.device.available = True
        self.device.led = True
        self.device.brightness = 55
        self.assertIsNone(self.entity.native_value)
        self.assertFalse(self.entity.available)

    def test_invalid_slider_values_are_rejected(self) -> None:
        for value in (-1, 3, 1.5, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                asyncio.run(self.entity.async_set_native_value(value))
        self.assertEqual(self.manager.payloads, [])

    def test_entity_is_created_only_for_configured_supported_capability(self) -> None:
        added = []
        entry = SimpleNamespace(
            runtime_data=self.manager,
            options={
                CONF_LIGHT_LOW_BRIGHTNESS: 10,
                CONF_LIGHT_HIGH_BRIGHTNESS: 20,
            },
        )
        asyncio.run(async_setup_entry(None, entry, added.extend))
        listener = self.manager.listeners[-1]

        unsupported_device = make_device("M2")
        listener(unsupported_device)
        self.assertEqual(added, [])

        supported_device = make_device("M1")
        listener(supported_device)
        self.assertEqual(len(added), 1)
        self.assertIsInstance(added[0], AtombergLightIntensity)

    def test_entity_is_not_created_without_verified_mapping(self) -> None:
        manager = FakeManager()
        added = []
        entry = SimpleNamespace(runtime_data=manager, options={})

        asyncio.run(async_setup_entry(None, entry, added.extend))

        self.assertEqual(added, [])
        self.assertEqual(manager.listeners, [])


if __name__ == "__main__":
    unittest.main()
