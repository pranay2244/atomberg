"""Constants for the Atomberg integration."""

DOMAIN = "atomberg_independent"
NAME = "Atomberg"
INTEGRATION_VERSION = "0.4.8"
INTEGRATION_STATUS = "local_wifi_unverified"

PLATFORMS = ("fan", "light", "number", "select", "sensor", "switch")
STATE_PORT = 5625
COMMAND_PORT = 5600
MAX_DATAGRAM_SIZE = 4096
MAX_DEVICES = 32
DEVICE_TIMEOUT_SECONDS = 180
UPDATE_INTERVAL_SECONDS = 30
STATE_REFRESH_SECONDS = 60

CONF_PREFER_BLUETOOTH = "prefer_bluetooth"
CONF_MODEL_OVERRIDE = "model_override"
CONF_LIGHT_LOW_BRIGHTNESS = "light_low_brightness"
CONF_LIGHT_HIGH_BRIGHTNESS = "light_high_brightness"
