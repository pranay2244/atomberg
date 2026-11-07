# Atomberg Independent

An independently implemented Home Assistant integration for local control of
Atomberg smart fans. It does not use cloud accounts or copy another
integration's source code.

## Current release: 0.3.0

The integration currently supports provisioned fans that announce JSON state
datagrams on the local network:

- Wi-Fi UDP state listening on port `5625` and commands to the discovered
  device on port `5600`.
- Home Assistant fan entity with power and six discrete speed levels.
- Light on/off, and brightness for series that advertise that capability.
- Sleep-mode switch and off-timer select.
- Connection and reported-series diagnostic sensors.
- Stable device identity across restarts without exposing the raw identifier
  in entity IDs or diagnostics.
- Model-family hints based on reported series codes. A series code is not
  treated as proof of the retail model.

Bluetooth transport, Bluetooth-only setup, lighting colour-mode commands,
unknown packet encodings, and exact Aris Contour identification are not yet
implemented. The integration does not currently receive command acknowledgments;
reported state is updated from subsequent fan broadcasts, not optimistically
from a successful UDP send.

## Aris Contour model identification

The public reference documents `I1`–`I5` as the Aris/Aris Starlight family and
`M1` as an Efficio family hint. This integration does not convert an `M1` series
code into a confirmed Efficio retail model: Home Assistant identifies the device
by its reported series, and provides a separate series diagnostic sensor.
Retail model recognition for the Aris Contour requires its actual advertised
series and independent evidence.

## Installation

This is an early-development custom integration for Home Assistant 2024.8 or
newer. To test it:

1. Copy `custom_components/atomberg_independent` into your Home Assistant
   `config/custom_components/` directory.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration** and choose
   **Atomberg Independent**.
4. Ensure Home Assistant and the provisioned fan are on a network that permits
   local UDP broadcast and traffic to the fan's UDP port `5600`.
5. If an already-running fan does not appear, change its state once with the
   physical remote and allow its local state broadcast to reach Home Assistant.

The integration listens for fan datagrams; it does not scan arbitrary network
addresses or send commands before a device has been heard from. A Bluetooth
adapter is not used by this release.

## Development

Run the hardware-independent tests with Python:

```sh
python3 -m unittest discover -s tests -v
```

Protocol notes, model evidence, troubleshooting, and Home Assistant release
versioning are documented in [docs/](docs/).

## Safety and privacy

- Device control is sent only to a fan that announced itself to Home Assistant.
- No internet or cloud calls are made.
- Device identifiers and local addresses are omitted from integration logs and
  diagnostics.
- The integration has not been hardware-validated against the Aris Contour.
- Do not publish raw packet captures, complete hardware identifiers, network
  addresses, credentials, or tokens.
