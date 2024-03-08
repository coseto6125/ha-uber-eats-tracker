import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN


class UberEatsOptionsFlow(config_entries.OptionsFlow):

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="修改 sid", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional("sid_token", default=""): str,
                }
            ),
        )


class UberEatsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Uber Eats."""

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required("sid_token"): str,
                    }
                ),
            )

        errors = {}

        def _validate_sid_token(sid_token):
            """Validate the sid_token."""
            return sid_token.startswith("QA.") and len(sid_token) > 150

        if not _validate_sid_token(user_input["sid_token"]):
            errors["sid_token"] = "invalid_sid_token"
        if errors:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required("sid_token"): str,
                    }
                ),
                errors=errors,
            )

        return self.async_create_entry(title="UberEats", data=user_input)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> UberEatsOptionsFlow:
        """Get the options flow for this handler."""
        return UberEatsOptionsFlow(config_entry)
