import logging

from custom_components.uber_eats.api import UberEatsApi
from custom_components.uber_eats.const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry):
    """Set up Uber Eats as config entry."""
    hass.data[DOMAIN] = UberEatsApi(entry.data["sid_token"])
    hass.async_create_task(hass.config_entries.async_forward_entry_setup(entry, "sensor"))
    return True
