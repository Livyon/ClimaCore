<p align="center">
  <img src="custom_components/images/logo_readme.png" alt="Home Optimizer Logo" width="400">
</p>

<h1 align="center">📘 Home Optimizer: Installatie & Gebruikersgids</h1>

<p align="center">
  <strong>Van "Domme" Schakelaar naar Intelligente Klimaat Regisseur.</strong><br>
  <em>Volg dit stappenplan om uw Home Optimizer systeem succesvol te installeren.</em>
</p>

---

## 🧠 Hoe werkt het? (Lees dit eerst!)

Home Optimizer (powered by **ClimaCore**) werkt anders dan een standaard thermostaat. Wij gebruiken **Thermische Respons Analyse**.

> [!TIP]
> **Fysica, geen gokwerk**
> Het systeem berekent elke nacht een wiskundige formule op basis van de buitentemperatuur en de isolatie van jouw woning.
>
> * **Jouw Huis is Uniek:** Een nieuwbouwwoning met vloerverwarming reageert heel anders dan een herenhuis met radiatoren.
> * **Het Resultaat:** Tijdens de installatie vragen we: *"Hoe snel warmt je huis op?"*. Met dat ene getal weet het systeem precies hoe laat de ketel moet starten (bijv. 05:43 uur) om om 06:30 uur exact op temperatuur te zijn.

---

## 🏠 Fase 1: De Basis (Je Huis Inrichten)

Voordat we software installeren, moet Home Assistant weten hoe uw huis eruitziet.

### 1.1 Ruimtes (Cruciaal voor het Dashboard!) ⚠️
Uw nieuwe dashboard bouwt zichzelf automatisch op basis van **Ruimtes**.
1.  Ga naar **Instellingen** > **Ruimtes & Zones**.
2.  Maak de volgende ruimtes aan (let op de spelling):
    * `Woonkamer`
    * `Keuken`
    * `Eetkamer`
    * `Badkamer`
    * `Slaapkamer 1`, `Slaapkamer 2`, `Hoofdslaapkamer`
    * `Gang`
3.  **Wijs uw apparaten toe:** Ga naar **Instellingen > Apparaten**. Klik op uw slimme lampen en thermostaten en wijs ze toe aan de juiste ruimte.
    * *Zodra u dit doet, verschijnen ze automatisch op uw dashboard.*

### 1.2 Waar staat je huis?
1.  Ga naar **Instellingen** > **Ruimtes & Zones** > **Zones**.
2.  Klik op **Thuis**.
3.  Sleep de pin precies naar uw woning en zet de **Straal** op `100` meter.

### 1.3 Wie woont er?
1.  Ga naar **Instellingen** > **Personen**.
2.  Maak voor elk gezinslid een persoon aan.
3.  Selecteer onderaan bij "Selecteer de apparaten" de telefoon van die persoon (voor aanwezigheidsdetectie).

### 1.4 Virtuele Knoppen (Helpers)
Maak twee schakelaars aan via **Instellingen** > **Apparaten & Diensten** > **Helpers** > **+ Helper aanmaken** > **Schakelaar**:

| Naam | Pictogram | Functie |
| :--- | :--- | :--- |
| `Gasten Aanwezig` | `mdi:account-group` | Voorkomt dat verwarming uitgaat bij bezoek |
| `Onderweg naar Huis` | `mdi:car` | Handmatige trigger voor voorverwarmen |

---

## 🏗️ Fase 2: De "App Store" (HACS) Installeren

We installeren nu de winkel voor de Home Optimizer software.

1.  **Geavanceerde Modus:** Klik op je Profiel (linksonder) > Zet **Geavanceerde modus** AAN.
2.  **Terminal:** Ga naar Instellingen > Add-ons > Zoek `Terminal & SSH` > Installeer & Start > **Open web-UI**.

**Voer nu het installatiecommando in:**

```bash
wget -O - [https://get.hacs.xyz](https://get.hacs.xyz) | bash -
