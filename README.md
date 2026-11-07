# Atomberg Independent

An independent Home Assistant integration project for locally controlling
Atomberg smart fans.

> **Early development:** this release does not discover or control fans yet.
> The Aris Contour has not been independently identified from its local series
> code or protocol messages. No fan or light entities are exposed and no
> network traffic is sent. Do not install it expecting working device controls.

The implementation is being developed independently. It does not copy or adapt
source code from other integrations. Protocol behavior must be established
through controlled observations and documented evidence before it is added.

## Current status

- Home Assistant integration setup and a single-instance config flow.
- An empty-by-default registry for explicitly verified model capabilities.
- Opaque stable-identifier hashing for future device identity without retaining
  or logging the original identifier.
- Diagnostics that report readiness without exposing device or network data.
- Integration and config-entry version metadata for Home Assistant upgrades.
- Unit tests for the model registry and identifier handling.
- No discovery, transport, protocol commands, fan controls, or lighting
  controls.

## Installation

This project is not ready for normal use. For development, copy
`custom_components/atomberg_independent` into your Home Assistant
`config/custom_components/` directory, restart Home Assistant, then add
**Atomberg Independent** from **Settings → Devices & services**. The integration
will create a config entry but no device entities.

## Development

Run the hardware-independent tests with Python 3:

```sh
python3 -m unittest discover -s tests -v
```

Release and Home Assistant configuration migration guidance is in
[docs/versioning.md](docs/versioning.md). Protocol research and privacy guidance
is in [docs/protocol-notes.md](docs/protocol-notes.md).
The empty [docs/hardware-matrix.md](docs/hardware-matrix.md) is intended to
record only hardware that has actually been examined.

## Safety and privacy

- No credentials, account access, or cloud service is used.
- No network discovery or control is performed by this foundation.
- Do not commit raw packet captures, full hardware identifiers, Wi-Fi details,
  tokens, or other household network information.
- Do not expose a capability until it has evidence for the specific model.
