# Atomberg

An independently implemented Home Assistant integration for local control of
Atomberg smart fans. It does not use cloud accounts or copy another
integration's source code.

## Version 1.0.0

This is the current stable release.

The integration listens for the documented local UDP packet formats:

- Wi-Fi UDP state listening on port `5625` and commands to the discovered
  device on port `5600`.
- Presence beacons (`<MAC>_<series>`) and hex-encoded JSON full-state packets.
- A bounded state-read request after discovery and periodically thereafter.
- Home Assistant fan entity with power and six discrete speed levels for
  recognized series.
- Light on/off, brightness and light-mode commands where the series profile
  supports them. Attribute commands are sent separately from LED power.
- For M1-reported fans, an optional three-position companion slider (Off, Low,
  High) is available after configuring distinct, observed protocol brightness
  values in the integration options. No Low/High values are assumed by default.
- Sleep-mode switch and off-timer select.
- Connection and reported-series diagnostic sensors.
- Stable device identity across restarts without exposing the raw identifier
  in entity IDs or diagnostics.
- Distinct, stable Home Assistant device names for multiple fans in the same
  series.
- Entities can be recreated after their Home Assistant registry entries are
  manually removed, while ordinary offline/online transitions keep the same
  entity objects.
- Model-family hints based on reported series codes. A series code is not
  treated as proof of the retail model.

Bluetooth transport and unknown packet encodings are not implemented. The
presence and full-state packet formats have been observed in sanitized captures
from five physical fans; all five reported `M1` in both packet types. This
confirms those observed packet envelopes and series fields, not the fans'
retail models or every decoded state bit. The Aris Contour association for
series `I5` remains a family hint, not verified retail model identification.
The integration does not receive command acknowledgments; reported state is
updated from subsequent fan broadcasts, not optimistically from a successful
UDP send.

The Aris Contour Moonbeam specification describes two light intensities. The
integration is designed to represent these as a separate Off/Low/High number
slider, not as a continuous light brightness control. Configure the fan-reported
brightness values for Low and High from observed state packets in the
integration's options. Until both values are configured, only the light on/off
entity is available for M1-reported fans. The slider is a companion entity,
not a control inside the light card.

## Aris Contour model identification

The public reference lists `I5` in the Aris Contour family and `M1` in an
Efficio family. This integration uses `I5` as an Aris Contour family hint and
`M1` as an Efficio family hint only. The series sensor preserves the reported
code; series alone does not establish a fan's retail model.

## Installation through HACS

The HACS default-store submission is pending review. Until it is accepted, add
the repository as a custom repository in HACS:

1. Open **HACS → Integrations → ⋮ → Custom repositories**.
2. Add `https://github.com/pranay2244/atomberg` with category **Integration**.
3. Find **Atomberg** in HACS, download it, and restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration** and choose
   **Atomberg**.

To enable the M1 three-position light slider after setup, open the integration
options and enter the observed protocol brightness values for the Low and High
light states. Leave both values unset until those states have been captured;
the slider is not created until both values are set.

## Manual installation

This is an early-development custom integration for Home Assistant 2024.8 or
newer. To install it manually:

1. Copy `custom_components/atomberg_independent` into your Home Assistant
   `config/custom_components/` directory.
2. Restart Home Assistant.
3. Go to **Settings → Devices & services → Add integration** and choose
   **Atomberg**.
4. Ensure Home Assistant and the provisioned fan are on a network that permits
   local UDP broadcast and traffic to the fan's UDP port `5600`.
5. Disable any other integration listening on UDP port `5625` while testing;
   UDP port sharing can cause discovery packets to be missed.
6. If an already-running fan does not appear, change its state once with the
   physical remote and allow its local presence broadcast to reach Home Assistant.

The integration listens for fan datagrams; it does not scan arbitrary network
addresses or send commands before a fan has announced itself. A Bluetooth
adapter is not used by this release.

## Apple Home through HomeKit Bridge

Atomberg exposes a standard Home Assistant fan entity with power and six
discrete speed levels. To control fans from Apple Home, use Home Assistant's
official HomeKit Bridge:

1. In Home Assistant, open **Settings → Devices & services → Add integration**
   and add **HomeKit Bridge**.
2. Configure the bridge to include only the Atomberg `fan` entities. Do not
   expose diagnostic sensors, timer selects, or companion number entities for
   this fan-control setup. Use one bridge.
3. Complete bridge setup and scan the QR code shown by Home Assistant in
   Apple's Home app using **Add Accessory**.

The bridge exposes the fan's native on/off and rotation-speed controls. Speed
and power state in Home Assistant and Apple Home follow subsequent fan
broadcasts; the integration does not optimistically change reported state.
Home Assistant's `fan.increase_speed` and `fan.decrease_speed` actions step
through physical speeds. Apple Home exposes a rotation-speed slider rather
than separate step-up/step-down controls.

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
  diagnostics. Logs use shortened one-way device hashes and never include raw
  packet payloads or network addresses. See
  [troubleshooting](docs/troubleshooting.md) for lifecycle and protocol logging.
-   The Aris Contour retail-model mapping and the Low/High light-stage mapping
  have not been verified from controlled physical state transitions.
- Do not publish raw packet captures, complete hardware identifiers, network
  addresses, credentials, or tokens.
