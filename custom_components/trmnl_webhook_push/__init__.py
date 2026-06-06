"""The TRMNL Entity Push integration."""
from __future__ import annotations

import logging

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_URL, CONF_INTERVAL
from .coordinator import TRMNLCoordinator
from .label import ensure_trmnl_label

_LOGGER = logging.getLogger(__name__)

# Since this integration only supports config entries, use this schema
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the TRMNL Entity Push component."""
    _LOGGER.debug("TRMNL: Setting up TRMNL Entity Push component")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up TRMNL Entity Push from a config entry."""
    _LOGGER.debug("TRMNL: Setting up config entry")
    hass.data.setdefault(DOMAIN, {})

    url = entry.data[CONF_URL]
    interval = entry.data[CONF_INTERVAL]
    interval_sec = interval * 60.0
    _LOGGER.debug("TRMNL: Using webhook URL: %s pushing every %s min", url, interval)

    # Ensure the TRMNL label exists in the label registry
    ensure_trmnl_label(hass)

    # Create and start the coordinator
    coordinator = TRMNLCoordinator(hass, url, interval_sec)
    await coordinator.async_start()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    _LOGGER.info("TRMNL: Integration setup completed for URL: %s", url)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    try:
        if entry.entry_id in hass.data[DOMAIN]:
            coordinator: TRMNLCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
            coordinator.async_stop()
            _LOGGER.info("TRMNL: Successfully unloaded integration")
    except Exception as err:
        _LOGGER.error("TRMNL: Error unloading integration: %s", err)
        return False
    return True
