# Protocol notes

## Implemented behavior

The independently written Wi-Fi transport follows the public behavioral
description of local fan UDP control:

- Device state is received as JSON datagrams on UDP `5625`.
- Commands are JSON datagrams sent to the announcing device on UDP `5600`.
- A stable `device_id` is required to create a device.
- Reported series, state, and optional capability fields are accepted only
  after type/range validation.
- Supported command fields are `power`, `speed`, `boost`, `led`, `brightness`,
  `sleep`, and `timer`.

The series/model table and command field names are informed by the public
integration README and public hardware observations. No source code from the
referenced integration is used. The current parser supports the JSON shape
`{"device_id":"…","power":true,"speed":3}` and common nested `device`,
`data`, `state`, or `payload` objects. Other packet encodings are ignored.

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
- Commands are sent only to the source address of a valid state datagram.
- Invalid values and unsupported command fields are rejected before sending.
- UDP send success is not treated as device acknowledgment. State changes are
  reflected only after a later valid state datagram.
- Bluetooth and colour-temperature command encoding remain unimplemented.
- No packet format or model mapping is hardware-verified by this project yet.

## Evidence record

The implementation has not been tested with a physical fan. The documented
series mappings and control surface are provisional and must be validated on
each supported model before making hardware compatibility claims.

For new observations, record the confirmed device-label model, the exact
advertised series, firmware if available, one controlled action, the sanitized
before/after state, and repeatability. Do not publish unredacted captures.
