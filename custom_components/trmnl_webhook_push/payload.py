"""Payload builder for the TRMNL Entity Push integration."""
from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)


def create_entity_payload(state) -> dict:
    """Create the payload for a single entity with filtered attributes."""
    # Define a strict whitelist of the specific attributes you want to keep
    allowed_attributes = ("friendly_name", "unit_of_measurement", "icon")
    
    # Extract only the keys that exist in the entity's current attributes
    filtered_attributes = {
        key: state.attributes[key]
        for key in allowed_attributes
        if key in state.attributes
    }

    payload = {
        "state": state.state,
        "attributes": filtered_attributes,
    }
    
    _LOGGER.debug("TRMNL: Created payload for %s: %s", state.entity_id, payload)
    return payload
