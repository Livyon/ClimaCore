<p align="center">
  <img src="custom_components/climacore/assets/logo.png" alt="ClimaCore Logo" width="400">
</p>

<h1 align="center">📘 ClimaCore: Installatie & Gebruikersgids</h1>

<p align="center">
  <strong>Van "Domme" Schakelaar naar Intelligente Klimaat Regisseur.</strong><br>
  <em>Volg dit stappenplan om ClimaCore succesvol te installeren.</em>
</p>

---

## 🧠 Hoe werkt ClimaCore? (Lees dit eerst!)

Voordat we beginnen: ClimaCore werkt anders dan een standaard thermostaat. Wij gebruiken **Thermische Respons Analyse**.

> [!TIP]
> **Fysica, geen gokwerk**
> ClimaCore berekent elke nacht een wiskundige formule op basis van de buitentemperatuur en de isolatie van jouw woning.
>
> * **Jouw Huis is Uniek:** Een nieuwbouwwoning met vloerverwarming reageert heel anders dan een herenhuis met radiatoren.
> * **Het Resultaat:** Tijdens de installatie vragen we: *"Hoe snel warmt je huis op?"*. Met dat ene getal weet ClimaCore precies hoe laat hij moet starten (bijv. 05:43 uur) om om 06:30 uur exact op temperatuur te zijn.

---

## 🏠 Fase 1: De Basis (Je Huis Inrichten)

Voordat we software installeren, moet Home Assistant de basis kennen.

### 1.1 Waar staat je huis?
1.  Ga naar **Instellingen** > **Ruimtes & Zones**.
2.  Klik op tabblad **Zones** > **Thuis**.
3.  Sleep de pin precies naar jouw woning.
4.  Zet de **Straal** op `100` meter.

### 1.2 Wie woont er?
1.  Ga naar **Instellingen** > **Personen**.
2.  Maak voor elk gezinslid een persoon aan.
3.  **Cruciaal:** Selecteer onderaan bij "Selecteer de apparaten" de telefoon van die persoon (voor GPS).

> [!IMPORTANT]
> **Toegang van buitenaf**
> ClimaCore moet weten wanneer je onderweg naar huis bent (via 4G). Wij raden **Home Assistant Cloud (Nabu Casa)** aan.
> * Veilig & werkt direct.
> * Inclusief **Google Assistant** ("Hey Google, zet de verwarming op 21 graden!").

### 1.3 Virtuele Knoppen (Helpers)
Maak twee schakelaars aan via **Instellingen** > **Apparaten & Diensten** > **Helpers** > **+ Helper aanmaken** > **Schakelaar**:

| Naam | Pictogram | Functie |
| :--- | :--- | :--- |
| `Gasten Aanwezig` | `mdi:account-group` | Voorkomt dat verwarming uitgaat bij bezoek |
| `Onderweg naar Huis` | `mdi:car` | Handmatige trigger voor voorverwarmen |

---

## 🏗️ Fase 2: De "App Store" (HACS) Installeren

We installeren nu de winkel voor de ClimaCore software.

1.  **Geavanceerde Modus:** Klik op je Profiel (linksonder) > Zet **Geavanceerde modus** AAN.
2.  **Terminal:** Ga naar Instellingen > Add-ons > Zoek `Terminal & SSH` > Installeer & Start > **Open web-UI**.

**Voer nu het installatiecommando in:**

```
wget -O - https://get.hacs.xyz | bash -
```

> [!WARNING]
> **Let op bij het plakken!**
> `Ctrl+V` werkt vaak niet in het terminal venster.
> Klik met je **Rechtermuisknop** in het zwarte scherm en kies **Plakken** (Paste). Druk daarna op ENTER.

Herstart hierna Home Assistant volledig en voeg de **HACS** integratie toe via *Apparaten & Diensten*.

---

## 📦 Fase 3: Installatie

### 3.1 Dashboard Tools (via HACS Frontend)
Zoek en installeer deze drie onderdelen in HACS > Frontend:
* ☑️ `Bubble Card` (Voor de interface)
* ☑️ `Restriction Card` (Voor beveiliging gastenmodus)
* ☑️ `card-mod` (Voor de achtergronden)

### 3.2 ClimaCore (via HACS Integraties)
1.  Ga naar HACS > Integraties > 3 puntjes (rechtsboven) > **Aangepaste repositories**.
2.  Plak de ClimaCore GitHub link.
3.  Download ClimaCore en **herstart Home Assistant**.

---

## 🔑 Fase 4: Activeren & Configureren

Ga naar **Instellingen** > **Apparaten & Diensten** > **+ Integratie toevoegen** > **ClimaCore**.
Vul je activatiecode in. Klik daarna op **Configureren**.

### De Instellingen uitgelegd:

* **Doeltijd Ochtend:** Hoe laat wil je het warm hebben?
* **Opwarmtijd (minuten per graad):** *De belangrijkste instelling!*
    * *Vloerverwarming:* Vul `45` tot `60` in.
    * *Radiatoren:* Vul `20` tot `30` in.
* **Zones & Setpoints:**
    * Koppel je thermostaten aan een zone.
    * **Setpoint Groep:** Vertel ClimaCore wat voor kamer het is (bijv. "Woonkamer").
    * Stel de temperaturen in voor **Dag - Fris** (normaal) en **Dag - Koud** (vrieskou).

---

## 🎨 Fase 5: Dashboard & Thema

Ga naar het **ClimaCore Apparaat** in Home Assistant en gebruik de installatieknoppen:

1.  Druk op **Thema Installeren**.
2.  Druk op **Dashboard Sjabloon Kopiëren**.

### Het Dashboard plaatsen
1.  Kijk in de meldingen (zijbalk). Klik **Rechtermuisknop** op de link > **Linkadres kopiëren**.
2.  Open een nieuw tabblad, plak de link, en **kopieer alle code**.
3.  Maak een nieuw Dashboard aan in Home Assistant.
4.  Klik potloodje ✏️ > 3 puntjes > **Raw configuration editor**.
5.  Plak de code.

> [!NOTE]
> **Thema Activeren**
> Vergeet niet in de dashboard-instellingen (of je profiel) het thema op **ClimaCore Theme** te zetten, anders zie je de dynamische achtergronden niet!

---

## 🤖 Fase 6: Slimme Automatiseringen

Je kunt via het ClimaCore apparaat twee extra Blueprints installeren:

### 🚗 1. Slimme Voorverwarming (Gratis)
*Werkt via de 'Proximity' integratie.*
ClimaCore ziet dat je onderweg bent en vraagt: *"Zal ik de verwarming alvast aanzetten?"*

### 🚦 2. ClimaCore Pro: Google Maps (Premium)
*Werkt via Google Cloud Platform.*
Wil je sturen op basis van **actuele file-informatie**?
* Dit is een **Pro Service** van Home Optimizer.
* Wij regelen de Google Cloud setup en API-keys.
* Neem contact op voor een upgrade.

---
<p align="center"><em>Developed by Home Optimizer</em></p>
