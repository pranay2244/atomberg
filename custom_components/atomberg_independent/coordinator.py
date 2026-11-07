"""Local UDP discovery, state, and command handling."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Callable, cast

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    COMMAND_PORT,
    DEVICE_TIMEOUT_SECONDS,
    MAX_DATAGRAM_SIZE,
    MAX_DEVICES,
    STATE_PORT,
    STATE_REFRESH_SECONDS,
    UPDATE_INTERVAL_SECONDS,
)
from .identity import stable_device_key
from .models import ModelProfile, resolve_model_profile
from .protocol import (
    FanState,
    encode_command,
    is_valid_source_address,
    parse_datagram,
)

LOGGER = logging.getLogger(__name__)


@dataclass
class FanDevice:
    """Current in-memory state for a device heard on the local network."""

    device_id: str
    device_key: str
    host: str
    series: str | None
    profile: ModelProfile
    last_seen: float
    last_read_at: float | None = None
    power: bool | None = None
    speed: int | None = None
    sleep: bool | None = None
    timer: int | None = None
    led: bool | None = None
    brightness: int | None = None
    light_mode: str | None = None
    firmware: str | None = None
    available: bool = True


class _FanDatagramProtocol(asyncio.DatagramProtocol):
    """Forward UDP datagrams to the device manager."""

    def __init__(self, manager: "FanManager") -> None:
        self.manager = manager

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.manager.transport = cast(asyncio.DatagramTransport, transport)

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        self.manager.handle_datagram(data, addr)

    def error_received(self, exc: Exception) -> None:
        LOGGER.warning(
            "Atomberg UDP transport reported %s", type(exc).__name__
        )


class FanManager:
    """Owns the UDP listener and live device state for one config entry."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.transport: asyncio.DatagramTransport | None = None
        self.devices: dict[str, FanDevice] = {}
        self._listeners: list[Callable[[FanDevice], None]] = []
        self._expiry_unsub: Callable[[], None] | None = None

    async def async_start(self) -> None:
        """Bind the documented local state port and start availability checks."""
        loop = asyncio.get_running_loop()
        await loop.create_datagram_endpoint(
            lambda: _FanDatagramProtocol(self),
            local_addr=("0.0.0.0", STATE_PORT),
            allow_broadcast=True,
            reuse_port=False,
        )
        self._expiry_unsub = async_track_time_interval(
            self.hass,
            self._expire_stale_devices,
            timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )

    async def async_stop(self) -> None:
        """Release listener resources."""
        if self._expiry_unsub:
            self._expiry_unsub()
            self._expiry_unsub = None
        if self.transport:
            self.transport.close()
            self.transport = None
        self._listeners.clear()

    def async_add_listener(self, callback: Callable[[FanDevice], None]) -> None:
        """Subscribe to discovery and state changes."""
        self._listeners.append(callback)
        for device in self.devices.values():
            callback(device)

    def handle_datagram(self, payload: bytes, addr: tuple[str, int]) -> None:
        """Validate and apply a fan state datagram."""
        if not is_valid_source_address(addr[0]):
            return

        parsed = parse_datagram(payload)
        if parsed is None:
            return

        key = stable_device_key(parsed.device_id)
        now = time.monotonic()
        device = self.devices.get(key)
        is_new = device is None
        if device is None:
            if len(self.devices) >= MAX_DEVICES:
                LOGGER.warning("Ignoring Atomberg device discovery limit")
                return
            profile = resolve_model_profile(parsed.series)
            device = FanDevice(
                device_id=parsed.device_id,
                device_key=key,
                host=addr[0],
                series=parsed.series,
                profile=profile,
                last_seen=now,
            )
            self.devices[key] = device
            LOGGER.info(
                "Discovered Atomberg fan (series=%s)",
                parsed.series or "unknown",
            )
        else:
            device.host = addr[0]
            device.last_seen = now
            device.available = True
            if parsed.series and parsed.series != device.series:
                device.series = parsed.series
                device.profile = resolve_model_profile(parsed.series)

        self._apply_state(device, parsed)
        if parsed.series and parsed.series != device.series:
            device.series = parsed.series
            device.profile = resolve_model_profile(parsed.series)
        for callback in tuple(self._listeners):
            callback(device)
        if is_new and not parsed.has_state:
            self._request_state_refresh(device, now)

    @staticmethod
    def _apply_state(device: FanDevice, state: FanState) -> None:
        """Apply only fields explicitly present and valid in the datagram."""
        if not state.has_state:
            return
        for state_field, device_field in (
            ("power", "power"),
            ("speed", "speed"),
            ("sleep", "sleep"),
            ("timer_hours", "timer"),
            ("led", "led"),
            ("brightness", "brightness"),
            ("light_mode", "light_mode"),
        ):
            value = getattr(state, state_field)
            if value is not None:
                setattr(device, device_field, value)

    def _request_state_refresh(self, device: FanDevice, now: float) -> None:
        """Ask an announced fan for state without sending repeated read packets."""
        if (
            not device.available
            or self.transport is None
            or (
                device.last_read_at is not None
                and now - device.last_read_at < STATE_REFRESH_SECONDS
            )
        ):
            return
        try:
            self.send_command(device, read=1)
        except RuntimeError as err:
            LOGGER.warning("Unable to request Atomberg fan state: %s", err)
            return
        device.last_read_at = now

    def _expire_stale_devices(self, _now: Any) -> None:
        """Mark devices offline after state broadcasts stop."""
        current_time = time.monotonic()
        for device in self.devices.values():
            available = current_time - device.last_seen <= DEVICE_TIMEOUT_SECONDS
            if available != device.available:
                device.available = available
                for callback in tuple(self._listeners):
                    callback(device)
            if available:
                self._request_state_refresh(device, current_time)

    def send_command(self, device: FanDevice, **fields: bool | int | str) -> None:
        """Send a validated command to a device heard on the local network."""
        self._send_command_payload(device, encode_command(**fields))

    def send_commands(
        self, device: FanDevice, payloads: tuple[bytes, ...]
    ) -> None:
        """Send a group of already validated, separate protocol commands."""
        for payload in payloads:
            self._send_command_payload(device, payload)

    def _send_command_payload(self, device: FanDevice, payload: bytes) -> None:
        """Send one encoded command to a previously discovered fan."""
        if not device.available or not device.host:
            raise RuntimeError("The Atomberg fan is not available on the local network")
        if self.transport is None:
            raise RuntimeError("The Atomberg local UDP listener is not running")
        if not payload or len(payload) > MAX_DATAGRAM_SIZE:
            raise ValueError("Invalid Atomberg command payload")
        self.transport.sendto(payload, (device.host, COMMAND_PORT))
        LOGGER.debug("Sent a local command to Atomberg device %s", device.device_key[:12])
