"""Config flow for TRMNL Entity Push integration."""
from __future__ import annotations

import re
import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

# Import your new constants
from .const import DOMAIN, CONF_URL, CONF_INTERVAL, DEFAULT_INTERVAL

URL_REGEX = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)

# Updated schema to include the floating-point number field
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): selector.TextSelector(
            selector.TextSelectorConfig(
                type=selector.TextSelectorType.URL
            )
        ),
        vol.Required(CONF_INTERVAL, default=DEFAULT_INTERVAL): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=7.5,        # 7.5 minutes minimum restriction
                max=720.0,      # 12 hours maximum restriction (12 * 60)
                step=0.5,       # Allows floating point adjustment steps
                mode=selector.NumberSelectorMode.BOX,
                unit_of_measurement="min"
            )
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, str]) -> dict[str, str]:
    """Validate the user input allows us to connect."""
    url = data[CONF_URL].strip()

    if not URL_REGEX.match(url):
        raise InvalidUrl

    session = async_get_clientsession(hass)
    test_payload = {
        "merge_variables":
        {
            "status": "connecting",
            "message": "Hello from Home Assistant"
        }
    }

    try:
        async with session.post(url, json=test_payload, timeout=10) as response:
            if response.status not in (200, 201, 202):
                raise CannotConnect
    except (aiohttp.ClientError, TimeoutError):
        raise CannotConnect

    return {"title": "TRMNL Entity Push"}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TRMNL Entity Push."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except InvalidUrl:
                errors["base"] = "invalid_url"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                errors["base"] = "unknown"
            else:
                # The data dictionary automatically includes both keys now
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "docs_url": "https://github.com/Jef-NL/trmnl-webhook-push"
            },
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidUrl(HomeAssistantError):
    """Error to indicate the URL format is malformed."""
