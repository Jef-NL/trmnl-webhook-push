"""Payload builder for the TRMNL Entity Push integration."""
from __future__ import annotations

import logging
from datetime import timedelta
import homeassistant.util.dt as dt_util

_LOGGER = logging.getLogger(__name__)


def create_entity_payload(state, history=None) -> dict:
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
    if history:
        payload[f"h_{history["duration"]}"] = history["data"]

    _LOGGER.debug("TRMNL: Created payload for %s: %s",
                  state.entity_id, payload)
    return payload


def create_history_payload(state_list, duration) -> dict | None:
    """Downsample history to a compact flat array of raw values."""
    if not state_list:
        return None

    now = dt_util.utcnow()

    # Generate the exact hour timestamps we want (e.g., -8h to -1h)
    target_hours = [
        (now - timedelta(hours=i)).replace(minute=0, second=0, microsecond=0)
        for i in range(duration, 0, -1)
    ]

    raw_values = []

    # Map the database states to our exact target hours
    for target_time in target_hours:
        active_state = None
        for state in state_list:
            if state.last_changed <= target_time:
                active_state = state
            else:
                break

        matched_state = active_state or state_list[0]
        raw_values.append(matched_state.state)

    # 4. Return a single start time and the sequential data points
    return {
        "duration": duration,
        "data": {
            "t_s": target_hours[0].strftime("%H:%M"),
            "s": raw_values
        }
    }
