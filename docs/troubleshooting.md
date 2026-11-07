# Troubleshooting

## No fan entities appear

The integration listens for presence beacons and hex-encoded JSON state
datagrams on UDP port `5625`. Check that Home Assistant and the provisioned fan
are on the same reachable network and that local UDP broadcasts are permitted.
The integration does not scan other addresses.

## The fan appears but controls do not take effect

Commands are sent to the device's last announcing address on UDP `5600`. A
successful local UDP send is not an acknowledgment; entities update from a
subsequent state broadcast. Check local network isolation/firewall rules and
Home Assistant logs. Bluetooth fallback is not implemented in this release.

## The model is shown as a series rather than a retail model

The integration reports the exact advertised series code and only shows the
family association as a hint. This avoids repeating a potentially incorrect
retail-model classification. The Aris Contour's series/model relationship
still needs direct validation.

## Diagnostics

Diagnostics include integration and Home Assistant versions, config-entry
schema version, reported series, and online status. Raw device identifiers,
network addresses, credentials, and raw protocol payloads are omitted.

## Lifecycle and protocol logging

At INFO level, the integration logs setup, listener readiness, setup completion,
Home Assistant shutdown, config-entry unload, listener stop, newly discovered
devices, and device timeouts. Device messages use a shortened one-way hash
rather than a MAC address. At DEBUG level, it logs an unrecognized packet's
size, outgoing command hashes, and one temporary protocol diagnostic per
device and packet type (presence and full-state). Protocol diagnostics include
the reported series and numeric status word when present, but not a source IP
or raw packet payload.

For lifecycle logs, enable the integration logger in Home Assistant's
`configuration.yaml`. Add the coordinator logger for protocol diagnostics:

```yaml
logger:
  default: warning
  logs:
    custom_components.atomberg_independent: info
    custom_components.atomberg_independent.coordinator: debug
```

Restart Home Assistant, reproduce the observation, then remove the
integration-specific logger entries and restart again. DEBUG-level unknown
packet messages are emitted per packet, so disable coordinator DEBUG when it is
not needed. Do not share full logs; retain only relevant sanitized messages and
redact device hashes before publishing them.

## Reporting an observation

Do not attach unredacted packet captures or logs. Include the confirmed model
and firmware, exact reported series, one controlled action, repeated results,
and sanitized state fields. Remove MAC addresses, IP addresses, serials, Wi-Fi
details, and tokens.
