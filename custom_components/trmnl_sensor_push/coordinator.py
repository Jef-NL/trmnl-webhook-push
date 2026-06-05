"""Coordinator for the TRMNL Entity Push integration.

Handles periodic polling, entity discovery via the TRMNL label,
payload construction, and webhook delivery.
"""
from __future__ import annotations

import logging
from datetime import timedelta

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.template import Template

from .const import MIN_TIME_BETWEEN_UPDATES
from .payload import create_entity_payload

_LOGGER = logging.getLogger(__name__)


class TRMNLCoordinator:
    """Manages the polling timer and webhook pushes for TRMNL."""

    def __init__(self, hass: HomeAssistant, webhook_url: str) -> None:
        """Initialise the coordinator."""
        self._hass = hass
        self._webhook_url = webhook_url
        self._remove_timer = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def async_start(self) -> None:
        """Start the coordinator: run an initial push and set up the timer."""
        _LOGGER.debug(
            "TRMNL: Setting up periodic timer for %d seconds",
            MIN_TIME_BETWEEN_UPDATES,
        )
        self._remove_timer = async_track_time_interval(
            self._hass,
            self._async_push,
            timedelta(seconds=MIN_TIME_BETWEEN_UPDATES),
        )

        _LOGGER.debug("TRMNL: Running initial entity push")
        await self._async_push()

    def async_stop(self) -> None:
        """Cancel the polling timer."""
        if self._remove_timer is not None:
            self._remove_timer()
            self._remove_timer = None
            _LOGGER.debug("TRMNL: Polling timer cancelled")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_trmnl_entities(self) -> list[str]:
        """Return entity IDs that carry the TRMNL label."""
        _LOGGER.debug("TRMNL: Fetching entities with TRMNL label")
        template = Template("{{ label_entities('TRMNL') }}", self._hass)
        result = template.async_render()
        _LOGGER.debug("TRMNL: Template rendered result: %s", result)
        return result

    async def _async_push(self, *_) -> None:
        """Collect TRMNL-labelled entities and POST them to the webhook."""
        _LOGGER.debug("TRMNL: Starting entity processing")

        entity_ids = self._get_trmnl_entities()

        if not entity_ids:
            _LOGGER.info("TRMNL: No entities found with TRMNL label")
            return

        _LOGGER.debug("TRMNL: Found %d entities with TRMNL label", len(entity_ids))

        entities_payload = []
        for entity_id in entity_ids:
            state = self._hass.states.get(entity_id)
            if state:
                _LOGGER.debug("TRMNL: Processing entity: %s", entity_id)
                entities_payload.append(create_entity_payload(state))

        if not entities_payload:
            _LOGGER.debug("TRMNL: No entity states available to send")
            return

        payload = {"merge_variables": {"entities": entities_payload}}
        _LOGGER.debug("TRMNL: Preparing to send payload: %s", payload)

        try:
            async with aiohttp.ClientSession() as session:
                _LOGGER.debug("TRMNL: Sending POST request to %s", self._webhook_url)
                async with session.post(self._webhook_url, json=payload) as response:
                    if response.status == 200:
                        _LOGGER.info("TRMNL: Successfully sent data to webhook")
                        _LOGGER.debug(
                            "TRMNL: Webhook response: %s", await response.text()
                        )
                    else:
                        _LOGGER.error(
                            "TRMNL: Error sending to webhook: %s", response.status
                        )
                        _LOGGER.error(
                            "TRMNL: Response: %s", await response.text()
                        )
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("TRMNL: Failed to send data to webhook: %s", err)
