"""Constants for the Atomberg Independent integration."""

DOMAIN = "atomberg_independent"
NAME = "Atomberg Independent"
INTEGRATION_VERSION = "0.4.0"
INTEGRATION_STATUS = "local_wifi_unverified"

PLATFORMS = ("fan", "light", "switch", "select", "sensor")
STATE_PORT = 5625
COMMAND_PORT = 5600
MAX_DATAGRAM_SIZE = 4096
MAX_DEVICES = 32
DEVICE_TIMEOUT_SECONDS = 180
UPDATE_INTERVAL_SECONDS = 30
STATE_REFRESH_SECONDS = 60

CONF_PREFER_BLUETOOTH = "prefer_bluetooth"
CONF_MODEL_OVERRIDE = "model_override"
