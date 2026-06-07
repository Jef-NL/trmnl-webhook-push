"""Payload builder for the TRMNL Entity Push integration."""
from __future__ import annotations

import logging
from datetime import timedelta
import homeassistant.util.dt as dt_util
from .label import TRMNLLabel

_LOGGER = logging.getLogger(__name__)


def create_entity_payload(state, history=None) -> dict:
    """Create the payload for a single entity with filtered attributes."""
    allowed_attributes = ("friendly_name", "unit_of_measurement", "icon")

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
        # e.g. h_8h, h_1h
        payload[f"h_{history['duration']}h"] = history["data"]

    _LOGGER.debug("TRMNL: Created payload for %s: %s",
                  state.entity_id, payload)
    return payload


def create_history_payload(state_list, trmnl_label: TRMNLLabel) -> dict | None:
    """Downsample history to a compact flat array of raw values."""
    if not state_list or trmnl_label.duration is None:
        return None

    now = dt_util.now()

    duration = trmnl_label.duration or timedelta(hours=8)
    interval = trmnl_label.interval or timedelta(hours=1)

    total_seconds = int(duration.total_seconds())
    interval_seconds = int(interval.total_seconds())

    # Generate target timestamps stepping by interval across the duration window
    target_times = [
        (now - timedelta(seconds=offset)).replace(second=0, microsecond=0)
        for offset in range(total_seconds, 0, -interval_seconds)
    ]

    raw_values = []
    for target_time in target_times:
        active_state = None
        for state in state_list:
            if state.last_changed <= target_time:
                active_state = state
            else:
                break

        matched_state = active_state or state_list[0]
        raw_values.append(matched_state.state)

    total_hours = int(duration.total_seconds() // 3600)

    return {
        "duration": total_hours,
        "data": {
            "t_s": target_times[0].strftime("%H:%M"),
            "s": raw_values,
        }
    }


# IDEA Compess all data to a matrix
def create_high_density_matrix(entities_data_list) -> dict:
    """Compresses large, highly granular datasets into single text blocks."""

    def to_base36(num: int) -> str:
        """Converts an integer to a compact base36 alpha-numeric string."""
        if num == 0:
            return "0"
        sign = "-" if num < 0 else ""
        num = abs(num)
        chars = "0123456789abcdefghijklmnopqrstuvwxyz"
        result = ""
        while num > 0:
            num, rem = divmod(num, 36)
            result = chars[rem] + result
        return sign + result

    rows = []
    for item in entities_data_list:
        state = item.get("state_obj")
        # e.g. [21.4, 21.4, 21.5, 21.2]
        history_values = item.get("raw_history_floats", [])

        name = state.attributes.get("friendly_name", "")
        unit = state.attributes.get("unit_of_measurement", "")

        # 1. Delta & Decimal Compaction Engine
        compressed_history = ""
        if history_values:
            # Shift decimals out of the first number and convert to Base36
            first_val = int(float(history_values[0]) * 10)
            compressed_history = to_base36(first_val)

            # Encode subsequent points as relative deltas
            for i in range(1, len(history_values)):
                current_shifted = int(float(history_values[i]) * 10)
                previous_shifted = int(float(history_values[i-1]) * 10)
                delta = current_shifted - previous_shifted

                # Use a period (.) to separate distinct delta blocks cleanly
                compressed_history += f".{to_base36(delta)}"

        # 2. Build the flat pipe row
        row_str = f"{state.state}|{name}|{unit}|{compressed_history}"
        rows.append(row_str)

    return {"merge_variables": {"matrix": "::".join(rows)}}

# And TRMNL SIDE
# function run(input) {
#   if (!input.matrix) return { entities: [] };

#   const entityRows = input.matrix.split("::");

#   const expandedEntities = entityRows.map(row => {
#     const [state, name, unit, compressedHistory] = row.split("|");
#     const historyArray = [];

#     if (compressedHistory) {
#       // Split the Base36 delta segments back out
#       const segments = compressedHistory.split(".");

#       // Parse the first absolute starting value from Base36
#       let runningValue = parseInt(segments[0], 36);
#       historyArray.push(runningValue / 10); // Restore decimal placement

#       // Rehydrate all subsequent delta points sequentially
#       for (let i = 1; i < segments.length; i++) {
#         const delta = parseInt(segments[i], 36);
#         runningValue += delta;
#         historyArray.push(runningValue / 10);
#       }
#     }

#     return {
#       state: state,
#       name: name,
#       unit: unit,
#       history: historyArray
#     };
#   });

#   return { entities: expandedEntities };
# }
