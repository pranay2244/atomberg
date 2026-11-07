"""Tests for UDP fan discovery and availability lifecycle."""

import asyncio
import json
import unittest
from unittest.mock import Mock, patch

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
        self.closed = False

    def sendto(self, payload: bytes, address: tuple[str, int]) -> None:
        self.sent.append((payload, address))

    def close(self) -> None:
        self.closed = True


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

    def test_temporary_protocol_diagnostics_are_sanitized_and_rate_limited(self) -> None:
        with self.assertLogs(
            "custom_components.atomberg_independent.coordinator", level="DEBUG"
        ) as captured:
            self.manager.handle_datagram(
                presence(1, "m1"), ("192.168.1.10", 5625)
            )
            self.manager.handle_datagram(
                presence(1, "m1"), ("192.168.1.10", 5625)
            )
            self.manager.handle_datagram(
                state_packet(0x10, series="M1"), ("192.168.1.10", 5625)
            )
            self.manager.handle_datagram(
                state_packet(0x10, series="M1"), ("192.168.1.10", 5625)
            )

        diagnostic_messages = [
            message
            for message in captured.output
            if "Temporary Atomberg protocol diagnostic" in message
        ]
        self.assertEqual(len(diagnostic_messages), 2)
        self.assertIn("packet_type=presence", diagnostic_messages[0])
        self.assertIn("raw_series='m1'", diagnostic_messages[0])
        self.assertIn("packet_type=full_state", diagnostic_messages[1])
        self.assertIn("status_word=16", diagnostic_messages[1])
        for message in diagnostic_messages:
            self.assertNotIn("02:00:00:00:00:01", message)
            self.assertNotIn("192.168.1.10", message)
            self.assertNotIn("state_string", message)

    def test_invalid_source_is_ignored(self) -> None:
        self.manager.handle_datagram(presence(1), ("8.8.8.8", 5625))

        self.assertEqual(self.manager.devices, {})
        self.assertEqual(self.manager.transport.sent, [])

    def test_unrecognized_datagram_logs_only_its_size(self) -> None:
        payload = b"unrecognized packet contents"

        with self.assertLogs(
            "custom_components.atomberg_independent.coordinator", level="DEBUG"
        ) as captured:
            self.manager.handle_datagram(payload, ("192.168.1.10", 5625))

        self.assertIn(f"size={len(payload)} bytes", captured.output[0])
        self.assertNotIn(payload.decode(), captured.output[0])

    def test_discovery_log_uses_hashed_identity_and_packet_metadata(self) -> None:
        with self.assertLogs(
            "custom_components.atomberg_independent.coordinator", level="INFO"
        ) as captured:
            self.manager.handle_datagram(
                presence(1), ("192.168.1.10", 5625)
            )

        self.assertIn("device_hash=", captured.output[0])
        self.assertIn("packet_type=presence", captured.output[0])
        self.assertIn("reported_series=I5", captured.output[0])
        self.assertNotIn("02:00:00:00:00:01", captured.output[0])
        self.assertNotIn("192.168.1.10", captured.output[0])

    def test_listener_start_and_stop_are_logged(self) -> None:
        manager = FanManager(object())
        transport = FakeTransport()
        unsubscribe = Mock()

        async def create_datagram_endpoint(_loop, protocol_factory, **_kwargs):
            protocol = protocol_factory()
            protocol.connection_made(transport)
            return transport, protocol

        async def start_and_stop() -> None:
            await manager.async_start()
            await manager.async_stop()

        with patch(
            "asyncio.BaseEventLoop.create_datagram_endpoint",
            new=create_datagram_endpoint,
        ):
            with patch(
                "custom_components.atomberg_independent.coordinator."
                "async_track_time_interval",
                return_value=unsubscribe,
            ):
                with self.assertLogs(
                    "custom_components.atomberg_independent.coordinator",
                    level="DEBUG",
                ) as captured:
                    asyncio.run(start_and_stop())

        self.assertIsNone(manager.transport)
        self.assertTrue(transport.closed)
        unsubscribe.assert_called_once_with()
        self.assertTrue(
            any("UDP listener is ready (port=5625)" in line for line in captured.output)
        )
        self.assertTrue(
            any("availability monitoring started" in line for line in captured.output)
        )
        self.assertTrue(
            any("UDP listener close requested" in line for line in captured.output)
        )

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
