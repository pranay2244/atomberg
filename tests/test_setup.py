"""Tests for Home Assistant config-entry setup behavior."""

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from ha_test_stubs import ensure_homeassistant_modules

ensure_homeassistant_modules()

from custom_components.atomberg_independent import async_setup_entry
from custom_components.atomberg_independent.const import NAME


class FakeManager:
    async def async_start(self) -> None:
        pass


class ConfigEntryTitleTests(unittest.TestCase):
    def test_existing_entry_title_is_updated_to_current_name(self) -> None:
        entry = SimpleNamespace(title="Atomberg Independent", runtime_data=None)

        class FakeConfigEntries:
            def async_update_entry(self, updated_entry, *, title: str) -> None:
                updated_entry.title = title

            async def async_forward_entry_setups(self, *_args) -> None:
                pass

        hass = SimpleNamespace(config_entries=FakeConfigEntries())
        manager = FakeManager()

        with patch(
            "custom_components.atomberg_independent.coordinator.FanManager",
            return_value=manager,
        ):
            result = asyncio.run(async_setup_entry(hass, entry))

        self.assertTrue(result)
        self.assertEqual(entry.title, NAME)
        self.assertIs(entry.runtime_data, manager)


if __name__ == "__main__":
    unittest.main()
