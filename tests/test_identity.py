"""Tests for privacy-preserving device identity."""

import unittest

from custom_components.atomberg_independent.identity import (
    device_display_name,
    stable_device_key,
)


class StableDeviceKeyTests(unittest.TestCase):
    def test_same_identifier_produces_same_key(self) -> None:
        self.assertEqual(stable_device_key("device-123"), stable_device_key("device-123"))

    def test_key_does_not_contain_original_identifier(self) -> None:
        identifier = "private-device-identifier"
        self.assertNotIn(identifier, stable_device_key(identifier))

    def test_whitespace_is_ignored(self) -> None:
        self.assertEqual(stable_device_key(" device-123 "), stable_device_key("device-123"))

    def test_mac_address_formatting_is_normalized(self) -> None:
        self.assertEqual(
            stable_device_key("AA:BB:CC:DD:EE:FF"),
            stable_device_key("aabbccddeeff"),
        )

    def test_empty_identifier_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            stable_device_key("  ")

    def test_device_names_are_stable_distinct_and_do_not_expose_mac(self) -> None:
        first_key = stable_device_key("AA:BB:CC:DD:EE:01")
        second_key = stable_device_key("AA:BB:CC:DD:EE:02")
        first_name = device_display_name(first_key, "I5")
        second_name = device_display_name(second_key, "I5")

        self.assertEqual(first_name, device_display_name(first_key, "I5"))
        self.assertNotEqual(first_name, second_name)
        self.assertTrue(first_name.startswith("Atomberg fan I5 - "))
        self.assertEqual(len(first_name.rsplit(" - ", 1)[1]), 8)
        self.assertNotIn("AA:BB:CC:DD:EE:01", first_name)


if __name__ == "__main__":
    unittest.main()
