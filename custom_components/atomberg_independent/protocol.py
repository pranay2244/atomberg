"""Small, validated helpers for the locally observed JSON datagram protocol."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .const import MAX_DATAGRAM_SIZE


_SERIES_PATTERN = re.compile(r"(?<![A-Z0-9])([IRSMK]\d+)(?![A-Z0-9])", re.IGNORECASE)
_IDENTIFIER_KEYS = ("device_id", "deviceId", "deviceID")
_SERIES_KEYS = ("series", "series_code", "seriesCode", "model_code", "modelCode")
_NESTED_KEYS = ("device", "data", "state", "payload")


@dataclass(frozen=True)
class FanState:
    """Validated state fields extracted from one fan datagram."""

    device_id: str
    series: str | None
    power: bool | None = None
    speed: int | None = None
    sleep: bool | None = None
    timer: int | None = None
    led: bool | None = None
    brightness: int | None = None
    light_mode: str | None = None
    firmware: str | None = None


def _find_value(objects: list[dict[str, Any]], keys: tuple[str, ...]) -> Any:
    for obj in objects:
        for key in keys:
            if key in obj:
                return obj[key]
    return None


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in ("true", "on", "1"):
            return True
        if normalized in ("false", "off", "0"):
            return False
    return None


def _as_int(value: Any, minimum: int, maximum: int) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if minimum <= parsed <= maximum else None


def _as_timer(value: Any) -> int | None:
    """Return only timer values supported by the Home Assistant control."""
    parsed = _as_int(value, 0, 6)
    return parsed if parsed in (0, 1, 2, 3, 6) else None


def _clean_text(value: Any, maximum_length: int = 64) -> str | None:
    if not isinstance(value, str):
        return None
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        return None
    result = value.strip()
    if not result or len(result) > maximum_length:
        return None
    return result


def parse_datagram(payload: bytes) -> FanState | None:
    """Parse a JSON discovery/state datagram; ignore unknown or malformed input."""
    if not payload or len(payload) > MAX_DATAGRAM_SIZE:
        return None
    try:
        message = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(message, dict):
        return None

    objects = [message]
    for key in _NESTED_KEYS:
        nested = message.get(key)
        if isinstance(nested, dict):
            objects.append(nested)

    device_id = _clean_text(_find_value(objects, _IDENTIFIER_KEYS))
    if device_id is None:
        return None

    series = _clean_text(_find_value(objects, _SERIES_KEYS), 32)
    if series and not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", series):
        series = None
    if series is None:
        advertised_name = _clean_text(
            _find_value(objects, ("name", "local_name", "localName")), 128
        )
        if advertised_name:
            match = _SERIES_PATTERN.search(advertised_name)
            if match:
                series = match.group(1).upper()
    if series is not None:
        series = series.upper()

    return FanState(
        device_id=device_id,
        series=series,
        power=_as_bool(_find_value(objects, ("power", "is_on", "isOn"))),
        speed=_as_int(_find_value(objects, ("speed", "fan_speed", "fanSpeed")), 0, 6),
        sleep=_as_bool(_find_value(objects, ("sleep", "sleep_mode", "sleepMode"))),
        timer=_as_timer(_find_value(objects, ("timer", "timer_hours", "timerHours"))),
        led=_as_bool(_find_value(objects, ("led", "light", "light_on", "lightOn"))),
        brightness=_as_int(_find_value(objects, ("brightness", "light_brightness")), 0, 100),
        light_mode=_clean_text(
            _find_value(objects, ("light_mode", "lightMode", "color_mode", "colorMode")),
            32,
        ),
        firmware=_clean_text(_find_value(objects, ("firmware", "firmware_version")), 64),
    )


def encode_command(**fields: bool | int | str) -> bytes:
    """Encode only the documented control fields with strict value validation."""
    allowed = {"power", "speed", "boost", "led", "brightness", "sleep", "timer"}
    if not fields or set(fields) - allowed:
        raise ValueError("Unsupported or empty fan command")

    for key, value in fields.items():
        if key in {"power", "boost", "led", "sleep"} and not isinstance(value, bool):
            raise ValueError(f"{key} must be a boolean")
        if key == "speed" and (
            isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 6
        ):
            raise ValueError("speed must be an integer from 1 to 6")
        if key == "brightness" and (
            isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 100
        ):
            raise ValueError("brightness must be an integer from 0 to 100")
        if key == "timer" and (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value not in (0, 1, 2, 3, 6)
        ):
            raise ValueError("timer must be one of 0, 1, 2, 3, or 6 hours")
    return json.dumps(fields, separators=(",", ":"), sort_keys=True).encode()


def percentage_to_speed(percentage: int) -> int:
    """Map Home Assistant percentage to one of the fan's six discrete levels."""
    if isinstance(percentage, bool) or not isinstance(percentage, int):
        raise ValueError("percentage must be an integer")
    if not 1 <= percentage <= 100:
        raise ValueError("percentage must be from 1 to 100")
    return max(1, min(6, (percentage * 6 + 50) // 100))


def speed_to_percentage(speed: int) -> int | None:
    """Map a reported discrete speed to Home Assistant percentage."""
    if isinstance(speed, bool) or not isinstance(speed, int) or not 1 <= speed <= 6:
        return None
    return round(speed * 100 / 6)
