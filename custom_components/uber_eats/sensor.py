"""Uber Eats sensors"""
import logging
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_TOKEN
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, SENSOR_NAME

NAME = DOMAIN
ISSUEURL = "https://github.com/coseto6125/ha-uber-eats-aiohttp/issues"

STARTUP = f"""
-------------------------------------------------------------------
{NAME}
如果您有任何問題，可以前往 github 提交 issue：{ISSUEURL}
-------------------------------------------------------------------
"""

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_TOKEN): cv.string,
    }
)

SCAN_INTERVAL = timedelta(seconds=20)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Uber Eats sensor based on a config entry."""
    api = hass.data[DOMAIN]
    async_add_entities([UberEatsDeliveriesSensor(SENSOR_NAME, api)], True)


class UberEatsDeliveriesSensor(Entity):

    def __init__(self, name, api):
        self._name = name
        self._icon = "mdi:truck-delivery"
        self._state = ""
        self._state_attributes = {}
        self._unit_of_measurement = None
        self._device_class = "running"
        self._unique_id = DOMAIN
        self._api = api

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return self._state_attributes

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._unique_id

    def update(self):
        _LOGGER.debug("Checking login validity")
        if self._api.check_auth():
            _LOGGER.debug("Fetching deliveries")
            response = self._api.get_deliveries()
            if response["data"].get("orders"):
                _LOGGER.debug(response["data"]["orders"])
                for order in response["data"]["orders"]:
                    if order["feedCards"][0]["status"]["currentProgress"] == 1:
                        self._state = "Preparing your order"
                    elif order["feedCards"][0]["status"]["currentProgress"] == 2:
                        self._state = "Preparing your order"
                    elif order["feedCards"][0]["status"]["currentProgress"] == 3:
                        self._state = "Heading your way"
                    elif order["feedCards"][0]["status"]["currentProgress"] == 4:
                        self._state = "Almost here"
                    else:
                        self._state = (f"Unknown currentProgress ({(order["feedCards"][0]["status"]["currentProgress"])})")

                    # self._state_attributes['Order Id'] = order['uuid']
                    self._state_attributes["ETA"] = order["feedCards"][0]["status"]["title"]
                    self._state_attributes["Order Status Description"] = order["feedCards"][0]["status"][
                        "timelineSummary"
                    ]
                    self._state_attributes["Order Status"] = order["feedCards"][0]["status"]["currentProgress"]
                    self._state_attributes["Restaurant Name"] = order["activeOrderOverview"]["title"]
                    self._state_attributes["Courier Name"] = order["contacts"][0]["title"]

                    if order["feedCards"][1]["mapEntity"]:
                        if order["feedCards"][1]["mapEntity"][0]:
                            self._state_attributes["Courier Location"] = (
                                str(order["feedCards"][1]["mapEntity"][0]["latitude"])
                                + ","
                                + str(order["feedCards"][1]["mapEntity"][0]["longitude"])
                            )
            else:
                self._state = "None"
        _LOGGER.error("Unable to log in")
