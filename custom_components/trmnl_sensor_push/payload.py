"""Payload builder for the TRMNL Entity Push integration."""
from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)


def create_entity_payload(state) -> dict:
    """Create the payload for a single entity."""
    payload = {
        "state": state.state,
        "attributes": state.attributes,
    }
    _LOGGER.debug("TRMNL: Created payload for %s: %s", state.entity_id, payload)
    return payload
