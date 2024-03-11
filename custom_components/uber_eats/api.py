import logging
from time import sleep

from requests import post

_LOGGER = logging.getLogger(__name__)


class UberEatsApi:

    def __init__(self, token):
        self._sid = token
        self._locale_code = "TW"
        self._timezone = "Asia/Taipei"
        self._url_base = f"https://www.ubereats.com/api/getActiveOrdersV1?localeCode={self._locale_code}"

    def get_deliveries(self):
        headers = {"Content-Type": "application/json", "X-CSRF-Token": "x", "Cookie": f"sid={self._sid}"}

        data = {"orderUuid": None, "timezone": self._timezone, "showAppUpsellIllustration": True}
        response = post(self._url_base, headers=headers, json=data)
        data = {"data": "Failed to fetch deliveries."}
        if response.status_code == 200:
            data = response.json()
            if not data:
                _LOGGER.warning("Fetched deliveries successfully, but did not find any")
            return data
        _LOGGER.warning(f"Failed to fetch deliveries: {response.status_code}\n{response.text}")
        sleep(3)
        return self.get_deliveries()

    def check_auth(self):
        """Check to see if our SID is valid."""
        if self._sid:
            _LOGGER.debug("Login is Acceptable.")
            return True
        return False
