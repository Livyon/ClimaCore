📘 ClimaCore: Installatie & Gebruikersgids
Welkom bij ClimaCore! Je staat op het punt om je Home Assistant te upgraden naar een Intelligente Klimaat Regisseur.

🧠 Hoe werkt ClimaCore? (Lees dit eerst!)
Voordat we beginnen, is het goed om te weten waarom ClimaCore anders is dan een "domme" thermostaat. ClimaCore gebruikt Thermische Respons Analyse.

Wat betekent dit?

Fysica, geen gokwerk: ClimaCore berekent elke nacht een wiskundige formule op basis van de buitentemperatuur, de huidige binnentemperatuur en de isolatie van jouw woning.

Jouw Huis is Uniek: Een nieuwbouwwoning met vloerverwarming reageert heel anders dan een herenhuis met radiatoren.

Het Resultaat: Tijdens de installatie vragen we: "Hoe snel warmt je huis op?". Met dat ene getal weet ClimaCore precies hoe laat hij moet starten (bijv. 05:43 uur) om om 06:30 uur exact op temperatuur te zijn. Geen minuut te vroeg (verspilling), geen minuut te laat (koud).

🏠 Fase 1: De Basis (Je Huis Inrichten)
Voordat we software installeren, moet Home Assistant weten waar je woont, wie er is, en maken we een paar "schakelaars" aan.

Stap 1.1: Waar staat je huis?

Ga in Home Assistant naar Instellingen > Ruimtes & Zones.

Klik bovenaan op het tabblad Zones.

Klik op de zone Thuis (Home).

Sleep de pin op de kaart precies naar jouw woning.

Zet de Straal op 100 meter (zodat hij niet flippert als je in de tuin staat).

Klik op Opslaan.

Stap 1.2: Wie woont er?

Ga naar Instellingen > Personen.

Klik rechtsonder op + Persoon toevoegen.

Maak voor elk gezinslid een persoon aan.

Belangrijk: Zorg dat iedereen de Home Assistant App op zijn telefoon heeft.

Selecteer bij elke persoon onderaan bij "Selecteer de apparaten..." hun telefoon. Dit zorgt voor de GPS-locatie.

Stap 1.3: Toegang van buitenaf (Essentieel!) ClimaCore moet weten wanneer je onderweg naar huis bent, ook als je op 4G zit.

Onze Aanrader: Neem Home Assistant Cloud (Nabu Casa).

Kosten: +/- €7,50 per maand (eerste maand vaak gratis).

Waarom? Geen technisch gedoe, veilig én het werkt direct.

🎁 Bonus: Je krijgt hierbij direct Google Assistant integratie ("Hey Google, zet de verwarming op 21 graden!").

Instellen: Ga naar Instellingen > Home Assistant Cloud.

Stap 1.4: Virtuele Knoppen aanmaken (Helpers) We hebben twee schakelaars nodig die ClimaCore gebruikt om te weten of je bezoek hebt of onderweg bent.

Ga naar Instellingen > Apparaten & Diensten.

Klik bovenaan op het tabblad Helpers.

Klik rechtsonder op + Helper aanmaken > Schakelaar.

Naam: Gasten Aanwezig

Pictogram: mdi:account-group (Typ dit in)

Klik op Aanmaken.

Klik nogmaals op + Helper aanmaken > Schakelaar.

Naam: Onderweg naar Huis

Pictogram: mdi:car

Klik op Aanmaken.

🏗️ Fase 2: De "App Store" (HACS) Installeren
We installeren nu de winkel voor de ClimaCore software.

Stap 2.1: Geavanceerde Modus

Klik linksonder in de zijbalk op je Gebruikersnaam (je profiel).

Scroll naar beneden en zet het schuifje aan bij Geavanceerde modus.

Stap 2.2: De Terminal starten

Ga naar Instellingen > Add-ons.

Klik rechtsonder op Add-on winkel.

Typ in de zoekbalk: Terminal.

Klik op Terminal & SSH > Installeer.

Wacht even en klik dan op Start.

Klik op Open web-UI. Je ziet een zwart scherm.

Stap 2.3: De Installatiecode (Let op!)

Kopieer deze regel code: wget -O - https://get.hacs.xyz | bash -

Ga naar het zwarte schermpje.

BELANGRIJK: Ctrl+V (Plakken) werkt hier niet!

Klik met je rechtermuisknop in het zwarte scherm.

Kies Plakken (Paste).

Druk op Enter. Wacht tot hij zegt "Installation complete".

Herstart Home Assistant: Ga naar Instellingen > Systeem (rechtsboven aan/uit knop) > Home Assistant Herstarten.

Stap 2.4: De winkel koppelen

Na herstart: Ga naar Instellingen > Apparaten & Diensten.

Klik rechtsonder op + Integratie toevoegen.

Zoek naar HACS, klik erop, vink alles aan en volg de stappen (inloggen met GitHub).

📦 Fase 3: ClimaCore & Extra's Installeren
Stap 3.1: De Dashboard tools

Ga in het menu links naar HACS > Frontend.

Klik rechtsonder op + Explore & Download Repositories.

Zoek en installeer deze drie onderdelen (één voor één):

Bubble Card (voor de mooie knoppen).

Restriction Card (voor de pincode op de gastenmodus).

card-mod (voor de achtergronden).

Klik na installatie op Opnieuw Laden (Reload) als daarom gevraagd wordt.

Stap 3.2: ClimaCore zelf

Ga in HACS naar Integraties.

Klik rechtsboven op de 3 puntjes > Aangepaste repositories.

Plak bij 'Repository' deze link: [HIER_JOUW_GITHUB_LINK_PLAATSEN]

Kies bij 'Categorie': Integratie. Klik op Toevoegen.

Klik op ClimaCore > Download.

Herstart Home Assistant opnieuw volledig.

🔑 Fase 4: Activeren & Configureren
Stap 4.1: Activeren

Ga naar Instellingen > Apparaten & Diensten.

Klik rechtsonder op + Integratie toevoegen.

Zoek naar ClimaCore.

Vul je Activatiecode in en klik op Verzenden.

Stap 4.2: Configureren (Vragenlijst) Klik bij de ClimaCore integratie op Configureren. Hier stellen we de Thermische Respons Analyse in.

Algemeen:

Doeltijd Ochtend: Hoe laat wil je dat de woonkamer warm is? (Bijv. 06:30). ClimaCore berekent zelf de starttijd.

Opwarmtijd (minuten per graad): Dit is de belangrijkste instelling!

Vloerverwarming / Goed Geïsoleerd: Vul 45 tot 60 in. (Systeem reageert traag).

Radiatoren / Ouder Huis: Vul 20 tot 30 in. (Systeem reageert snel).

Tip: Bij twijfel, begin op 30.

Entiteiten:

Weer: "Forecast Thuis".

Wi-Fi: Jouw Wi-Fi naam (SSID).

Helpers: Koppel de Helpers die je in Stap 1.4 maakte.

Zones & Setpoints:

Koppel je thermostaten aan de juiste Zone.

Kies bij "Setpoint Groep" het kamertype (Woonkamer, Badkamer, etc.).

Stel per profiel (Dag - Fris, Dag - Koud) je gewenste temperaturen in.

🎨 Fase 5: Dashboard & Thema (De Finale)
Stap 5.1: De Bestanden installeren

Ga naar Instellingen > Apparaten & Diensten > ClimaCore > 1 Apparaat.

Druk op ClimaCore Thema Installeren/Updaten. (Wacht op 'Succes').

Druk op ClimaCore Dashboard Sjabloon Kopiëren. (Er verschijnt een melding in de zijbalk).

Ververs je browser (Druk op F5).

Stap 5.2: Het Thema activeren (Voor je hele huis) We zorgen nu dat je hele Home Assistant er strak uitziet.

Klik links onderaan in de zijbalk op je Gebruikersnaam (Je Profiel).

Zoek het kopje Algemeen (of Thema).

Klik op het keuzemenu bij Thema en kies ClimaCore Theme.

Je ziet direct dat de achtergrond en kleuren veranderen!

Stap 5.3: Het Dashboard plaatsen

Kijk in de linker zijbalk bij Meldingen.

Klik in de melding met je rechtermuisknop op de link "Klik hier voor het Sjabloon" en kies Linkadres kopiëren.

Open een nieuw tabblad in je browser en plak de link.

Je browser downloadt nu een bestand: climacore-dashboard-template.yaml.

Ga naar je map Downloads, open dit bestand met Kladblok en kopieer alle tekst (Ctrl+A, Ctrl+C).

Ga terug naar Home Assistant -> Instellingen -> Dashboards -> Dashboard toevoegen.

Kies Nieuw dashboard, noem het 'ClimaCore' en open het.

Klik rechtsboven op het potloodje ✏️ -> 3 puntjes -> Raw configuration editor.

Haal alles weg, en plak jouw tekst erin. Klik op Opslaan.

Stap 5.4: Je eigen apparaten koppelen Het dashboard ziet er nu mooi uit, maar de knoppen werken nog niet omdat ze nog niet gekoppeld zijn aan jouw lampen.

Klik (terwijl je in bewerk-modus bent) op een kaart, bijvoorbeeld "Woonkamer".

Zoek in het menu naar Entity.

Haal de vreemde tekst weg en selecteer jouw eigen lamp of thermostaat uit de lijst.

Herhaal dit voor alle knoppen en klik rechtsboven op Klaar.

🤖 Fase 6: Slimme Automatiseringen (Blueprints)
ClimaCore heeft twee extra functies die je via het ClimaCore apparaat kunt installeren.

1. Slimme Voorverwarming (via Proximity)
Wat doet het? ClimaCore ziet dat je onderweg naar huis bent en vraagt via een melding: "Zal ik de verwarming alvast aanzetten?".

Instellen:

Installeer eerst de gratis Proximity integratie via Instellingen > Apparaten & Diensten. Kies je "Thuis" zone en vink de personen aan.

Ga naar Instellingen > Automatiseringen > Blueprints, kies de Slimme Voorverwarming blueprint en koppel je nieuwe Proximity sensor.

2. ClimaCore Pro: Google Maps Beheer
Wat doet het? Wil je échte reistijd weten op basis van live files en verkeersdrukte? Dan heb je Google Maps data nodig. Dit is een Pro Service van Home Optimizer.

Wij regelen de complexe Google Cloud setup en API-sleutels.

Jij krijgt de meest accurate aankomsttijden, zonder technisch gedoe.

Interesse? Neem contact met ons op voor de ClimaCore Pro upgrade.
