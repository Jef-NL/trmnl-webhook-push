"""Label registry helpers for the TRMNL Entity Push integration."""
from __future__ import annotations

import logging
from enum import Enum
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import Template
from homeassistant.helpers import label_registry as lr

from .const import TRMNL_LABEL_NAME

_LOGGER = logging.getLogger(__name__)


class TRMNLLabel(Enum):
    DEFAULT = (TRMNL_LABEL_NAME, None, None)
    ONE_H = (f"{TRMNL_LABEL_NAME}_1h", timedelta(
        hours=1), timedelta(minutes=5))
    FOUR_H = (f"{TRMNL_LABEL_NAME}_4h", timedelta(
        hours=4), timedelta(minutes=30))
    EIGHT_H = (f"{TRMNL_LABEL_NAME}_8h",
               timedelta(hours=8), timedelta(hours=1))
    TWELVE_H = (f"{TRMNL_LABEL_NAME}_12h",
                timedelta(hours=12), timedelta(hours=1))
    ONE_W = (f"{TRMNL_LABEL_NAME}_1w", timedelta(weeks=1), timedelta(hours=12))
    TEN_D = (f"{TRMNL_LABEL_NAME}_10d", timedelta(
        days=10), timedelta(hours=24))

    def __init__(self, label: str, duration: timedelta | None, interval: timedelta | None):
        self.label = label
        self.duration = duration
        self.interval = interval


@dataclass
class TRMNLEntity:
    entity_id: str
    trmnl_label: TRMNLLabel


def ensure_trmnl_label(hass: HomeAssistant) -> None:
    """Create the TRMNL label in HA if it does not already exist.

    This function is idempotent - safe to call on every startup.
    It checks for an existing label by name before creating one,
    so it will never create duplicates.
    """
    registry = lr.async_get(hass)

    existing = next(
        (label for label in registry.labels.values()
         if label.name == TRMNL_LABEL_NAME),
        None,
    )

    if existing is None:
        registry.async_create(TRMNL_LABEL_NAME)
        _LOGGER.info("TRMNL: Created label '%s'", TRMNL_LABEL_NAME)
    else:
        _LOGGER.debug(
            "TRMNL: Label '%s' already exists, skipping creation", TRMNL_LABEL_NAME)


def get_labelled_entities(hass: HomeAssistant) -> list[TRMNLEntity]:
    """Return TRMNLEntity entries for all entities carrying any TRMNL label.

    If an entity has multiple TRMNL labels, the one with the longest duration wins.
    """
    _LOGGER.debug("TRMNL: Fetching entities with TRMNL labels")
    entities: list[TRMNLEntity] = []
    seen: set[str] = set()

    # Iterate largest duration first so the most specific label wins
    sorted_labels = sorted(
        TRMNLLabel,
        key=lambda l: l.duration.total_seconds() if l.duration is not None else 0,
        reverse=True,
    )

    for trmnl_label in sorted_labels:
        template = Template(
            f"{{{{ label_entities('{trmnl_label.label}') }}}}", hass
        )
        result = template.async_render()
        _LOGGER.debug(
            "TRMNL: Label '%s' rendered result: %s", trmnl_label.label, result
        )
        if not isinstance(result, list):
            continue
        for entity_id in result:
            if entity_id not in seen:
                seen.add(entity_id)
                entities.append(TRMNLEntity(
                    entity_id=entity_id, trmnl_label=trmnl_label))

    return entities
