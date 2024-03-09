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

    entities = [UberEatsDeliveriesSensor(f"Order {i}", order_summary_sensor) for i in range(1, 4)]
    async_add_entities(entities, True)


class UberEatsOrderSummarySensor(Entity):

    def __init__(self, name, api):
        self._name = self._unique_id = f"{DOMAIN}_summary_{name}"
        self._icon = "mdi:shopping-search"
        self._state = 0
        self._state_attributes = {}
        self._unit_of_measurement = None
        self._device_class = "running"
        self._api = api
        self._orders = []

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return self._icon

    @property
    def unit_of_measurement(self):
        return self._unit_of_measurement

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        return self._state
    
    @property
    def orders(self):
        return self._orders

    @property
    def extra_state_attributes(self):
        return {"訂單": self._state}

    def update(self):
        response = self._api.get_deliveries()
        self._orders = response["data"].get("orders", [])
        # debug
        # from pathlib import Path

        # self._orders = eval(Path("test2.json").read_text(encoding="utf-8-sig"))[0]["data"]["orders"]
        # -end debug
        self._state = len(self._orders)


class UberEatsDeliveriesSensor(Entity):

    def __init__(self, name, order_summary_sensor):
        self._unique_id = self._name = f"{DOMAIN}_tracker_{name}"
        self._icon = "mdi:motorbike"
        self._state = "目前無訂單"
        self._state_attributes = {"msg": "目前無訂單"}
        self._unit_of_measurement = None
        self._device_class = "running"
        self._order_summary_sensor: UberEatsOrderSummarySensor = order_summary_sensor

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return self._icon

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return {k: v for k, v in self._state_attributes.items() if k != "msg"}

    @property
    def state_attributes(self):
        return self._state_attributes

    @property
    def unit_of_measurement(self):
        return self._unit_of_measurement

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def msg(self):
        return self.state_attributes["msg"]

    def update(self):
        _LOGGER.debug(f"Updating {self._name} sensor")
        order_index = int(self._name[-1]) - 1  # 從名稱中獲取訂單索引
        orders: list[dict] = self._order_summary_sensor.orders
        if order_index < self._order_summary_sensor.state:
            _LOGGER.debug(f"{self._name} : {orders[order_index]}")
            order = orders[order_index]
            self.parse_order(order)
            map_entity = order["feedCards"][1].get("mapEntity")
            if map_entity and map_entity[0]:
                self._state_attributes["Courier Location"] = f'{map_entity[0]["latitude"]},{map_entity[0]["longitude"]}'

        else:
            _LOGGER.debug("Order index out of range")

    def parse_order(self, order):
        info = order["feedCards"]
        current_progress = info[0]["status"]["currentProgress"]
        self._state = ORDER_STATES.get(current_progress, unknown_progress := f"訂單狀態不明 ({current_progress})")
        self._state_attributes["外送員名稱"] = deliver = order["contacts"][0]["title"]
        self._state_attributes["餐廳名稱"] = restaurant = order["activeOrderOverview"]["title"]
        self._state_attributes["餐點狀態"] = self._state
        self._state_attributes["訂餐時間"] = order_time = info[0]["status"]["title"]
        self._state_attributes["訂餐金額"] = money = info[5]["orderSummary"]["total"].replace(".00", "")
        self._state_attributes["額外描述"] = sub_msg = info[0]["status"]["statusSummary"]["text"]

        self.state_attributes["msg"] = f"訂單 {restaurant}，訂餐時間：{order_time}。\n"
        match current_progress:
            case 1:
                self.state_attributes["msg"] += "店家正在準備餐點。"
            case 2:
                self.state_attributes["msg"] += f"外送員 {deliver} 正前往取餐。"
            case 3:
                self.state_attributes["msg"] += f"外送員 {deliver} 正在送餐中。"
            case 4:
                self.state_attributes["msg"] += f"外送員 {deliver} 即將抵達，金額 {money}。"
            case _:
                self.state_attributes["msg"] += unknown_progress

        if (mt := "Lastest arrival by ") in sub_msg:
            self.state_attributes["msg"] += f"\n預估最晚送達時間：{sub_msg.replace(mt,'')}"
