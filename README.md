# 🏆 WK Pool 2026

Lokale web-app voor het bijhouden van WK-voorspellingen. Werkt als `.exe` (Windows) én in de browser.

## Snel starten

### Optie A — EXE (Windows)
1. Download `WK_Pool_2026.exe` + `schema.json` uit de map `exe/`
2. Zet beide bestanden **in dezelfde map**
3. Dubbelklik op `WK_Pool_2026.exe`
4. De browser opent automatisch op `http://localhost:5026`

### Optie B — Python (Mac/Linux/Windows)
```bash
pip install flask
python main.py
```
Browser opent automatisch. Of ga zelf naar `http://localhost:5026`.

### Optie C — Netwerk (meerdere computers)
Start de app op één computer. Andere computers in hetzelfde netwerk gaan naar:
```
http://<ip-van-host>:5026
```

## Hoe werkt het?

| Feature | Uitleg |
|---|---|
| **Inloggen** | Typ je naam — geen wachtwoord nodig |
| **Meerdere gebruikers** | Iedereen logt in met eigen naam, ook op 1 pc |
| **Voorspellingen** | Score invullen per wedstrijd (bijv. `2-1`) |
| **Vergrendeling** | Zodra een wedstrijd begint, kun je die niet meer wijzigen |
| **Andere wedstrijden** | Dezelfde dag, andere wedstrijd → gewoon nog aanpasbaar |
| **Uitslagen** | Iedereen kan uitlagen invoeren (geen PIN nodig) |
| **Punten** | Exacte score = 3 pts, juiste uitslag = 1 pt, juiste kampioen = 10 bonus pts |
| **Stand** | Automatisch bijgewerkte ranglijst |

## Bestandsstructuur

```
WK_Pool_2026.exe    ← het programma
schema.json         ← wedstrijdschema (aanpasbaar)
wk_pool_data.dat    ← voorspellingen (automatisch aangemaakt, gecodeerd)
```

> **Let op:** `wk_pool_data.dat` bevat alle voorspellingen. Maak er regelmatig een backup van.

## Puntensysteem

- ⚽ Exacte score correct → **3 punten**
- ✅ Juiste uitslag (win/gelijk/verlies) → **1 punt**
- ❌ Fout → 0 punten
- ⭐ Juiste wereldkampioen → **10 bonus punten**

## Tijden

Alle tijden zijn **CEST** (Nederlandse zomertijd, UTC+2).

## Wedstrijdschema

Het schema bevat alle **72 groepswedstrijden** van het WK 2026 (11 juni – 28 juni):

| Groep | Teams |
|---|---|
| A | Mexico, Zuid-Afrika, Zuid-Korea, Tsjechië |
| B | Canada, Bosnië-Herzegovina, Qatar, Zwitserland |
| C | Brazilië, Marokko, Haïti, Schotland |
| D | VS, Paraguay, Australië, Turkije |
| E | Duitsland, Curaçao, Ivoorkust, Ecuador |
| F | Nederland, Japan, Zweden, Tunesië |
| G | België, Egypte, Iran, Nieuw-Zeeland |
| H | Spanje, Kaapverdië, Saudi-Arabië, Uruguay |
| I | Frankrijk, Senegal, Irak, Noorwegen |
| J | Argentinië, Algerije, Oostenrijk, Jordanië |
| K | Portugal, Congo DR, Oezbekistan, Colombia |
| L | Engeland, Kroatië, Ghana, Panama |

## Automatische build

Bij elke push naar `main` bouwt GitHub Actions automatisch een nieuwe `WK_Pool_2026.exe`.  
De exe staat daarna in de map `exe/` in de repo.

---
*Gemaakt met Python (Flask + Tkinter) · GitHub Actions voor automatische builds*
