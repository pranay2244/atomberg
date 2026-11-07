# Protocol notes

## Implemented behavior

The independently written Wi-Fi transport follows the public behavioral
description of local fan UDP control:

- Presence beacons are ASCII `<device_id>_<series>` datagrams on UDP `5625`.
- Full state is a hex-encoded JSON envelope containing `device_id` and a
  comma-separated `state_string`.
- Commands are JSON datagrams sent to the announcing device on UDP `5600`.
- Device IDs must be valid unicast MAC addresses. Packets from non-private
  source addresses are ignored, and discovery is limited to 32 active devices.
  Stale entries are marked unavailable and evicted from the in-memory registry,
  freeing capacity. Their Home Assistant entities remain registered and
  unavailable until the device is rediscovered and the entities are rebound.
- A bounded `{"read":1}` request is sent after presence discovery and at most
  once per minute thereafter.
- The first state word is decoded into power, speed, LED, sleep, brightness,
  timer hours, and light-mode hints with range validation.
- Provisional status masks: speed bits `0-2`, cool mode bit `3`, power bit `4`,
  LED bit `5`, sleep bit `7`, brightness bits `8-14`, warm mode bit `15`, and
  timer bits `16-19`. Series is read from the eighth CSV field.
- If neither light-mode bit is set, the mode remains unknown. Whether this
  represents the fan's default warm mode is unverified and needs a real
  Aris Contour state capture.
- The reported timer hours (`0`, `1`, `2`, `3`, `6`) map to wire command
  indices (`0`, `1`, `2`, `3`, `4`); six hours must not be sent as `timer: 6`.
- Light attribute commands (`brightness` and `light mode`) are sent separately
  from LED power commands.
- Supported command fields include `power`, `speed`, `boost`, `led`,
  `brightness`, `sleep`, `timer`, `light_mode`, and the `read` request.

The series/model table and command field names are informed by the public
integration README and the user's protocol review. No source code from the
referenced integration is used. Parser tests create synthetic examples in the
documented wire format; they are not genuine device captures. Other packet
encodings are ignored.

Behavioral references:

- [Atomberg Local README: transport and supported-series overview](https://github.com/allusv/atomberg-local#how-it-works)
- [Public R1 BLE field report](https://github.com/allusv/atomberg-local/issues/2)
- [Public hardware report: series-family table and limitations](https://github.com/allusv/atomberg-local#supported-models)

The public report of a CSV/status-bit BLE characteristic is not used here:
that report applies to BLE, whose service/characteristic identifiers and
reconnection behavior have not been independently established for this
implementation.

## Safety limits and limitations

- The listener binds the documented local state port and does not probe a
  subnet or send a discovery request.
- Commands are sent only to the private source address of a valid fan packet.
- Invalid values and unsupported command fields are rejected before sending.
- UDP send success is not treated as device acknowledgment. State changes are
  reflected only after a later valid state datagram.
- Bluetooth and colour-temperature control remain unimplemented.
- No packet format or model mapping is hardware-verified by this project yet.
- Source-address checks and MAC validation reduce accidental input but do not
  authenticate packets; another host on the LAN can spoof this UDP protocol.

## Evidence record

The implementation has not been tested with a physical fan. In particular,
the status bit mapping and `I5` Aris Contour family hint are provisional and
must be validated against sanitized captures from each supported model before
making hardware compatibility claims.

For new observations, record the confirmed device-label model, the exact
advertised series, firmware if available, one controlled action, the sanitized
before/after state, and repeatability. Do not publish unredacted captures.
