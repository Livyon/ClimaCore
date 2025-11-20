"""Constanten voor de ClimaCore integratie."""

# Het 'domain' van je integratie. Dit MOET overeenkomen met de mapnaam.
DOMAIN = "climacore"

# Constanten voor de config flow
CONF_ACTIVATION_CODE = "activation_code"

# URL van je publieke API Gateway
# TIP: Sla dit niet hardcoded op, maar laat de gebruiker het misschien invoeren
# of heb een 'default' en maak het overschrijfbaar.
# Voor nu hardcoded voor eenvoud.
CLIMACORE_GATEWAY_URL = "https://climacore-gateway-301645355529.europe-west1.run.app"