"""Privacy-preserving device identity helpers."""

from __future__ import annotations

import hashlib
import re


def stable_device_key(identifier: str) -> str:
    """Hash an opaque stable device identifier without retaining its raw value."""
    normalized = identifier.strip()
    if not normalized:
        raise ValueError("A stable device identifier cannot be empty")
    compact = re.sub(r"[:-]", "", normalized)
    if re.fullmatch(r"[0-9a-fA-F]{12}", compact):
        normalized = compact.lower()
    return hashlib.sha256(
        b"atomberg-independent\x00" + normalized.encode("utf-8")
    ).hexdigest()


def device_display_name(device_key: str, series: str | None) -> str:
    """Create a stable, MAC-safe name that distinguishes same-series devices."""
    series_label = f" {series}" if series else ""
    return f"Atomberg fan{series_label} - {device_key[:8].upper()}"
