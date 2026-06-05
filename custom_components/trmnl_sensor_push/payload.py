"""Payload builder for the TRMNL Entity Push integration."""
from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)


def create_entity_payload(state) -> dict:
    """Create the payload for a single entity."""
    payload = {
        "name": state.attributes.get("friendly_name", state.entity_id),
        "value": state.state,
        "device_class": state.attributes.get("device_class", None),
        "unit_of_measurement": state.attributes.get("unit_of_measurement", None),
        "icon": state.attributes.get("icon", None),
        "friendly_name": state.attributes.get("friendly_name", state.entity_id),
        "attributes": state.attributes,
    }
    _LOGGER.debug("TRMNL: Created payload for %s: %s", state.entity_id, payload)
    return payload
