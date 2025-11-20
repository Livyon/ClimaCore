"""API Client voor de ClimaCore Gateway."""
import requests
import logging
import json

from .const import CLIMACORE_GATEWAY_URL

_LOGGER = logging.getLogger(__name__)

# Aangepaste Foutklasses
class ApiConnectionError(Exception):
    """Fout bij het verbinden met de API."""
    pass

class ApiTimeoutError(Exception):
    """Timeout bij het verbinden met de API."""
    pass

class ApiAuthError(Exception):
    """Ongeldige activatiecode."""
    pass

class ClimaCoreApiClient:
    """De API Client die communiceert met de ClimaCore Gateway."""

    def __init__(self, activation_code: str, gateway_url: str = CLIMACORE_GATEWAY_URL):
        """Initialiseer de API client."""
        self._activation_code = activation_code
        # Zorg dat de URL geen trailing slash heeft
        self._gateway_url = gateway_url.rstrip('/')
        self._headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _make_request(self, endpoint: str, payload: dict, timeout: int = 15) -> dict:
        """
        Helper-functie om een verzoek naar een endpoint te sturen.
        Deze functie is *synchroon* en moet via hass.async_add_executor_job worden aangeroepen.
        """
        url = f"{self._gateway_url}{endpoint}"
        
        data_to_send = {
            "activation_code": self._activation_code,
            "payload": payload
        }

        # --- AANGEPAST: Robuustere foutafhandeling ---
        try:
            response = requests.post(url, json=data_to_send, headers=self._headers, timeout=timeout)

            if response.status_code == 200:
                # Probeer JSON te parsen
                try:
                    return response.json()
                except requests.exceptions.JSONDecodeError as e:
                    _LOGGER.error(f"Gateway gaf 200 OK, maar response was geen JSON. {e}")
                    raise ApiConnectionError(f"Gateway gaf 200 OK, maar response was geen JSON.")

            elif response.status_code == 403:
                _LOGGER.error("Activatiecode is ongeldig of verlopen (403 Forbidden).")
                raise ApiAuthError("Activatiecode ongeldig.")
            
            else:
                # Probeer de fout-JSON van de gateway te loggen
                try:
                    error_json = response.json()
                    _LOGGER.error(f"Gateway gaf onverwachte status: {response.status_code}, {error_json}")
                except requests.exceptions.JSONDecodeError:
                    _LOGGER.error(f"Gateway gaf onverwachte status: {response.status_code}, {response.text}")
                
                raise ApiConnectionError(f"Onverwachte fout van de Gateway: {response.status_code}")

        except requests.exceptions.Timeout:
            _LOGGER.error(f"Timeout bij verbinden met ClimaCore Gateway ({url})")
            raise ApiTimeoutError("Verbinding met de ClimaCore Gateway time-out.")
        
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Fout bij verbinden met ClimaCore Gateway: {e}")
            raise ApiConnectionError(f"Verbindingsfout: {e}")
            
        except Exception as e:
            # vang alle andere mogelijke fouten af (zoals bugs in de code hierboven)
            _LOGGER.error(f"Onverwachte fout in _make_request: {e}")
            # We raisen ApiConnectionError zodat de config flow het snapt
            raise ApiConnectionError(f"Onverwachte fout in API client: {e}")
        # --- EINDE AANPASSING ---

    def validate_activation_code(self) -> str:
        """
        Valideert de activatiecode door een dummy-request naar de Gateway te sturen.
        """
        # We gebruiken een minimale 'test' payload.
        # De Gateway checkt de code in Firestore. Als die klopt, stuurt hij het door naar main-logic.
        # Main-logic zal waarschijnlijk een lege actielijst terugsturen (wat een 200 OK is).
        test_payload = {
            "test_connection": True,
            "sensors": {},
            "config": {},
            "persons": {},
            "climate_zones": {},
            "context": {"current_time": "12:00:00"}
        }

        try:
            # Korte timeout voor de validatie-check
            self._make_request("/api/v1/main_logic", payload=test_payload, timeout=10)
            _LOGGER.info("Activatiecode succesvol gevalideerd.")
            return "valid"
            
        except ApiAuthError:
            return "invalid_auth"
        except ApiTimeoutError:
            return "timeout"
        except ApiConnectionError:
            # Als we hier komen, is de code waarschijnlijk WEL geldig (want geen 403),
            # maar faalde de backend (bv. 500 error).
            # Voor installatie-doeleinden kunnen we dit als 'cannot_connect' markeren
            # zodat de gebruiker het opnieuw probeert.
            return "cannot_connect"
        except Exception:
            return "unknown"


    def trigger_main_logic(self, payload: dict) -> dict:
        """Roept de hoofdlogica (Het Brein) aan in de cloud."""
        _LOGGER.debug("API-aanroep: trigger_main_logic")
        # Standaard timeout van 30 seconden voor de 'echte' logica
        return self._make_request("/api/v1/main_logic", payload, timeout=30)

    def trigger_proactive_start(self, payload: dict) -> dict:
        """Roept de proactieve start calculator aan in de cloud."""
        _LOGGER.debug("API-aanroep: trigger_proactive_start")
        return self._make_request("/api/v1/proactive_start", payload, timeout=30)