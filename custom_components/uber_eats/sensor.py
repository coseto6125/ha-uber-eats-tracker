"""Uber Eats sensors"""
import logging
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_TOKEN
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, ORDER_STATES

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
    api = hass.data[DOMAIN]
    order_summary_sensor = UberEatsOrderSummarySensor("Order Summary", api)
    async_add_entities([order_summary_sensor], True)

    entities = [UberEatsDeliveriesSensor(f"Order {i}", order_summary_sensor, api) for i in range(1, 4)]
    async_add_entities(entities, True)


class UberEatsOrderSummarySensor(Entity):

    def __init__(self, name, api):
        self._name = name
        self._icon = "mdi:shopping-search"
        self._state = 0
        self._state_attributes = {}
        self._unit_of_measurement = None
        self._device_class = "running"
        self._unique_id = f"{DOMAIN}_{name}"
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
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._unique_id

    def update(self):
        response = self._api.get_deliveries()
        self._attributes["orders"] = response["data"].get("orders", [])
    
    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            "current_order": self._current_order,
            # 你可以在這裡添加其他你想要顯示的屬性
        }


class UberEatsDeliveriesSensor(Entity):

    def __init__(self, name, order_summary_sensor, api):
        self._name = name
        self._icon = "mdi:motorbike"
        self._state = ""
        self._state_attributes = {}
        self._unit_of_measurement = None
        self._device_class = "running"
        self._unique_id = f"{DOMAIN}_{name}"
        self._api = api
        self._order_summary_sensor = order_summary_sensor

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
        _LOGGER.debug(f"Updating {self._name} sensor")
        orders = self._order_summary_sensor.attributes.get("orders", [])
        order_index = int(self._name[-1])  # 從名稱中獲取訂單索引，訂單想超過9改self._name.split(' ')[1]
        if order_index < len(orders):
            _LOGGER.debug(f"{self._name} : {orders[order_index]}")
            order = orders[order_index]
            current_progress = order["feedCards"][0]["status"]["currentProgress"]
            self._state = ORDER_STATES.get(current_progress, f"Unknown currentProgress ({current_progress})")
            self._state_attributes["ETA"] = order["feedCards"][0]["status"]["title"]
            self._state_attributes["Order Status Description"] = order["feedCards"][0]["status"]["timelineSummary"]
            self._state_attributes["Order Status"] = order["feedCards"][0]["status"]["currentProgress"]
            self._state_attributes["Restaurant Name"] = order["activeOrderOverview"]["title"]
            self._state_attributes["Courier Name"] = order["contacts"][0]["title"]

            map_entity = order["feedCards"][1].get("mapEntity")
            if map_entity and map_entity[0]:
                self._state_attributes["Courier Location"] = f'{map_entity[0]["latitude"]},{map_entity[0]["longitude"]}'

        else:
            _LOGGER.error("Unable to log in")
