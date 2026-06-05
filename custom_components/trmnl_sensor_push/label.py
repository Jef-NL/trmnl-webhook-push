"""Label registry helpers for the TRMNL Entity Push integration."""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers import label_registry as lr

from .const import TRMNL_LABEL_NAME

_LOGGER = logging.getLogger(__name__)


def ensure_trmnl_label(hass: HomeAssistant) -> None:
    """Create the TRMNL label in the registry if it does not already exist."""
    registry = lr.async_get(hass)

    existing = next(
        (label for label in registry.labels.values() if label.name == TRMNL_LABEL_NAME),
        None,
    )

    if existing is None:
        registry.async_create(TRMNL_LABEL_NAME)
        _LOGGER.info("TRMNL: Created label '%s'", TRMNL_LABEL_NAME)
    else:
        _LOGGER.debug("TRMNL: Label '%s' already exists, skipping creation", TRMNL_LABEL_NAME)
