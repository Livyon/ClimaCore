"""De ClimaCore Integratie."""
import logging
import asyncio
import os
from typing import Any
from datetime import time

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    Platform, ATTR_ENTITY_ID, STATE_UNAVAILABLE, STATE_UNKNOWN
)
from homeassistant.components.http import StaticPathConfig
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
    async_track_time_interval, 
)
from homeassistant.helpers.entity_registry import (
    async_get as async_get_entity_registry,
    EntityRegistry,
)
import homeassistant.util.dt as dt_util

from .const import DOMAIN, CONF_ACTIVATION_CODE
from .api import ClimaCoreApiClient, ApiAuthError, ApiConnectionError, ApiTimeoutError

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]

async def async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Wordt aangeroepen wanneer de opties worden bijgewerkt."""
    _LOGGER.debug(f"ClimaCore opties bijgewerkt, herlaad listeners...")
    coordinator: ClimaCoreCoordinator = hass.data[DOMAIN].get(entry.entry_id)
    if coordinator:
        await coordinator.update_options(entry.options)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Zet ClimaCore op vanuit een config entry."""
    
    _LOGGER.info(f"ClimaCore v1.5.0 (schone setup) aan het opzetten...")
    
    api_client = ClimaCoreApiClient(entry.data.get(CONF_ACTIVATION_CODE))
    coordinator = ClimaCoreCoordinator(hass, entry, api_client)
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    entry.add_update_listener(async_options_updated)
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    static_path = os.path.join(hass.config.path(f"custom_components/{DOMAIN}/www"))
    await hass.http.async_register_static_paths([
        StaticPathConfig(f"/{DOMAIN}_assets", static_path, cache_headers=False)
    ])
    _LOGGER.info(f"Assets geregistreerd op URL: /{DOMAIN}_assets")
    
    await coordinator.setup_listeners()

    _LOGGER.info("ClimaCore succesvol ingesteld en listeners gestart.")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Verwijder een ClimaCore config entry."""
    _LOGGER.debug("ClimaCore aan het verwijderen...")
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    coordinator: ClimaCoreCoordinator = hass.data[DOMAIN].get(entry.entry_id)
    if coordinator:
        coordinator.cleanup_listeners()
    
    if unload_ok:
        _LOGGER.debug("ClimaCore static path aan het unregisteren...")
        await hass.http.async_unregister_static_paths(f"/{DOMAIN}_assets")
        
        if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
            hass.data[DOMAIN].pop(entry.entry_id)

    _LOGGER.debug("ClimaCore succesvol verwijderd.")
    return unload_ok


class ClimaCoreCoordinator:
    """De "Motor" van ClimaCore."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api_client: ClimaCoreApiClient):
        self.hass = hass
        self.entry = entry
        self.api_client = api_client
        self.options = entry.options
        self._listeners = []
        self._entity_registry: EntityRegistry | None = None
        self._is_running = False
        self._boost_window = None 

    @callback
    def cleanup_listeners(self) -> None:
        _LOGGER.debug(f"Opschonen van {len(self._listeners)} listeners...")
        for remove_listener in self._listeners:
            remove_listener()
        self._listeners = []

    async def update_options(self, new_options: dict) -> None:
        self.options = new_options
        self.cleanup_listeners()
        await self.setup_listeners()

    async def setup_listeners(self) -> None:
        _LOGGER.debug("Registreren van ClimaCore triggers...")
        self._entity_registry = async_get_entity_registry(self.hass)
        
        main_triggers = []
        
        if person_entities := self.options.get("person_entities"):
            main_triggers.extend(person_entities)
        if weather_entity := self.options.get("weather_entity"):
            main_triggers.append(weather_entity)
        if gasten_entity := self.options.get("gasten_entity"):
            main_triggers.append(gasten_entity)
        if onderweg_entity := self.options.get("onderweg_entity"):
            main_triggers.append(onderweg_entity)
            
        # --- NIEUW: TAGS & WIFI ---
        if presence_sensors := self.options.get("presence_sensors"):
            main_triggers.extend(presence_sensors)
        if wifi_sensors := self.options.get("wifi_tracker_sensors"):
            main_triggers.extend(wifi_sensors)
        # --------------------------

        if main_triggers:
            _LOGGER.debug(f"Listener voor Hoofdtriggers: {main_triggers}")
            self._listeners.append(
                async_track_state_change_event(
                    self.hass, main_triggers, self.async_trigger_main_logic
                )
            )

        window_sensors = []
        for i in range(1, 11):
            zone_data = self.options.get(f"zone_{i}", {})
            if sensors := zone_data.get("window_sensors"):
                window_sensors.extend(sensors)
        
        if window_sensors:
            _LOGGER.debug(f"Listener voor Raamsensoren: {window_sensors}")
            self._listeners.append(
                async_track_state_change_event(
                    self.hass, window_sensors, self.async_trigger_main_logic
                )
            )

        # TIJD TRIGGERS
        self._listeners.append(async_track_time_change(self.hass, self.async_trigger_main_logic, hour=23, minute=0, second=0))
        self._listeners.append(async_track_time_change(self.hass, self.async_trigger_main_logic, hour=4, minute=59, second=59))
        self._listeners.append(async_track_time_change(self.hass, self.async_trigger_proactive_start, hour=4, minute=0, second=0))
        
        # HEARTBEAT
        self._listeners.append(async_track_time_interval(self.hass, self.async_trigger_main_logic, dt_util.dt.timedelta(minutes=10)))
        
        _LOGGER.debug("Alle listeners zijn geregistreerd.")

    def _get_state(self, entity_id: str) -> str | None:
        state = self.hass.states.get(entity_id)
        if state and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return state.state
        return None

    def _get_state_attr(self, entity_id: str, attr: str, default: Any = None) -> Any:
        if not entity_id: return default
        state = self.hass.states.get(entity_id)
        if state:
            value = state.attributes.get(attr)
            return value if value is not None else default
        return default

    def _build_main_logic_payload(self, trigger_entity_id: str | None = None) -> dict:
        config_data = {key: value for key, value in self.options.items() if key.startswith("temp_")}
        config_data["fallback_temp"] = self.options.get("fallback_temp", 18.0)

        # BOOST LOGICA
        nu = dt_util.now()
        simulated_time_str = nu.strftime('%H:%M:%S')
        
        if self._boost_window:
            if self._boost_window["start"] <= nu < self._boost_window["end"]:
                simulated_time_str = self._boost_window["end"].strftime('%H:%M:%S')
                _LOGGER.info(f"BOOST ACTIEF: A.I. berekende voorverwarming. Ik simuleer tijdstip {simulated_time_str}.")
            elif nu >= self._boost_window["end"]:
                self._boost_window = None
        
        context_data = {
            "current_time": simulated_time_str,
            "trigger_entity_id": trigger_entity_id 
        }

        weather_entity = self.options.get("weather_entity")
        try: temp = float(self._get_state_attr(weather_entity, "temperature", 15.0))
        except (ValueError, TypeError): temp = 15.0
        try: hum = float(self._get_state_attr(weather_entity, "humidity", 50))
        except (ValueError, TypeError): hum = 50.0

        sensors_data = {
            "outdoor_temp": temp, "outdoor_humidity": hum,
            "gasten_aanwezig": self._get_state(self.options.get("gasten_entity")) or "off",
            "onderweg_naar_huis": self._get_state(self.options.get("onderweg_entity")) or "off",
            "systeem_keuze": self.options.get("systeem_keuze_direct", "Ambisense/MyPyllant")
        }

        # --- WI-FI & TAG DOMINANTIE LOGICA ---
        persons_data = {}
        person_entities = self.options.get("person_entities", [])
        
        # 1. Check Tag/Sensor Aanwezigheid (Nieuw)
        tags = self.options.get("presence_sensors", [])
        is_tag_home = False
        for tag in tags:
            state = self._get_state(tag)
            # Accepteer 'home' (trackers) en 'on' (binary sensors/knoppen)
            if state in ["home", "on", "active"]:
                is_tag_home = True
                break

        # 2. Check Wi-Fi
        target_ssid = self.options.get("home_wifi_ssid")
        wifi_sensors = self.options.get("wifi_tracker_sensors", [])
        is_wifi_connected = False
        if target_ssid and wifi_sensors:
            for sensor in wifi_sensors:
                wifi_state = self._get_state(sensor)
                if wifi_state and target_ssid in wifi_state:
                    is_wifi_connected = True
                    break
        
        for entity_id in person_entities:
            gps_state = self._get_state(entity_id)
            # Als Wi-Fi OF Tag aanwezig is -> Iedereen is "Thuis"
            if is_wifi_connected or is_tag_home:
                persons_data[entity_id] = "home"
            elif gps_state == "home":
                persons_data[entity_id] = "home"
            else:
                persons_data[entity_id] = "not_home"
        # ------------------------------------------------

        climate_zones_data = {}
        for i in range(1, 11): 
            zone_key = f"zone_{i}"
            zone_config = self.options.get(zone_key)
            
            if not zone_config or not zone_config.get("climate_entities"): 
                continue
            
            zone_name = zone_config.get("zone_name", f"Zone {i}")
            if not zone_name: zone_name = f"Zone {i}"
            
            window_states = []
            for sensor_id in zone_config.get("window_sensors", []):
                state = self._get_state(sensor_id)
                if state: window_states.append(state)
            
            day_start = zone_config.get("day_start", "06:00:00")
            night_start = zone_config.get("night_start", "22:00:00")

            climate_zones_data[zone_name] = {
                "climate_entity": zone_config["climate_entities"][0],
                "lookup_prefix": zone_config.get("lookup_prefix", "woonkamer"),
                "window_sensors": window_states,
                "_all_climate_entities": zone_config["climate_entities"],
                "schedule": {
                    "start": day_start,
                    "end": night_start
                }
            }

        return {
            "config": config_data, "context": context_data,
            "sensors": sensors_data, "persons": persons_data,
            "climate_zones": climate_zones_data
        }

    async def _execute_actions(self, actions: list, climate_zones_payload: dict):
        _LOGGER.debug(f"Uitvoeren van {len(actions)} acties ontvangen van ClimaCore API...")
        
        for action in actions:
            try:
                service = action.get("service")
                entity_name = action.get("entity") 
                data = action.get("data", {})
                
                if not service: continue

                if service == "delay":
                    delay_seconds = data.get("seconds", 1)
                    _LOGGER.debug(f"Actie: Wacht {delay_seconds} seconden...")
                    await asyncio.sleep(delay_seconds)
                    continue

                if service.startswith("persistent_notification"):
                    await self.hass.services.async_call("persistent_notification", service.split('.')[1], data)
                    continue

                if not entity_name: continue

                zone_data = climate_zones_payload.get(entity_name)
                if not zone_data:
                    _LOGGER.warning(f"Actie overgeslagen: Zone '{entity_name}' niet gevonden.")
                    continue

                target_entities = zone_data.get("_all_climate_entities", [])
                if not target_entities: continue
                
                _LOGGER.debug(f"Actie: Roep service {service} aan voor {entity_name} | Data: {data}")
                domain, service_name = service.split('.')
                
                await self.hass.services.async_call(
                    domain, service_name, 
                    {"entity_id": target_entities, **data},
                    blocking=True 
                )
            
            except Exception as e:
                _LOGGER.error(f"FOUT tijdens uitvoeren actie voor {entity_name}: {e}. We gaan door...")
                continue

    @callback
    async def async_trigger_main_logic(self, *args):
        _LOGGER.debug(f"ClimaCore Hoofdlogica getriggerd door: {args}")
        
        trigger_entity_id = None
        event = None
        old_state_obj = None
        new_state_obj = None

        if args:
            try:
                if len(args) > 0 and hasattr(args[0], "data"):
                    event = args[0]
                    trigger_entity_id = event.data.get("entity_id")
                    old_state_obj = event.data.get("old_state")
                    new_state_obj = event.data.get("new_state")
            except Exception:
                _LOGGER.debug("Kon trigger details niet parsen (waarschijnlijk tijd-trigger).")

        if trigger_entity_id and trigger_entity_id.startswith("person."):
            if old_state_obj and new_state_obj and old_state_obj.state == new_state_obj.state:
                _LOGGER.debug(f"Persoon trigger {trigger_entity_id} genegeerd: Alleen GPS/Nauwkeurigheid veranderd.")
                return

        is_window_trigger = False
        if trigger_entity_id:
            for i in range(1, 11):
                zone_data = self.options.get(f"zone_{i}", {})
                if trigger_entity_id in zone_data.get("window_sensors", []):
                    is_window_trigger = True
                    break
        
        if is_window_trigger:
            to_state = new_state_obj.state if new_state_obj else "unknown"
            _LOGGER.debug(f"Raamsensor {trigger_entity_id} ging naar '{to_state}'. Wacht 15s debounce...")
            await asyncio.sleep(15)
            
            current_state = self._get_state(trigger_entity_id)
            if to_state == "on" and current_state == "off":
                _LOGGER.info(f"Debounce: Raam {trigger_entity_id} was even open, maar nu weer dicht. Genegeerd.")
                return
            if to_state == "off" and current_state == "on":
                _LOGGER.info(f"Debounce: Raam {trigger_entity_id} was even dicht, maar nu weer open. Genegeerd.")
                return
            _LOGGER.debug(f"Raam {trigger_entity_id} status bevestigd als '{current_state}'. Doorgaan met API-call.")

        if self._is_running:
            _LOGGER.warning("Trigger overgeslagen: ClimaCore is al bezig (anti-loop).")
            return
        self._is_running = True
        
        try:
            payload = self._build_main_logic_payload(trigger_entity_id=trigger_entity_id)
            
            response = await self.hass.async_add_executor_job(
                self.api_client.trigger_main_logic, payload
            )
            
            if response and (actions := response.get("actions")):
                await self._execute_actions(actions, payload.get("climate_zones", {}))
            
            scenario = response.get('scenario')
            _LOGGER.info(f"ClimaCore logica succesvol uitgevoerd. Actief scenario: {scenario}")

            if scenario:
                self.hass.bus.async_fire("climacore_scenario_update", {"scenario": scenario})

        except (ApiAuthError, ApiConnectionError, ApiTimeoutError) as e:
            _LOGGER.error(f"Fout tijdens aanroepen ClimaCore API: {e}")
        except Exception as e:
            _LOGGER.exception(f"Onverwachte fout in ClimaCore hoofdlogica: {e}")
        finally:
            self._is_running = False

    @callback
    async def async_trigger_proactive_start(self, *args):
        _LOGGER.info("Proactieve Start Calculator trigger (04:00)...")
        
        weather_entity = self.options.get("weather_entity")
        woonkamer_climate_entity = None
        for i in range(1, 11):
            zone_cfg = self.options.get(f"zone_{i}", {})
            if zone_cfg.get("lookup_prefix") == "woonkamer":
                if climate_entities := zone_cfg.get("climate_entities"):
                    woonkamer_climate_entity = climate_entities[0]
                    break
        
        if not woonkamer_climate_entity:
            _LOGGER.error("Proactieve start geannuleerd: Geen climate entiteit gevonden met 'woonkamer' setpoint groep.")
            return

        try: temp = float(self._get_state_attr(weather_entity, "temperature", 15.0))
        except (ValueError, TypeError): temp = 15.0
        try: hum = float(self._get_state_attr(weather_entity, "humidity", 50))
        except (ValueError, TypeError): hum = 50.0
        try: current_temp = float(self._get_state_attr(woonkamer_climate_entity, "current_temperature", 18.0))
        except (ValueError, TypeError): current_temp = 18.0

        sensors_payload = {"outdoor_temp": temp, "outdoor_humidity": hum, "current_indoor_temp": current_temp}
        config_payload = {
            "proactive_target_time": self.options.get("proactive_target_time", "06:00:00"),
            "minutes_per_degree": self.options.get("minutes_per_degree", 30),
            "temp_woonkamer_dag_fris": self.options.get("temp_woonkamer_dag_fris", 20.5),
            "temp_woonkamer_dag_koud": self.options.get("temp_woonkamer_dag_koud", 21.0),
            "temp_woonkamer_dag_mild_warm": self.options.get("temp_woonkamer_dag_mild_warm", 20.0),
        }
        payload = {"sensors": sensors_payload, "config": config_payload}
        
        try:
            response = await self.hass.async_add_executor_job(
                self.api_client.trigger_proactive_start, payload
            )
            
            start_tijd_str = response.get("calculated_start_time")
            if not start_tijd_str:
                _LOGGER.error(f"Proactieve start API gaf geen starttijd terug. Info: {response.get('info')}")
                return
            
            _LOGGER.info(f"Proactieve start API berekend: start om {start_tijd_str}. Info: {response.get('info')}")
            
            start_tijd = time.fromisoformat(start_tijd_str)
            vandaag = dt_util.now().date()
            start_datetime = dt_util.as_local(dt_util.dt.datetime.combine(vandaag, start_tijd))

            if start_datetime < dt_util.now():
                _LOGGER.warning(f"Berekende starttijd {start_tijd_str} ligt in het verleden. Wordt overgeslagen.")
                return

            _LOGGER.info(f"Dynamische trigger ingesteld om hoofdlogica te starten om {start_datetime.isoformat()}")

            target_str = self.options.get("proactive_target_time", "06:00:00")
            target_time = time.fromisoformat(target_str)
            target_datetime = dt_util.as_local(dt_util.dt.datetime.combine(vandaag, target_time))
            
            self._boost_window = {
                "start": start_datetime,
                "end": target_datetime
            }
            
            async_track_time_change(
                self.hass, self.async_trigger_main_logic, 
                hour=start_datetime.hour, 
                minute=start_datetime.minute, 
                second=start_datetime.second
            )
        except (ApiAuthError, ApiConnectionError, ApiTimeoutError) as e:
            _LOGGER.error(f"Fout tijdens aanroepen Proactieve Start API: {e}")
        except Exception as e:
            _LOGGER.exception(f"Onverwachte fout in Proactieve Start logica: {e}")
