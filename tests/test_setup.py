"""Tests for Home Assistant config-entry setup behavior."""

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from ha_test_stubs import ensure_homeassistant_modules

ensure_homeassistant_modules()

from custom_components.atomberg_independent import (
    async_setup_entry,
    async_unload_entry,
)
from custom_components.atomberg_independent.const import NAME


class FakeManager:
    async def async_start(self) -> None:
        pass

    async def async_stop(self) -> None:
        pass


class ConfigEntryTitleTests(unittest.TestCase):
    def test_existing_entry_title_is_updated_to_current_name(self) -> None:
        entry = SimpleNamespace(title="Atomberg Independent", runtime_data=None)

        class FakeConfigEntries:
            def async_update_entry(self, updated_entry, *, title: str) -> None:
                updated_entry.title = title

            async def async_forward_entry_setups(self, *_args) -> None:
                pass

        class FakeBus:
            def __init__(self) -> None:
                self.event_type = None
                self.callback = None

            def async_listen_once(self, event_type, callback):
                self.event_type = event_type
                self.callback = callback
                return lambda: None

        hass = SimpleNamespace(
            config_entries=FakeConfigEntries(),
            bus=FakeBus(),
        )
        entry.unload_callbacks = []
        entry.async_on_unload = entry.unload_callbacks.append
        manager = FakeManager()

        with patch(
            "custom_components.atomberg_independent.coordinator.FanManager",
            return_value=manager,
        ), self.assertLogs(
            "custom_components.atomberg_independent", level="INFO"
        ) as logs:
            result = asyncio.run(async_setup_entry(hass, entry))

        self.assertTrue(result)
        self.assertEqual(entry.title, NAME)
        self.assertIs(entry.runtime_data, manager)
        self.assertEqual(hass.bus.event_type, "homeassistant_stop")
        self.assertEqual(len(entry.unload_callbacks), 1)
        self.assertTrue(
            any(
                "Setting up Atomberg integration" in message
                for message in logs.output
            )
        )
        self.assertTrue(
            any("setup completed" in message for message in logs.output)
        )
        with self.assertLogs(
            "custom_components.atomberg_independent", level="INFO"
        ) as shutdown_logs:
            hass.bus.callback(None)
        self.assertIn("Home Assistant shutdown detected", shutdown_logs.output[0])

    def test_unload_logs_failure_without_stopping_listener(self) -> None:
        class FakeConfigEntries:
            async def async_unload_platforms(self, *_args) -> bool:
                return False

        hass = SimpleNamespace(config_entries=FakeConfigEntries())
        entry = SimpleNamespace(runtime_data=FakeManager())

        with self.assertLogs(
            "custom_components.atomberg_independent", level="WARNING"
        ) as logs:
            result = asyncio.run(async_unload_entry(hass, entry))

        self.assertFalse(result)
        self.assertIn("listener remains active", logs.output[-1])

    def test_unload_stops_manager_after_platforms_unload(self) -> None:
        manager = FakeManager()
        manager.stopped = False

        async def stop_manager() -> None:
            manager.stopped = True

        manager.async_stop = stop_manager

        class FakeConfigEntries:
            async def async_unload_platforms(self, *_args) -> bool:
                return True

        hass = SimpleNamespace(config_entries=FakeConfigEntries())
        entry = SimpleNamespace(runtime_data=manager)

        with self.assertLogs(
            "custom_components.atomberg_independent", level="INFO"
        ) as logs:
            result = asyncio.run(async_unload_entry(hass, entry))

        self.assertTrue(result)
        self.assertTrue(manager.stopped)
        self.assertIn("Unloading Atomberg integration", logs.output[0])
        self.assertIn("Atomberg integration unloaded", logs.output[-1])


if __name__ == "__main__":
    unittest.main()
