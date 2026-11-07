# Troubleshooting

## No fan entities appear

This is expected in the current research-foundation release. Device discovery,
transports, and controls have not been implemented. The integration config flow
only creates an entry; it does not contact the local network.

## Diagnostics

The config-entry diagnostics report implementation readiness only. They do not
include device identifiers, addresses, credentials, or raw protocol data.

## Reporting an observation

Do not attach unredacted packet captures or logs. Include the confirmed model
and firmware, test setup at a high level, the single action performed, repeated
results, and a sanitized summary of the observed behavior.
