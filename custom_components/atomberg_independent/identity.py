"""Privacy-preserving device identity helpers."""

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
