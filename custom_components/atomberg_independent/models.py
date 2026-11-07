"""Series-based Atomberg model hints and conservative capability profiles."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Capability(str, Enum):
    """Controls reported for a fan series."""

    FAN_POWER = "fan_power"
    FAN_SPEED = "fan_speed"
    SLEEP_MODE = "sleep_mode"
    OFF_TIMER = "off_timer"
    LIGHT_POWER = "light_power"
    LIGHT_BRIGHTNESS = "light_brightness"
    LIGHT_COLOR_MODE = "light_color_mode"


@dataclass(frozen=True)
class ModelProfile:
    """A best-effort series-family hint, not a verified retail model identity."""

    identifier: str
    name: str
    capabilities: frozenset[Capability]
    evidence_status: str = "unverified"


BASE_CAPABILITIES = frozenset(
    {
        Capability.FAN_POWER,
        Capability.FAN_SPEED,
        Capability.SLEEP_MODE,
        Capability.OFF_TIMER,
        Capability.LIGHT_POWER,
    }
)
DIMMABLE = BASE_CAPABILITIES | {Capability.LIGHT_BRIGHTNESS}
ARIS = DIMMABLE | {Capability.LIGHT_COLOR_MODE}

# Series names are approximate family hints from public documentation.
# Retail model names are deliberately not inferred from a series code.
MODEL_PROFILES: dict[str, ModelProfile] = {
    "R1": ModelProfile("R1", "Renesa family (series hint)", BASE_CAPABILITIES),
    "R2": ModelProfile("R2", "Renesa+ family (series hint)", BASE_CAPABILITIES),
    "R3": ModelProfile("R3", "Renesa Smart+ family (series hint)", BASE_CAPABILITIES),
    "S1": ModelProfile("S1", "Studio+ family (series hint)", frozenset(DIMMABLE)),
    "S2": ModelProfile(
        "S2",
        "Renesa Elite family (series hint)",
        frozenset(DIMMABLE),
        evidence_status="hardware-tested-by-reference-project",
    ),
    "M1": ModelProfile("M1", "Efficio family (series hint)", frozenset(DIMMABLE)),
    "M2": ModelProfile("M2", "Efficio+ family (series hint)", BASE_CAPABILITIES),
    "K1": ModelProfile(
        "K1",
        "Gorilla family (series hint)",
        BASE_CAPABILITIES
        - {Capability.LIGHT_POWER, Capability.LIGHT_BRIGHTNESS},
    ),
}

for _series_number in range(1, 6):
    _series = f"I{_series_number}"
    MODEL_PROFILES[_series] = ModelProfile(
        _series, "Aris family (series hint)", frozenset(ARIS)
    )

UNKNOWN_MODEL = ModelProfile(
    "unknown",
    "Unknown Atomberg series",
    BASE_CAPABILITIES,
)


def resolve_model_profile(identifier: str | None) -> ModelProfile:
    """Resolve a series code without treating its family name as device truth."""
    if identifier is None:
        return UNKNOWN_MODEL
    return MODEL_PROFILES.get(identifier.strip().upper(), UNKNOWN_MODEL)
