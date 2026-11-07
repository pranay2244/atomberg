"""Tests for safe fan packet parsing and command encoding."""

import json
import unittest

from custom_components.atomberg_independent.protocol import (
    encode_command,
    parse_datagram,
    percentage_to_speed,
    speed_to_percentage,
)


class DatagramParsingTests(unittest.TestCase):
    def test_parses_nested_device_state_and_series_from_name(self) -> None:
        payload = json.dumps(
            {
                "device": {"device_id": "fan-123", "name": "atomberg_I3_abc"},
                "state": {"power": True, "speed": 3, "sleep": False, "timer": 2},
            }
        ).encode()

        state = parse_datagram(payload)

        self.assertIsNotNone(state)
        assert state is not None
        self.assertEqual(state.device_id, "fan-123")
        self.assertEqual(state.series, "I3")
        self.assertEqual(state.speed, 3)
        self.assertEqual(state.timer, 2)

    def test_rejects_non_json_and_json_without_stable_identity(self) -> None:
        self.assertIsNone(parse_datagram(b"not-json"))
        self.assertIsNone(parse_datagram(b'{"power":true}'))

    def test_rejects_oversized_datagrams(self) -> None:
        self.assertIsNone(parse_datagram(b" " * 4097))

    def test_invalid_state_values_are_not_applied(self) -> None:
        state = parse_datagram(
            b'{"device_id":"fan-123","speed":99,"power":"maybe","brightness":300}'
        )

        self.assertIsNotNone(state)
        assert state is not None
        self.assertIsNone(state.speed)
        self.assertIsNone(state.power)
        self.assertIsNone(state.brightness)

    def test_timer_is_limited_to_supported_choices(self) -> None:
        state = parse_datagram(b'{"device_id":"fan-123","timer":4}')

        self.assertIsNotNone(state)
        assert state is not None
        self.assertIsNone(state.timer)

    def test_control_characters_in_device_metadata_are_rejected(self) -> None:
        state = parse_datagram(b'{"device_id":"fan-123","series":"I1\\n"}')

        self.assertIsNotNone(state)
        assert state is not None
        self.assertIsNone(state.series)


class CommandEncodingTests(unittest.TestCase):
    def test_encodes_documented_command_fields(self) -> None:
        command = encode_command(power=True, speed=4, boost=False)

        self.assertEqual(
            json.loads(command),
            {"boost": False, "power": True, "speed": 4},
        )

    def test_rejects_invalid_speed_timer_and_unknown_field(self) -> None:
        with self.assertRaises(ValueError):
            encode_command(speed=7)
        with self.assertRaises(ValueError):
            encode_command(timer=4)
        with self.assertRaises(ValueError):
            encode_command(color="warm")

    def test_maps_six_discrete_speed_levels(self) -> None:
        self.assertEqual([percentage_to_speed(p) for p in (1, 17, 34, 50, 67, 84, 100)],
                         [1, 1, 2, 3, 4, 5, 6])
        self.assertEqual([speed_to_percentage(speed) for speed in range(1, 7)],
                         [17, 33, 50, 67, 83, 100])

    def test_rejects_zero_percent_as_a_speed_command(self) -> None:
        with self.assertRaises(ValueError):
            percentage_to_speed(0)


if __name__ == "__main__":
    unittest.main()
