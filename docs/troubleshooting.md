# Troubleshooting

## No fan entities appear

The integration listens for JSON UDP state datagrams on port `5625`. Check that
Home Assistant and the provisioned fan are on the same reachable network and
that local UDP broadcasts are permitted. The integration does not scan other
addresses or send a discovery request.

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

## Reporting an observation

Do not attach unredacted packet captures or logs. Include the confirmed model
and firmware, exact reported series, one controlled action, repeated results,
and sanitized state fields. Remove MAC addresses, IP addresses, serials, Wi-Fi
details, and tokens.
