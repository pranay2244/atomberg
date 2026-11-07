# Atomberg Independent

An independently implemented Home Assistant integration for local control of
Atomberg smart fans. It does not use cloud accounts or copy another
integration's source code.

## Current release: 0.4.0

The integration listens for the documented local UDP packet formats:

- Wi-Fi UDP state listening on port `5625` and commands to the discovered
  device on port `5600`.
- Presence beacons (`<MAC>_<series>`) and hex-encoded JSON full-state packets.
- A bounded state-read request after discovery and periodically thereafter.
- Home Assistant fan entity with power and six discrete speed levels for
  recognized series.
- Light on/off, brightness and light-mode commands where the series profile
  supports them. Attribute commands are sent separately from LED power.
- Sleep-mode switch and off-timer select.
- Connection and reported-series diagnostic sensors.
- Stable device identity across restarts without exposing the raw identifier
  in entity IDs or diagnostics.
- Model-family hints based on reported series codes. A series code is not
  treated as proof of the retail model.

Bluetooth transport and unknown packet encodings are not implemented. The
Aris Contour association for series `I5` is a family hint, not verified retail
model identification. No physical fan packet capture has yet been validated
by this project. The integration does not receive command acknowledgments;
reported state is updated from subsequent fan broadcasts, not optimistically
from a successful UDP send.

## Aris Contour model identification

The public reference lists `I5` in the Aris Contour family and `M1` in an
Efficio family. This integration uses `I5` as an Aris Contour family hint and
does not identify the device as Efficio unless its reported series is `M1`.
The series sensor preserves the reported code; retail model identity remains
unverified without evidence from the physical fan.

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
5. Disable any other integration listening on UDP port `5625` while testing;
   UDP port sharing can cause discovery packets to be missed.
6. If an already-running fan does not appear, change its state once with the
   physical remote and allow its local presence broadcast to reach Home Assistant.

The integration listens for fan datagrams; it does not scan arbitrary network
addresses or send commands before a fan has announced itself. A Bluetooth
adapter is not used by this release.

## Development

Run the hardware-independent tests with Python:

```sh
python3 -m unittest discover -s tests -v
```

Protocol notes, model evidence, troubleshooting, and Home Assistant release
versioning are documented in [docs/](docs/).

## Safety and privacy

- Commands are sent only to the private source address of a validated fan
  announcement. The UDP protocol is unauthenticated and is not secure against
  another host spoofing packets on an untrusted local network.
- No internet or cloud calls are made.
- Device identifiers and local addresses are omitted from integration logs and
  diagnostics.
- The integration has not been hardware-validated against the Aris Contour.
- Do not publish raw packet captures, complete hardware identifiers, network
  addresses, credentials, or tokens.
