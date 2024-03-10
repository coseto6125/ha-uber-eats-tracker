import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN


class UberEatsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Uber Eats."""

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="UberEats Tracker", data={})

        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ):
        """Get the options flow for this handler."""
        return UberEatsOptionsFlow(config_entry)


class UberEatsOptionsFlow(config_entries.OptionsFlow):

    def __init__(self, config_entry: config_entries.ConfigEntry):
        self.config_entry = config_entry

    def _validate_sid_token(self, sid_token):
        """Validate the sid_token."""
        return sid_token.startswith("QA.") and len(sid_token) > 150

    async def async_step_init(self, user_input=None):
        errors = {}
        sid_token = self.config_entry.options.get("sid_token", "")
        if user_input is not None:
            if sid_token := user_input.get("sid_token"):
                if self._validate_sid_token(sid_token) is False:
                    errors = {"sid_token": "invalid_sid_token"}
                if not errors:
                    return self.async_create_entry(title="Uber Eats Tracker", data=user_input)
        schema = {
            vol.Required(
                "sid_token",
                description={"suggested_value": sid_token},
            ): str,
        }
        return self.async_show_form(step_id="init", errors=errors, data_schema=vol.Schema(schema))
