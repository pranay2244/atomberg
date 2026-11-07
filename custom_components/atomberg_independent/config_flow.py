"""Config flow for Atomberg."""

from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.data_entry_flow import FlowResult
import voluptuous as vol

from .const import (
    CONF_LIGHT_HIGH_BRIGHTNESS,
    CONF_LIGHT_LOW_BRIGHTNESS,
    DOMAIN,
    NAME,
)
from .protocol import validate_light_stage_brightness


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a single integration setup entry."""

    VERSION = 1
    MINOR_VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> "AtombergOptionsFlow":
        """Return the options flow for configuring observed light levels."""
        return AtombergOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Create a single local discovery entry."""
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=NAME, data={})

        return self.async_show_form(step_id="user", data_schema=None)


class AtombergOptionsFlow(config_entries.OptionsFlow):
    """Configure reported protocol values for discrete light stages."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Save user-verified low and high protocol brightness values."""
        errors: dict[str, str] = {}
        if user_input is not None:
            low = user_input.get(CONF_LIGHT_LOW_BRIGHTNESS)
            high = user_input.get(CONF_LIGHT_HIGH_BRIGHTNESS)
            try:
                validate_light_stage_brightness(low, high)
            except ValueError:
                errors["base"] = "invalid_light_stage_values"
            else:
                return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_LIGHT_LOW_BRIGHTNESS,
                    description={
                        "suggested_value": self.config_entry.options.get(
                            CONF_LIGHT_LOW_BRIGHTNESS
                        )
                    },
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
                vol.Optional(
                    CONF_LIGHT_HIGH_BRIGHTNESS,
                    description={
                        "suggested_value": self.config_entry.options.get(
                            CONF_LIGHT_HIGH_BRIGHTNESS
                        )
                    },
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
            }
        )
        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
