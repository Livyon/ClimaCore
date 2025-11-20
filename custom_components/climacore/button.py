"""Button platform voor ClimaCore."""
import logging
import os
import shutil

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.network import get_url

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# --- Thema Constanten ---
THEME_DESTINATION_FILENAME = "climacore.yaml"
THEME_SOURCE_FILENAME = "climacore_theme.yaml"
THEME_SOURCE_SUBDIR = "themes"

# --- Dashboard Constanten ---
DASHBOARD_TEMPLATE_FILENAME = "dashboard_template.yaml"
DASHBOARD_SOURCE_SUBDIR = "assets"
DASHBOARD_DESTINATION_DIR = os.path.join("custom_components", DOMAIN, "www")
DASHBOARD_PUBLIC_FILENAME = "climacore-dashboard-template.yaml"

# --- Preheat Blueprint Constanten ---
PREHEAT_BLUEPRINT_TEMPLATE_FILENAME = "blueprint-preheat.yaml"
PREHEAT_BLUEPRINT_SOURCE_SUBDIR = "assets"
PREHEAT_BLUEPRINT_DESTINATION_DIR = "blueprints/automation/climacore" # Pad: /config/blueprints/automation/climacore/
PREHEAT_BLUEPRINT_DESTINATION_FILENAME = "smart_preheat.yaml"

# --- Gmaps Blueprint Constanten ---
GMAPS_BLUEPRINT_TEMPLATE_FILENAME = "blueprint-gmaps-manager.yaml"
GMAPS_BLUEPRINT_SOURCE_SUBDIR = "assets"
GMAPS_BLUEPRINT_DESTINATION_DIR = "blueprints/automation/climacore" # Zelfde map
GMAPS_BLUEPRINT_DESTINATION_FILENAME = "gmaps_manager.yaml"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Zet de ClimaCore knoppen op."""
    
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="ClimaCore",
        manufacturer="Home Optimizer",
        model="ClimaCore v1.5"
    )
    
    # Maak alle vier de knoppen aan
    theme_button = ClimaCoreInstallThemeButton(hass, entry, device_info)
    dashboard_button = ClimaCoreInstallDashboardButton(hass, entry, device_info)
    preheat_blueprint_button = ClimaCoreInstallBlueprintButton(hass, entry, device_info, "preheat")
    gmaps_blueprint_button = ClimaCoreInstallBlueprintButton(hass, entry, device_info, "gmaps")
    
    async_add_entities([theme_button, dashboard_button, preheat_blueprint_button, gmaps_blueprint_button])


def _copy_file_to_config(
    hass: HomeAssistant, 
    source_subdir: str, 
    source_filename: str, 
    dest_dir: str, 
    dest_filename: str
) -> tuple[bool, str]:
    """
    Helper-functie om een bestand van de integratiemap naar een config-map te kopiëren.
    """
    try:
        config_dir = hass.config.path()
        
        source_path = os.path.join(
            config_dir, "custom_components", DOMAIN, source_subdir, source_filename
        )
        destination_dir_path = os.path.join(config_dir, dest_dir)
        destination_file_path = os.path.join(destination_dir_path, dest_filename)

        if not os.path.exists(source_path):
            _LOGGER.error(f"Bronbestand niet gevonden: {source_path}")
            return (False, f"Kon het bronbestand niet vinden: {source_filename}")

        os.makedirs(destination_dir_path, exist_ok=True)
        shutil.copy2(source_path, destination_file_path)
        
        _LOGGER.info(f"Bestand succesvol geïnstalleerd naar: {destination_file_path}")
        return (True, f"Bestand succesvol geïnstalleerd als '{dest_dir}/{dest_filename}'.")

    except Exception as e:
        _LOGGER.error(f"Fout bij kopiëren bestand: {e}")
        return (False, f"Er is een fout opgetreden: {e}")


class ClimaCoreInstallThemeButton(ButtonEntity):
    """De knop om het ClimaCore thema te installeren/updaten."""

    _attr_icon = "mdi:palette-outline"
    _attr_name = "ClimaCore Thema Installeren/Updaten"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, device_info: DeviceInfo):
        self.hass = hass
        self._attr_unique_id = f"{entry.entry_id}_install_theme"
        self._attr_device_info = device_info

    async def async_press(self) -> None:
        success, message = await self.hass.async_add_executor_job(
            _copy_file_to_config,
            self.hass,
            THEME_SOURCE_SUBDIR,
            THEME_SOURCE_FILENAME,
            "themes", # Doelmap (config/themes)
            THEME_DESTINATION_FILENAME
        )
        if success:
            await self.hass.services.async_call(
                "persistent_notification", "create", {
                    "title": "ClimaCore Thema Geïnstalleerd",
                    "message": (f"{message}\n\n**BELANGRIJK:** Herstart Home Assistant nu om het thema te laden."),
                    "notification_id": "climacore_theme_installed",
                })
        else:
            await self.hass.services.async_call(
                "persistent_notification", "create", {
                    "title": "ClimaCore Thema Fout", "message": message,
                    "notification_id": "climacore_theme_error",
                })


class ClimaCoreInstallDashboardButton(ButtonEntity):
    """De knop om het ClimaCore dashboard-sjabloon beschikbaar te maken."""
    _attr_icon = "mdi:view-dashboard-edit"
    _attr_name = "ClimaCore Dashboard Sjabloon Kopiëren"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, device_info: DeviceInfo):
        self.hass = hass
        self._attr_unique_id = f"{entry.entry_id}_copy_dashboard"
        self._attr_device_info = device_info

    async def async_press(self) -> None:
        success, message = await self.hass.async_add_executor_job(
            _copy_file_to_config,
            self.hass,
            DASHBOARD_SOURCE_SUBDIR,
            DASHBOARD_TEMPLATE_FILENAME,
            DASHBOARD_DESTINATION_DIR,
            DASHBOARD_PUBLIC_FILENAME
        )
        if success:
            template_url_path = f"/climacore_assets/{DASHBOARD_PUBLIC_FILENAME}"
            instructions = (
                f"Het dashboard-sjabloon is gekopieerd. Volg deze stappen:\n\n"
                f"1. **Klik met je RECHTERMUISKNOP** op de link hieronder en kies **'Kopieer linkadres'**.\n"
                f"   *(Een normale (linker)klik werkt niet in de Home Assistant app)*\n"
                f"   [Klik hier voor het Sjabloon]({template_url_path})\n\n"
                f"2. **Plak de gekopieerde link** in een nieuw browsertabblad om de code te zien.\n"
                f"3. **Kopieer** de volledige inhoud (Ctrl+A, Ctrl+C).\n"
                f"4. Ga naar **Instellingen > Dashboards** en maak een nieuw dashboard (bv. 'ClimaCore').\n"
                f"5. Open dat nieuwe, lege dashboard.\n"
                f"6. Klik op de 3 puntjes (rechtsboven) en kies **'Dashboard bewerken'**.\n"
                f"7. Klik nogmaals op de 3 puntjes en kies **'Raw configuration editor'**.\n"
                f"8. **Plak** de gekopieerde code hier en sla op.\n\n"
                f"Vergeet niet het **'climacore'** thema in te stellen voor dit dashboard."
            )
            await self.hass.services.async_call(
                "persistent_notification", "create", {
                    "title": "ClimaCore Dashboard Sjabloon", "message": instructions,
                    "notification_id": "climacore_dashboard_template",
                })
        else:
            await self.hass.services.async_call(
                "persistent_notification", "create", {
                    "title": "ClimaCore Dashboard Fout", "message": message,
                    "notification_id": "climacore_dashboard_error",
                })

# --- NIEUWE KLASSE VOOR BLUEPRINTS (Herbruikbaar) ---
class ClimaCoreInstallBlueprintButton(ButtonEntity):
    """Een generieke knop om een ClimaCore blueprint te installeren."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, device_info: DeviceInfo, blueprint_type: str):
        """Initialiseer de blueprint knop."""
        self.hass = hass
        self._attr_device_info = device_info
        self._blueprint_type = blueprint_type

        if blueprint_type == "preheat":
            self._attr_icon = "mdi:auto-fix"
            self._attr_name = "ClimaCore Slimme Voorverwarming Installeren"
            self._attr_unique_id = f"{entry.entry_id}_install_preheat_blueprint"
            self._source_file = PREHEAT_BLUEPRINT_TEMPLATE_FILENAME
            self._dest_file = PREHEAT_BLUEPRINT_DESTINATION_FILENAME
            self._dest_dir = PREHEAT_BLUEPRINT_DESTINATION_DIR
            self._title = "Slimme Voorverwarming Blueprint"
        elif blueprint_type == "gmaps":
            self._attr_icon = "mdi:google-maps"
            self._attr_name = "ClimaCore Pro: Google Maps Beheer Installeren"
            self._attr_unique_id = f"{entry.entry_id}_install_gmaps_blueprint"
            self._source_file = GMAPS_BLUEPRINT_TEMPLATE_FILENAME
            self._dest_file = GMAPS_BLUEPRINT_DESTINATION_FILENAME
            self._dest_dir = GMAPS_BLUEPRINT_DESTINATION_DIR
            self._title = "Google Maps Beheer Blueprint"

    async def async_press(self) -> None:
        """Handel de druk op de knop af."""
        
        success, message = await self.hass.async_add_executor_job(
            _copy_file_to_config,
            self.hass,
            "assets", # Alle blueprints staan in de 'assets' map
            self._source_file,
            self._dest_dir,
            self._dest_file
        )

        if success:
            # Herlaad de automatiseringen om de blueprint zichtbaar te maken
            await self.hass.services.async_call("automation", "reload")
            
            await self.hass.services.async_call(
                "persistent_notification", "create", {
                    "title": f"ClimaCore Blueprint Geïnstalleerd",
                    "message": (
                        f"De '{self._title}' blueprint is geïnstalleerd.\n"
                        f"Je kunt deze nu gebruiken via **Instellingen > Automatiseringen & Scènes > Blueprints**."
                    ),
                    "notification_id": f"climacore_bp_{self._blueprint_type}_installed",
                })
        else:
            await self.hass.services.async_call(
                "persistent_notification", "create", {
                    "title": f"ClimaCore Blueprint Fout",
                    "message": message,
                    "notification_id": f"climacore_bp_{self._blueprint_type}_error",
                })