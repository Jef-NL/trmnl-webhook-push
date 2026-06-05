"""Constants for the TRMNL Entity Push integration."""
DOMAIN = "trmnl_sensor_push"
CONF_URL = "webhook_url"
DEFAULT_URL = "https://usetrmnl.com/api/custom_plugins/XXXX-XXXX-XXXX-XXXX"  # Example URL
CONF_INTERVAL = "publish_interval"
DEFAULT_INTERVAL = 7.5  # Default to 7.5 minutes
MIN_TIME_BETWEEN_UPDATES = 450  # Push every 7.5min to ensure new data every 15min screen refresh
TRMNL_LABEL_NAME = "TRMNL"
