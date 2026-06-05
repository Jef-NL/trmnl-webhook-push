def create_entity_payload(state) -> dict:
    """Create the payload for a single entity with filtered attributes."""
    # Limited set of attributes to save on message size
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