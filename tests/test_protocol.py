"""Tests for the documented local fan packet format and command encoding."""

import json
import unittest

from custom_components.atomberg_independent.protocol import (
    build_light_commands,
    encode_command,
    home_assistant_brightness_to_percent,
    is_valid_source_address,
    parse_datagram,
    parse_full_state,
    parse_presence,
    percentage_to_speed,
    speed_to_percentage,
    timer_hours_to_command_index,
    validate_light_stage_brightness,
)


def full_state_packet(status: int, series: str = "I5") -> bytes:
    """Build a documented-format fixture; this is not a hardware capture."""
    envelope = {
        "device_id": "aa:bb:cc:dd:ee:ff",
        "state_string": f"{status},a,b,c,d,e,f,{series}",
    }
    return json.dumps(envelope).encode().hex().encode()


class DatagramParsingTests(unittest.TestCase):
    def test_parses_ascii_presence_beacon(self) -> None:
        state = parse_presence(b"AA:BB:CC:DD:EE:FF_i5")

        self.assertIsNotNone(state)
        assert state is not None
        self.assertEqual(state.device_id, "aabbccddeeff")
        self.assertEqual(state.series, "I5")
        self.assertFalse(state.has_state)
        self.assertIsNone(state.power)

    def test_parses_hex_encoded_state_and_status_bits(self) -> None:
        status = (
            4
            | 0x08
            | 0x10
            | 0x20
            | 0x80
            | (70 << 8)
            | 0x8000
            | (6 << 16)
        )
        state = parse_full_state(full_state_packet(status, "i5"))

        self.assertIsNotNone(state)
        assert state is not None
        self.assertEqual(state.device_id, "aabbccddeeff")
        self.assertEqual(state.series, "I5")
        self.assertTrue(state.has_state)
        self.assertTrue(state.power)
        self.assertEqual(state.speed, 4)
        self.assertTrue(state.led)
        self.assertTrue(state.sleep)
        self.assertEqual(state.brightness, 70)
        self.assertEqual(state.timer_hours, 6)
        self.assertEqual(state.light_mode, "daylight")

    def test_light_mode_bit_combinations_preserve_unknown_default(self) -> None:
        self.assertEqual(parse_full_state(full_state_packet(0)).light_mode, None)
        self.assertEqual(parse_full_state(full_state_packet(0x08)).light_mode, "cool")
        self.assertEqual(parse_full_state(full_state_packet(0x8000)).light_mode, "warm")

    def test_timer_hours_map_to_command_indices(self) -> None:
        self.assertEqual(
            [timer_hours_to_command_index(value) for value in (0, 1, 2, 3, 6)],
            [0, 1, 2, 3, 4],
        )
        with self.assertRaises(ValueError):
            timer_hours_to_command_index(4)
        with self.assertRaises(ValueError):
            timer_hours_to_command_index(True)
        with self.assertRaises(ValueError):
            timer_hours_to_command_index(6.0)

    def test_rejects_malformed_packets_and_invalid_device_ids(self) -> None:
        self.assertIsNone(parse_datagram(b"not-a-presence-or-hex-packet"))
        self.assertIsNone(parse_presence(b"fan-123_I5"))
        self.assertIsNone(parse_presence(b"01:00:00:00:00:00_I5"))
        self.assertIsNone(parse_presence(b"aa:bb-cc:dd:ee:ff_I5"))
        self.assertIsNone(parse_full_state(b"not-hex"))
        self.assertIsNone(parse_datagram(b" " * 4097))

    def test_source_addresses_must_be_private_unicast(self) -> None:
        self.assertTrue(is_valid_source_address("192.168.1.20"))
        self.assertTrue(is_valid_source_address("10.0.0.20"))
        for address in ("8.8.8.8", "224.0.0.1", "127.0.0.1", "not-an-ip"):
            with self.subTest(address=address):
                self.assertFalse(is_valid_source_address(address))

    def test_rejects_invalid_state_words(self) -> None:
        self.assertIsNone(parse_full_state(full_state_packet(0x1000000)))
        self.assertIsNone(parse_full_state(full_state_packet(-1)))
        self.assertIsNone(parse_full_state(full_state_packet(123, "invalid series")))


class CommandEncodingTests(unittest.TestCase):
    def test_encodes_documented_command_fields_and_read_request(self) -> None:
        command = encode_command(power=True, speed=4, boost=False)

        self.assertEqual(
            json.loads(command),
            {"boost": False, "power": True, "speed": 4},
        )
        self.assertEqual(json.loads(encode_command(read=1)), {"read": 1})

    def test_timer_command_uses_index_not_reported_hours(self) -> None:
        self.assertEqual(
            json.loads(encode_command(timer=timer_hours_to_command_index(6))),
            {"timer": 4},
        )
        with self.assertRaises(ValueError):
            encode_command(timer=6)

    def test_light_attribute_commands_are_separate_from_led_power(self) -> None:
        commands = build_light_commands(
            brightness=72, light_mode="warm"
        )
        self.assertEqual(
            [json.loads(command) for command in commands],
            [{"brightness": 72}, {"light_mode": "warm"}],
        )
        self.assertEqual(
            [json.loads(command) for command in build_light_commands()],
            [{"led": True}],
        )

    def test_rejects_invalid_command_fields(self) -> None:
        for invalid in (
            {"speed": 7},
            {"timer": 5},
            {"color": "warm"},
            {"light_mode": []},
            {"read": True},
            {"read": 1, "power": True},
            {"led": True, "brightness": 25},
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                encode_command(**invalid)

    def test_maps_six_discrete_speed_levels(self) -> None:
        speeds = range(1, 7)
        percentages = (16, 33, 50, 66, 83, 100)
        self.assertEqual(
            [speed_to_percentage(speed) for speed in speeds],
            list(percentages),
        )
        self.assertEqual(
            [percentage_to_speed(percentage) for percentage in percentages],
            list(speeds),
        )
        self.assertEqual(
            [
                percentage_to_speed(value)
                for value in (1, 16, 24, 25, 41, 42, 58, 59, 74, 75, 91, 92, 100)
            ],
            [1, 1, 1, 2, 2, 3, 4, 4, 4, 5, 5, 6, 6],
        )
        for invalid in (0, 101, True, 50.0):
            with self.subTest(percentage=invalid), self.assertRaises(ValueError):
                percentage_to_speed(invalid)
        for invalid in (0, 7, True, 3.0, "3"):
            with self.subTest(speed=invalid):
                self.assertIsNone(speed_to_percentage(invalid))

    def test_home_assistant_brightness_keeps_positive_requests_nonzero(self) -> None:
        self.assertEqual(
            [
                home_assistant_brightness_to_percent(value)
                for value in (0, 1, 2, 127, 128, 255)
            ],
            [0, 1, 1, 50, 50, 100],
        )
        with self.assertRaises(ValueError):
            home_assistant_brightness_to_percent(256)

    def test_light_stage_mapping_requires_distinct_configured_wire_values(self) -> None:
        self.assertIsNone(validate_light_stage_brightness(None, None))
        self.assertEqual(validate_light_stage_brightness(10, 20), (10, 20))
        for values in ((10, None), (None, 20), (10, 10), (0, 20), (10, 101), (True, 20)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                validate_light_stage_brightness(*values)


if __name__ == "__main__":
    unittest.main()
