"""Constants for the Atomberg Independent integration."""

DOMAIN = "atomberg_independent"
NAME = "Atomberg Independent"
INTEGRATION_VERSION = "0.3.0"
INTEGRATION_STATUS = "local_wifi_unverified"

PLATFORMS = ("fan", "light", "switch", "select", "sensor")
STATE_PORT = 5625
COMMAND_PORT = 5600
MAX_DATAGRAM_SIZE = 4096
DEVICE_TIMEOUT_SECONDS = 180
UPDATE_INTERVAL_SECONDS = 30

CONF_PREFER_BLUETOOTH = "prefer_bluetooth"
CONF_MODEL_OVERRIDE = "model_override"
