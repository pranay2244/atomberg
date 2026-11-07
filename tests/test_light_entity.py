"""Tests for Home Assistant light features and commands."""

from __future__ import annotations

import asyncio
import json
import unittest
from types import SimpleNamespace

from ha_test_stubs import ensure_homeassistant_modules

ensure_homeassistant_modules()

from homeassistant.components.light import LightEntityFeature

from custom_components.atomberg_independent.light import AtombergLight
from custom_components.atomberg_independent.entity import (
    setup_device_entities,
)
from custom_components.atomberg_independent.coordinator import FanDevice
from custom_components.atomberg_independent.models import resolve_model_profile
from custom_components.atomberg_independent.protocol import encode_command


class FakeManager:
    def __init__(self) -> None:
        self.payloads: list[bytes] = []
        self.listeners = []

    def async_add_listener(self, callback) -> None:
        self.listeners.append(callback)

    def send_command(self, _device: object, **fields: bool | int | str) -> None:
        self.payloads.append(encode_command(**fields))

    def send_commands(self, _device: object, payloads: tuple[bytes, ...]) -> None:
        self.payloads.extend(payloads)


def make_light(series: str) -> tuple[AtombergLight, FakeManager]:
    manager = FakeManager()
    device = SimpleNamespace(
        device_key="a" * 64,
        profile=resolve_model_profile(series),
        available=True,
        led=True,
        brightness=50,
        light_mode=None,
        series=series,
        firmware=None,
    )
    return AtombergLight(manager, device, "light", "Light"), manager


class LightEntityTests(unittest.TestCase):
    def test_effect_feature_is_advertised_only_for_supported_series(self) -> None:
        aris_light, _ = make_light("I5")
        basic_light, _ = make_light("M2")
        basic_light.device.light_mode = "cool"

        self.assertEqual(aris_light.supported_features, LightEntityFeature.EFFECT)
        self.assertEqual(aris_light.effect_list, ["warm", "cool", "daylight"])
        self.assertIsNone(aris_light.effect)
        self.assertEqual(aris_light.brightness, round(50 * 255 / 100))
        self.assertEqual(basic_light.supported_features, LightEntityFeature(0))
        self.assertIsNone(basic_light.effect_list)
        self.assertIsNone(basic_light.effect)
        self.assertIsNone(basic_light.brightness)

    def test_brightness_boundary_commands(self) -> None:
        expected = {
            0: {"led": False},
            1: {"brightness": 1},
            2: {"brightness": 1},
            127: {"brightness": 50},
            128: {"brightness": 50},
            255: {"brightness": 100},
        }

        for requested, command in expected.items():
            with self.subTest(brightness=requested):
                light, manager = make_light("I5")
                asyncio.run(light.async_turn_on(brightness=requested))
                self.assertEqual([json.loads(payload) for payload in manager.payloads], [command])

    def test_effect_and_brightness_commands_are_separate(self) -> None:
        light, manager = make_light("I5")

        asyncio.run(light.async_turn_on(brightness=128, effect="cool"))

        self.assertEqual(
            [json.loads(payload) for payload in manager.payloads],
            [{"brightness": 50}, {"light_mode": "cool"}],
        )

    def test_existing_entity_rebinds_after_stale_device_eviction(self) -> None:
        manager = FakeManager()
        added = []
        profile = resolve_model_profile("I5")
        old_device = FanDevice(
            device_id="020000000001",
            device_key="a" * 64,
            host="192.168.1.10",
            series="I5",
            profile=profile,
            last_seen=0,
            led=True,
        )
        new_device = FanDevice(
            device_id="020000000001",
            device_key="a" * 64,
            host="192.168.1.11",
            series="I5",
            profile=profile,
            last_seen=1,
            led=True,
        )

        setup_device_entities(
            manager,
            added.extend,
            lambda current_manager, device: AtombergLight(
                current_manager, device, "light", "Light"
            ),
        )
        manager.listeners[0](old_device)
        entity = added[0]
        self.assertTrue(entity.available)

        old_device.available = False
        manager.listeners[0](old_device)

        self.assertFalse(entity.available)

        manager.listeners[0](new_device)

        self.assertIs(entity.device, new_device)
        self.assertTrue(entity.available)


if __name__ == "__main__":
    unittest.main()
