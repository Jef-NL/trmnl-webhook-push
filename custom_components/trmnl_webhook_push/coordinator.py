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
import homeassistant.util.dt as dt_util
from homeassistant.components.recorder import history

from .label import get_labelled_entities
from .payload import create_entity_payload, create_history_payload

_LOGGER = logging.getLogger(__name__)


class TRMNLCoordinator:
    """Manages the polling timer and webhook pushes for TRMNL."""

    def __init__(self, hass: HomeAssistant, webhook_url: str, update_interval: float) -> None:
        """Initialise the coordinator."""
        self._hass = hass
        self._webhook_url = webhook_url
        self._remove_timer = None
        self._update_interval = update_interval

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def async_start(self) -> None:
        """Start the coordinator: run an initial push and set up the timer."""
        _LOGGER.debug(
            "TRMNL: Setting up periodic timer for %d seconds",
            self._update_interval,
        )
        self._remove_timer = async_track_time_interval(
            self._hass,
            self._async_push,
            timedelta(seconds=self._update_interval),
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
    async def _async_push(self, *_) -> None:
        """Collect TRMNL-labelled entities and POST them to the webhook."""
        _LOGGER.debug("TRMNL: Starting entity processing")
        trmnl_entities = get_labelled_entities(self._hass)

        if not trmnl_entities:
            _LOGGER.info("TRMNL: No entities found with TRMNL label")
            return
        _LOGGER.debug("TRMNL: Found %d entities with TRMNL label",
                      len(trmnl_entities))
        entity_ids = [e.entity_id for e in trmnl_entities]

        # Find the largest duration across all labelled entities
        max_duration = max(
            (e.trmnl_label.duration for e in trmnl_entities if e.trmnl_label.duration is not None),
            # fallback for DEFAULT label (no duration)
            default=None,
        )
        db_history = {}
        if max_duration:
            now = dt_util.now()
            start_time = now - max_duration
            _LOGGER.debug("TRMNL: Using history window of %s (from %s to %s)",
                          max_duration, start_time, now)

            # Query the Recorder database for all entity histories in a single batch
            try:
                db_history = await self._hass.async_add_executor_job(
                    history.get_significant_states,
                    self._hass,
                    start_time,
                    now,
                    entity_ids,
                )
            except Exception as err:
                _LOGGER.error(
                    "TRMNL: Failed to query recorder database for history: %s", err)
                return

        entities_payload = []
        for trmnl_entity in trmnl_entities:
            entity_id = trmnl_entity.entity_id
            label = trmnl_entity.trmnl_label

            state_list = db_history.get(entity_id, [])
            history_data = create_history_payload(state_list, label)

            state = self._hass.states.get(entity_id)
            if state:
                _LOGGER.debug(
                    "TRMNL: Processing entity '%s' with label %s",
                    entity_id, label.name,
                )
                entities_payload.append(
                    create_entity_payload(state, history_data))

        if not entities_payload:
            _LOGGER.debug("TRMNL: No entity states available to send")
            return

        payload = {"merge_variables": {"entities": entities_payload}}
        _LOGGER.debug("TRMNL: Preparing to send payload: %s", payload)

        try:
            async with aiohttp.ClientSession() as session:
                _LOGGER.debug("TRMNL: Sending POST request to %s",
                              self._webhook_url)
                async with session.post(self._webhook_url, json=payload) as response:
                    if response.status == 200:
                        _LOGGER.info(
                            "TRMNL: Successfully sent data to webhook")
                        _LOGGER.debug("TRMNL: Webhook response: %s", await response.text())
                    else:
                        _LOGGER.error(
                            "TRMNL: Error sending to webhook: %s", response.status)
                        _LOGGER.error("TRMNL: Response: %s", await response.text())
        except Exception as err:  # noqa: BLE001
            _LOGGER.error("TRMNL: Failed to send data to webhook: %s", err)
