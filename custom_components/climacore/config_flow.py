"""Config flow voor ClimaCore."""
import voluptuous as vol
import logging
from typing import Any, Dict

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigFlow, ConfigEntry, OptionsFlow
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import selector

from .const import DOMAIN, CONF_ACTIVATION_CODE
from .api import ClimaCoreApiClient, ApiAuthError, ApiConnectionError

_LOGGER = logging.getLogger(__name__)

SETPOINT_GROUPS = ["woonkamer", "badkamer", "keuken", "slaapkamer_1", "slaapkamer_2", "slaapkamer_3"]

# --- SCHEMA'S ---
def _get_general_schema(options: dict) -> vol.Schema:
    return vol.Schema({
        vol.Required("proactive_target_time", default=options.get("proactive_target_time", "06:00:00")): selector.TimeSelector(),
        vol.Required("night_start_time", default=options.get("night_start_time", "23:00:00")): selector.TimeSelector(),
        vol.Required("minutes_per_degree", default=options.get("minutes_per_degree", 30.0)): selector.NumberSelector({"min": 5.0, "max": 90.0, "step": 1.0, "mode": "slider", "unit_of_measurement": "min/°C"}),
    })

def _get_entities_schema(options: dict) -> vol.Schema:
    return vol.Schema({
        vol.Required("weather_entity", default=options.get("weather_entity")): selector.EntitySelector({"domain": "weather"}),
        vol.Optional("home_wifi_ssid", description="De naam van je Thuis Wi-Fi (SSID)", default=options.get("home_wifi_ssid", "")): selector.TextSelector(),
        vol.Optional("wifi_tracker_sensors", description="Selecteer de Wi-Fi verbinding sensoren", default=options.get("wifi_tracker_sensors", [])): selector.EntitySelector({"domain": "sensor", "multiple": True}),
        vol.Required("gasten_entity", default=options.get("gasten_entity")): selector.EntitySelector({"domain": "input_boolean"}),
        vol.Required("onderweg_entity", default=options.get("onderweg_entity")): selector.EntitySelector({"domain": "input_boolean"}),
        vol.Required("systeem_keuze_direct", default=options.get("systeem_keuze_direct", "Ambisense/MyPyllant")): selector.SelectSelector(selector.SelectSelectorConfig(options=["Ambisense/MyPyllant", "Zigbee/Lokaal"], mode=selector.SelectSelectorMode.DROPDOWN)),
    })

def _get_persons_schema(options: dict) -> vol.Schema:
    return vol.Schema({
        vol.Required("person_entities", default=options.get("person_entities", [])): selector.EntitySelector({"domain": "person", "multiple": True}),
    })

def _get_fallback_schema(options: dict) -> vol.Schema:
    return vol.Schema({
        vol.Required("fallback_temp", default=options.get("fallback_temp", 18.0)): selector.NumberSelector({"min": 10.0, "max": 25.0, "step": 0.5, "mode": "slider", "unit_of_measurement": "°C"}),
    })

def _get_zone_schema_generic(zone_data: dict, zone_slot_key: str) -> vol.Schema:
    return vol.Schema({
        vol.Optional("zone_name", default=zone_data.get("zone_name", "")): selector.TextSelector(),
        vol.Optional("climate_entities", default=zone_data.get("climate_entities", [])): selector.EntitySelector(selector.EntitySelectorConfig(domain="climate", multiple=True)),
        vol.Required("day_start", default=zone_data.get("day_start", "06:00:00")): selector.TimeSelector(),
        vol.Required("night_start", default=zone_data.get("night_start", "22:00:00")): selector.TimeSelector(),
        vol.Optional("window_sensors", default=zone_data.get("window_sensors", [])): selector.EntitySelector(selector.EntitySelectorConfig(domain="binary_sensor", multiple=True)),
        vol.Required("lookup_prefix", default=zone_data.get("lookup_prefix", "woonkamer")): selector.SelectSelector(selector.SelectSelectorConfig(options=SETPOINT_GROUPS, mode=selector.SelectSelectorMode.DROPDOWN)),
    })

def _get_setpoints_schema(options: dict, prefix: str) -> vol.Schema:
    defaults_living = {"afwezig": 15.0, "voorverwarming": 20.0, "dag_fris": 21.0, "dag_koud": 21.5, "dag_mild_warm": 20.5, "nacht_fris": 17.0, "nacht_koud": 17.0, "nacht_mild_warm": 17.0}
    defaults_bathroom = {"afwezig": 15.0, "voorverwarming": 22.0, "dag_fris": 23.0, "dag_koud": 23.5, "dag_mild_warm": 22.5, "nacht_fris": 18.0, "nacht_koud": 18.0, "nacht_mild_warm": 18.0}
    defaults_bedroom = {"afwezig": 15.0, "voorverwarming": 17.0, "dag_fris": 18.0, "dag_koud": 18.5, "dag_mild_warm": 17.5, "nacht_fris": 16.0, "nacht_koud": 16.0, "nacht_mild_warm": 16.0}

    if "badkamer" in prefix: current_defaults = defaults_bathroom
    elif "slaapkamer" in prefix: current_defaults = defaults_bedroom
    else: current_defaults = defaults_living

    scenarios = ["afwezig", "voorverwarming", "dag_fris", "dag_koud", "dag_mild_warm", "nacht_fris", "nacht_koud", "nacht_mild_warm"]
    schema_dict = {}
    for scenario in scenarios:
        key = f"temp_{prefix}_{scenario}"
        default_val = options.get(key, current_defaults[scenario])
        schema_dict[vol.Required(key, default=default_val)] = selector.NumberSelector({"min": 10.0, "max": 25.0, "step": 0.5, "mode": "slider", "unit_of_measurement": "°C"})
    return vol.Schema(schema_dict)

# --- INSTALLATIE FLOW ---
STEP_USER_DATA_SCHEMA = vol.Schema({vol.Required(CONF_ACTIVATION_CODE): str})

async def validate_input(hass: HomeAssistant, data: dict) -> dict:
    api_client = ClimaCoreApiClient(data[CONF_ACTIVATION_CODE])
    try:
        validation_status = await hass.async_add_executor_job(api_client.validate_activation_code)
    except Exception as e:
        _LOGGER.error(f"Onbekende validatiefout: {e}")
        raise InvalidAuth("unknown")
    
    if validation_status == "valid": return {"title": "ClimaCore"}
    elif validation_status == "invalid_auth": raise InvalidAuth("invalid_auth")
    elif validation_status == "cannot_connect": raise ApiConnectionError("cannot_connect")
    else: raise Exception(f"Validatie mislukt: {validation_status}")

class ClimaCoreConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1
    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return ClimaCoreOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)
            except InvalidAuth: errors["base"] = "invalid_auth"
            except ApiConnectionError: errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Onverwachte fout in config flow")
                errors["base"] = "unknown"
        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors)

class ClimaCoreOptionsFlow(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry):
        self.options: Dict[str, Any] = {}
        self.current_zone_slot: str = "" 

    async def async_step_init(self, user_input: Dict[str, Any] = None):
        # ALTIJD verversen vanaf de source-of-truth
        self.options = dict(self.config_entry.options)
        return self.async_show_menu(step_id="init", menu_options={
            "general": "Stap 1: Algemene Instellingen", "entities": "Stap 2: Hoofd-Entiteiten",
            "persons": "Stap 3: Personen", "zone_config": "Stap 4: Zone Configuratie",
            "fallback": "Stap 7: Noodloop (Fallback)", "setpoints": "Stap 8: Setpoint Groepen"
        })

    async def async_step_general(self, user_input=None): return await self._async_show_form_step(user_input, "general", _get_general_schema, False)
    async def async_step_entities(self, user_input=None): return await self._async_show_form_step(user_input, "entities", _get_entities_schema, False)
    async def async_step_persons(self, user_input=None): return await self._async_show_form_step(user_input, "persons", _get_persons_schema, False)
    async def async_step_fallback(self, user_input=None): return await self._async_show_form_step(user_input, "fallback", _get_fallback_schema, False)
    
    async def async_step_zone_config(self, user_input: Dict[str, Any] = None):
        # ALTIJD verversen om zeker te zijn dat we de nieuwste zone-namen zien
        self.options = dict(self.config_entry.options)
        opts = {f"zone_{i}": f"Zone {i}: {self.options.get(f'zone_{i}', {}).get('zone_name', '')}" or f"Zone {i}" for i in range(1, 11)}
        return self.async_show_menu(step_id="zone_config", menu_options=opts)

    async def async_step_zone_1(self, user_input=None): self.current_zone_slot="zone_1"; return await self._async_show_form_step(user_input, "zone_1", _get_zone_schema_generic, True, "zone_1")
    async def async_step_zone_2(self, user_input=None): self.current_zone_slot="zone_2"; return await self._async_show_form_step(user_input, "zone_2", _get_zone_schema_generic, True, "zone_2")
    async def async_step_zone_3(self, user_input=None): self.current_zone_slot="zone_3"; return await self._async_show_form_step(user_input, "zone_3", _get_zone_schema_generic, True, "zone_3")
    async def async_step_zone_4(self, user_input=None): self.current_zone_slot="zone_4"; return await self._async_show_form_step(user_input, "zone_4", _get_zone_schema_generic, True, "zone_4")
    async def async_step_zone_5(self, user_input=None): self.current_zone_slot="zone_5"; return await self._async_show_form_step(user_input, "zone_5", _get_zone_schema_generic, True, "zone_5")
    async def async_step_zone_6(self, user_input=None): self.current_zone_slot="zone_6"; return await self._async_show_form_step(user_input, "zone_6", _get_zone_schema_generic, True, "zone_6")
    async def async_step_zone_7(self, user_input=None): self.current_zone_slot="zone_7"; return await self._async_show_form_step(user_input, "zone_7", _get_zone_schema_generic, True, "zone_7")
    async def async_step_zone_8(self, user_input=None): self.current_zone_slot="zone_8"; return await self._async_show_form_step(user_input, "zone_8", _get_zone_schema_generic, True, "zone_8")
    async def async_step_zone_9(self, user_input=None): self.current_zone_slot="zone_9"; return await self._async_show_form_step(user_input, "zone_9", _get_zone_schema_generic, True, "zone_9")
    async def async_step_zone_10(self, user_input=None): self.current_zone_slot="zone_10"; return await self._async_show_form_step(user_input, "zone_10", _get_zone_schema_generic, True, "zone_10")

    async def async_step_setpoints(self, user_input=None):
        # ALTIJD verversen
        self.options = dict(self.config_entry.options)
        return self.async_show_menu(step_id="setpoints", menu_options={"sp_woonkamer": "Woonkamer", "sp_badkamer": "Badkamer", "sp_keuken": "Keuken", "sp_sk1": "Slaapkamer 1", "sp_sk2": "Slaapkamer 2", "sp_sk3": "Slaapkamer 3"})

    async def async_step_sp_woonkamer(self, user_input=None): return await self._async_show_form_step(user_input, "sp_woonkamer", _get_setpoints_schema, False, "woonkamer")
    async def async_step_sp_badkamer(self, user_input=None): return await self._async_show_form_step(user_input, "sp_badkamer", _get_setpoints_schema, False, "badkamer")
    async def async_step_sp_keuken(self, user_input=None): return await self._async_show_form_step(user_input, "sp_keuken", _get_setpoints_schema, False, "keuken")
    async def async_step_sp_sk1(self, user_input=None): return await self._async_show_form_step(user_input, "sp_sk1", _get_setpoints_schema, False, "slaapkamer_1")
    async def async_step_sp_sk2(self, user_input=None): return await self._async_show_form_step(user_input, "sp_sk2", _get_setpoints_schema, False, "slaapkamer_2")
    async def async_step_sp_sk3(self, user_input=None): return await self._async_show_form_step(user_input, "sp_sk3", _get_setpoints_schema, False, "slaapkamer_3")

    async def _async_show_form_step(self, user_input, step_id, schema_fn, is_zone, schema_arg=None):
        errors = {}
        if user_input is not None:
            try:
                if is_zone: self.options[self.current_zone_slot] = user_input
                else: self.options.update(user_input)
                
                # Forceer een directe save naar disk
                self.hass.config_entries.async_update_entry(self.config_entry, options=self.options)
                
                if step_id.startswith("zone_"): return await self.async_step_zone_config()
                elif step_id.startswith("sp_"): return await self.async_step_setpoints()
                return await self.async_step_init()
            except Exception as e:
                _LOGGER.error(f"Fout in options flow stap {step_id}: {e}")
                errors["base"] = "unknown"
        
        # Laad de data opnieuw voor de weergave (dubbele zekerheid)
        current_data = self.options
        if is_zone: current_data = self.options.get(self.current_zone_slot, {})
        schema = schema_fn(current_data, schema_arg) if schema_arg else schema_fn(current_data)
        return self.async_show_form(step_id=step_id, data_schema=schema, errors=errors)

class InvalidAuth(HomeAssistantError):
    def __init__(self, error_key: str): super().__init__(); self.error_key = error_key
    def __str__(self) -> str: return self.error_key
