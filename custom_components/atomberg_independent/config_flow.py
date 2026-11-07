"""Config flow for Atomberg Independent."""

from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, NAME


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a single integration setup entry."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Create an entry for the research foundation."""
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=NAME, data={})

        return self.async_show_form(step_id="user", data_schema=None)
