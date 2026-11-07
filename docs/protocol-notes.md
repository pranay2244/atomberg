# Protocol investigation notes

There are no verified protocol observations for this implementation yet.
Protocol code must not be added based only on a product name, an unverified
model mapping, or behavior inferred from another implementation.

## Observation record

For each controlled observation, record:

- Date and test setup (without private network details).
- Actual model and hardware revision, when confirmed from the device label.
- Firmware version, if available.
- Transport and network conditions.
- One action performed and the before/after observations.
- Whether the result was repeated.
- Interpretation and confidence: confirmed, probable, or unknown.
- A reference to a redacted fixture or test, if one is safe to publish.

Keep raw packet captures private until reviewed for credentials, stable device
identifiers, network addresses, and unrelated household traffic. Do not send
speculative commands to a fan in normal use.

## Implementation gate

Only add message formats, identifiers, command values, or model capabilities
after a reproducible observation supports them. Add parser and encoder tests
from redacted observations before enabling a transport or exposing entities.
