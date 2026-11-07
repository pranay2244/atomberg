"""Verified model capability registry.

The registry intentionally starts empty. Add a profile only after its model
identity and each listed capability have independent, repeatable evidence.
"""

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Iterable, Mapping, Optional


class Capability(str, Enum):
    """Controls that a verified model may expose."""

    FAN_POWER = "fan_power"
    FAN_SPEED = "fan_speed"
    SLEEP_MODE = "sleep_mode"
    OFF_TIMER = "off_timer"
    LIGHT_POWER = "light_power"
    LIGHT_BRIGHTNESS = "light_brightness"
    LIGHT_COLOR_MODE = "light_color_mode"


@dataclass(frozen=True)
class ModelProfile:
    """Evidence-backed capabilities for one model identifier."""

    identifier: str
    name: str
    capabilities: frozenset[Capability] = field(default_factory=frozenset)
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.identifier.strip():
            raise ValueError("A model profile requires a non-empty identifier")
        if not self.name.strip():
            raise ValueError("A model profile requires a non-empty display name")
        if not self.evidence:
            raise ValueError("A model profile requires an evidence reference")


UNKNOWN_MODEL = ModelProfile(
    identifier="unknown",
    name="Unknown Atomberg model",
    evidence=("No model profiles have been independently verified.",),
)

# Do not add a profile until evidence has been gathered for that specific model.
MODEL_PROFILES: Mapping[str, ModelProfile] = MappingProxyType({})


def resolve_model_profile(
    identifier: Optional[str],
    profiles: Mapping[str, ModelProfile] = MODEL_PROFILES,
) -> ModelProfile:
    """Return an exact known profile or the explicit unknown profile."""
    if identifier is None:
        return UNKNOWN_MODEL
    return profiles.get(identifier.strip().casefold(), UNKNOWN_MODEL)


def build_model_registry(
    profiles: Iterable[ModelProfile],
) -> Mapping[str, ModelProfile]:
    """Build a normalized registry and reject ambiguous duplicate identifiers."""
    registry: dict[str, ModelProfile] = {}
    for profile in profiles:
        key = profile.identifier.strip().casefold()
        if key in registry:
            raise ValueError("Duplicate model identifier: " + profile.identifier)
        registry[key] = profile
    return registry
