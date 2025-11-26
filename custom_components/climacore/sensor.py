"""Sensor platform voor ClimaCore."""
import logging
from homeassistant.core import callback
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# De prefix voor de assets, zoals geregistreerd in __init__.py
ASSET_URL_PREFIX = f"/{DOMAIN}_assets"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Zet de ClimaCore sensoren op."""
    
    # Maak beide sensoren aan en voeg ze toe
    scenario_sensor = ClimaCoreScenarioSensor(hass, entry)
    background_sensor = ClimaCoreBackgroundSensor(hass, entry, scenario_sensor)
    
    async_add_entities([scenario_sensor, background_sensor])


class ClimaCoreScenarioSensor(SensorEntity):
    """De sensor die het huidige ClimaCore scenario bijhoudt."""

    _attr_icon = "mdi:theme-light-dark"
    _attr_should_poll = False
    _attr_translation_key = "current_scenario" # Gebruikt strings.json

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        """Initialiseer de sensor."""
        self.hass = hass
        self._attr_unique_id = f"{entry.entry_id}_current_scenario"
        
        # De apparaat-info wordt gedeeld door alle entiteiten
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "ClimaCore",
            "manufacturer": "Home Optimizer",
            "model": "ClimaCore v1.5" # Versie bijgewerkt
        }
        self._attr_native_value = "Onbekend" # Begin-staat

    @callback
    def _async_handle_event(self, event):
        """Handel de scenario update event af."""
        new_scenario = event.data.get("scenario")
        if new_scenario:
            self._attr_native_value = new_scenario
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Wordt aangeroepen wanneer de sensor aan HA wordt toegevoegd."""
        await super().async_added_to_hass()
        # Luister naar de custom event die de __init__.py zal afvuren
        self.async_on_remove(
            self.hass.bus.async_listen(
                "climacore_scenario_update", self._async_handle_event
            )
        )

# --- NIEUWE SENSOR ---

class ClimaCoreBackgroundSensor(SensorEntity):
    """Genereert de URL voor de dynamische achtergrondafbeelding."""

    _attr_icon = "mdi:image"
    _attr_should_poll = False
    _attr_name = "ClimaCore Background URL" # Vaste naam

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, scenario_sensor: ClimaCoreScenarioSensor):
        """Initialiseer de achtergrond sensor."""
        self.hass = hass
        self._attr_unique_id = f"{entry.entry_id}_background_url"
        
        # Koppel aan hetzelfde ClimaCore "Apparaat"
        self._attr_device_info = scenario_sensor.device_info
        
        # Begin-staat (kan ook een 'default.jpg' zijn als je die hebt)
        self._attr_native_value = f"{ASSET_URL_PREFIX}/afwezig.jpg" 

    def _format_scenario_to_filename(self, scenario_name: str) -> str:
        """Converteert 'Scenario Titel' naar 'scenario-titel.jpg'."""
        if not scenario_name or scenario_name == "Onbekend":
            return "afwezig.jpg" # Fallback
            
        filename = scenario_name.replace(" - ", "-").replace(" ", "-").lower()
        return f"{filename}.jpg"

    @callback
    def _async_handle_event(self, event):
        """Handel de scenario update event af."""
        new_scenario = event.data.get("scenario")
        if new_scenario:
            filename = self._format_scenario_to_filename(new_scenario)
            self._attr_native_value = f"{ASSET_URL_PREFIX}/{filename}"
            self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Wordt aangeroepen wanneer de sensor aan HA wordt toegevoegd."""
        await super().async_added_to_hass()
        # Luister ook naar dezelfde event
        self.async_on_remove(
            self.hass.bus.async_listen(
                "climacore_scenario_update", self._async_handle_event
            )
        )
