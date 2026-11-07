"""Validated parsing and command encoding for Atomberg local UDP packets."""

from __future__ import annotations

import ipaddress
import json
import re
from dataclasses import dataclass
from typing import Any

from .const import MAX_DATAGRAM_SIZE

_MAC_PATTERN = re.compile(
    r"^(?:[0-9a-fA-F]{12}|(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}|"
    r"(?:[0-9a-fA-F]{2}-){5}[0-9a-fA-F]{2})$"
)
_SERIES_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9-]{0,15}$")
_TIMER_HOURS_TO_INDEX = {0: 0, 1: 1, 2: 2, 3: 3, 6: 4}
_LIGHT_MODES = {"warm", "cool", "daylight"}


@dataclass(frozen=True)
class FanState:
    """Parsed presence or full-state packet."""

    device_id: str
    series: str | None
    has_state: bool
    power: bool | None = None
    speed: int | None = None
    sleep: bool | None = None
    timer_hours: int | None = None
    led: bool | None = None
    brightness: int | None = None
    light_mode: str | None = None


def _normalize_device_id(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not _MAC_PATTERN.fullmatch(normalized):
        return None
    device_id = re.sub(r"[:-]", "", normalized).lower()
    if device_id == "000000000000" or int(device_id[:2], 16) & 1:
        return None
    return device_id


def _normalize_series(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    series = value.strip()
    if not _SERIES_PATTERN.fullmatch(series):
        return None
    return series.upper()


def _parse_integer(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"-?\d{1,8}", value.strip()):
        return int(value.strip())
    return None


def is_valid_source_address(address: str) -> bool:
    """Accept only private, unicast local-network source addresses."""
    try:
        source = ipaddress.ip_address(address)
    except ValueError:
        return False
    return (
        source.is_private
        and not source.is_multicast
        and not source.is_unspecified
        and not source.is_loopback
        and not source.is_reserved
    )


def _decode_state_string(state_string: Any) -> dict[str, Any] | None:
    """Decode fields from the first status word of a CSV state string."""
    if not isinstance(state_string, str):
        return None
    fields = state_string.split(",")
    status = _parse_integer(fields[0].strip()) if fields else None
    if status is None or status < 0 or status > 0xFFFFFF:
        return None

    speed = status & 0x07
    brightness = (status & 0x7F00) >> 8
    timer_hours = (status & 0x0F0000) >> 16
    series_text = fields[7].strip() if len(fields) > 7 else None
    series = _normalize_series(series_text) if series_text else None
    if series_text and series is None:
        return None
    cool = bool(status & 0x08)
    warm = bool(status & 0x8000)
    light_mode = (
        "daylight" if cool and warm else "cool" if cool else "warm" if warm else None
    )
    return {
        "power": bool(status & 0x10),
        "speed": speed if speed <= 6 else None,
        "led": bool(status & 0x20),
        "sleep": bool(status & 0x80),
        "brightness": brightness if brightness <= 100 else None,
        "timer_hours": timer_hours if timer_hours in _TIMER_HOURS_TO_INDEX else None,
        "light_mode": light_mode,
        "series": series,
    }


def parse_presence(payload: bytes) -> FanState | None:
    """Parse the ASCII presence beacon ``<device_id>_<series>``."""
    if not payload or len(payload) > 128:
        return None
    try:
        message = payload.decode("ascii").strip()
    except UnicodeDecodeError:
        return None
    device_id_text, separator, series_text = message.partition("_")
    if not separator:
        return None
    device_id = _normalize_device_id(device_id_text)
    series = _normalize_series(series_text)
    if device_id is None or series is None:
        return None
    return FanState(device_id=device_id, series=series, has_state=False)


def parse_full_state(payload: bytes) -> FanState | None:
    """Parse a hex-encoded JSON envelope carrying ``device_id`` and ``state_string``."""
    if not payload or len(payload) > MAX_DATAGRAM_SIZE:
        return None
    try:
        encoded = payload.decode("ascii").strip()
        decoded = bytes.fromhex(encoded)
        envelope = json.loads(decoded)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(envelope, dict):
        return None

    device_id = _normalize_device_id(envelope.get("device_id"))
    if device_id is None:
        return None
    state = _decode_state_string(envelope.get("state_string"))
    if state is None:
        return None
    return FanState(
        device_id=device_id,
        series=state["series"],
        has_state=True,
        power=state["power"],
        speed=state["speed"],
        sleep=state["sleep"],
        timer_hours=state["timer_hours"],
        led=state["led"],
        brightness=state["brightness"],
        light_mode=state["light_mode"],
    )


def parse_datagram(payload: bytes) -> FanState | None:
    """Parse either a plain presence beacon or hex-encoded full-state packet."""
    if not payload or len(payload) > MAX_DATAGRAM_SIZE:
        return None
    presence = parse_presence(payload)
    if presence is not None:
        return presence
    return parse_full_state(payload)


def encode_command(**fields: bool | int | str) -> bytes:
    """Encode the documented command fields after strict validation."""
    allowed = {
        "power",
        "speed",
        "boost",
        "led",
        "brightness",
        "sleep",
        "timer",
        "light_mode",
        "read",
    }
    if not fields or set(fields) - allowed:
        raise ValueError("Unsupported or empty fan command")
    if "read" in fields and len(fields) > 1:
        raise ValueError("read must be sent as a separate command")
    if "led" in fields and {"brightness", "light_mode"} & fields.keys():
        raise ValueError("LED power and light attributes must be sent separately")

    for key, value in fields.items():
        if key in {"power", "boost", "led", "sleep", "read"}:
            if key == "read":
                if type(value) is not int or value != 1:
                    raise ValueError("read must be 1")
            elif not isinstance(value, bool):
                raise ValueError(f"{key} must be a boolean")
        elif key == "speed" and (
            isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 6
        ):
            raise ValueError("speed must be an integer from 1 to 6")
        elif key == "brightness" and (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 100
        ):
            raise ValueError("brightness must be an integer from 0 to 100")
        elif key == "timer" and (
            isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 4
        ):
            raise ValueError("timer command index must be from 0 to 4")
        elif key == "light_mode" and (
            not isinstance(value, str) or value not in _LIGHT_MODES
        ):
            raise ValueError("light_mode must be warm, cool, or daylight")
    return json.dumps(fields, separators=(",", ":"), sort_keys=True).encode()


def timer_hours_to_command_index(hours: int) -> int:
    """Convert the reported timer hours to the fan's command option index."""
    if isinstance(hours, bool) or not isinstance(hours, int):
        raise ValueError("Timer hours must be 0, 1, 2, 3, or 6")
    try:
        return _TIMER_HOURS_TO_INDEX[hours]
    except KeyError as err:
        raise ValueError("Timer hours must be 0, 1, 2, 3, or 6") from err


def build_light_commands(
    *, turn_on: bool = True, brightness: int | None = None, light_mode: str | None = None
) -> tuple[bytes, ...]:
    """Build separate LED and attribute commands; firmware ignores combined attributes."""
    commands: list[bytes] = []
    if brightness is not None:
        commands.append(encode_command(brightness=brightness))
    if light_mode is not None:
        commands.append(encode_command(light_mode=light_mode))
    if not commands:
        commands.append(encode_command(led=turn_on))
    return tuple(commands)


def home_assistant_brightness_to_percent(brightness: int) -> int:
    """Convert Home Assistant brightness to fan percent without dropping nonzero values."""
    if isinstance(brightness, bool) or not isinstance(brightness, int):
        raise ValueError("Brightness must be an integer")
    if not 0 <= brightness <= 255:
        raise ValueError("Brightness must be between 0 and 255")
    if brightness == 0:
        return 0
    return max(1, round(brightness * 100 / 255))


def validate_light_stage_brightness(
    low: Any, high: Any
) -> tuple[int, int] | None:
    """Validate configured protocol brightness values for the low and high stages."""
    if low is None and high is None:
        return None
    for value in (low, high):
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 1 <= value <= 100
        ):
            raise ValueError("Both light-stage brightness values must be from 1 to 100")
    if low == high:
        raise ValueError("Low and high light-stage brightness values must differ")
    return low, high


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
