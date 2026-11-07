"""Tests for UDP fan discovery and availability lifecycle."""

import json
import unittest

from ha_test_stubs import ensure_homeassistant_modules

ensure_homeassistant_modules()

from custom_components.atomberg_independent.const import (
    DEVICE_TIMEOUT_SECONDS,
    MAX_DEVICES,
)
from custom_components.atomberg_independent.coordinator import FanManager


class FakeTransport:
    def __init__(self) -> None:
        self.sent: list[tuple[bytes, tuple[str, int]]] = []

    def sendto(self, payload: bytes, address: tuple[str, int]) -> None:
        self.sent.append((payload, address))


def presence(mac_tail: int, series: str = "I5") -> bytes:
    return f"02:00:00:00:00:{mac_tail:02X}_{series}".encode()


def state_packet(status: int, mac_tail: int = 1, series: str = "I5") -> bytes:
    envelope = {
        "device_id": f"02:00:00:00:00:{mac_tail:02X}",
        "state_string": f"{status},a,b,c,d,e,f,{series}",
    }
    return json.dumps(envelope).encode().hex().encode()


class FanManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = FanManager(object())
        self.manager.transport = FakeTransport()
        self.updates = []
        self.manager.async_add_listener(self.updates.append)

    def test_presence_discovery_sends_read_and_updates_existing_device(self) -> None:
        self.manager.handle_datagram(presence(1), ("192.168.1.10", 5625))

        self.assertEqual(len(self.manager.devices), 1)
        device = next(iter(self.manager.devices.values()))
        self.assertEqual(device.series, "I5")
        self.assertEqual(len(self.manager.transport.sent), 1)
        self.assertEqual(json.loads(self.manager.transport.sent[0][0]), {"read": 1})

        self.manager.handle_datagram(presence(1), ("192.168.1.11", 5625))

        self.assertEqual(len(self.manager.devices), 1)
        self.assertEqual(device.host, "192.168.1.11")
        self.assertEqual(len(self.manager.transport.sent), 1)

    def test_full_state_updates_device_fields(self) -> None:
        status = 4 | 0x10 | (70 << 8) | (6 << 16)

        self.manager.handle_datagram(state_packet(status), ("192.168.1.10", 5625))

        device = next(iter(self.manager.devices.values()))
        self.assertTrue(device.power)
        self.assertEqual(device.speed, 4)
        self.assertEqual(device.brightness, 70)
        self.assertEqual(device.timer, 6)

    def test_invalid_source_is_ignored(self) -> None:
        self.manager.handle_datagram(presence(1), ("8.8.8.8", 5625))

        self.assertEqual(self.manager.devices, {})
        self.assertEqual(self.manager.transport.sent, [])

    def test_expired_device_is_removed_and_can_be_rediscovered(self) -> None:
        self.manager.handle_datagram(presence(1), ("192.168.1.10", 5625))
        old_device = next(iter(self.manager.devices.values()))
        old_device.last_seen -= DEVICE_TIMEOUT_SECONDS + 1

        self.manager._expire_stale_devices(None)

        self.assertFalse(old_device.available)
        self.assertEqual(self.manager.devices, {})
        self.assertIs(self.updates[-1], old_device)

        self.manager.handle_datagram(presence(1), ("192.168.1.12", 5625))

        new_device = next(iter(self.manager.devices.values()))
        self.assertIsNot(new_device, old_device)
        self.assertTrue(new_device.available)

    def test_device_limit_evicts_stale_device_and_rejects_when_all_are_active(self) -> None:
        for mac_tail in range(MAX_DEVICES):
            self.manager.handle_datagram(
                presence(mac_tail), ("192.168.1.10", 5625)
            )
        stale_device = self.manager.devices[
            next(iter(self.manager.devices))
        ]
        stale_device.last_seen -= DEVICE_TIMEOUT_SECONDS + 1

        self.manager.handle_datagram(
            presence(MAX_DEVICES), ("192.168.1.20", 5625)
        )

        self.assertEqual(len(self.manager.devices), MAX_DEVICES)
        self.assertNotIn(stale_device.device_key, self.manager.devices)
        self.assertFalse(stale_device.available)

        active_keys = set(self.manager.devices)
        self.manager.handle_datagram(
            presence(MAX_DEVICES + 1), ("192.168.1.21", 5625)
        )
        self.assertEqual(set(self.manager.devices), active_keys)


if __name__ == "__main__":
    unittest.main()
