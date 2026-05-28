# 🏆 WK Pool 2026

Lokale web-app voor het bijhouden van WK-voorspellingen. Werkt als `.exe` (Windows) én in de browser.

## Snel starten

### Optie A — EXE (Windows, makkelijkst)
1. Ga naar de [nieuwste release](https://github.com/brennyc86/wk-pool/releases/latest)
2. Download `WK_Pool_2026.zip` en pak uit
3. Zet `WK_Pool_2026.exe` en `schema.json` **in dezelfde map**
4. Dubbelklik op `WK_Pool_2026.exe`
5. De browser opent automatisch op `http://localhost:5026`

### Optie B — Python (Mac / Linux / Windows)
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

---

## Hoe werkt het?

| Feature | Uitleg |
|---|---|
| **Inloggen** | Typ je naam — geen wachtwoord nodig |
| **Meerdere gebruikers** | Iedereen logt in met eigen naam, ook op 1 pc |
| **Voorspellingen** | Score invullen per wedstrijd (bijv. `2-1`) |
| **Vergrendeling** | Zodra een wedstrijd begint, kun je die niet meer wijzigen |
| **Andere wedstrijden** | Dezelfde dag, andere wedstrijd → gewoon nog aanpasbaar |
| **Uitslagen** | Iedereen kan uitslagen invoeren (geen PIN nodig) |
| **Punten** | Exacte score = 3 pts · juiste uitslag = 1 pt · juiste kampioen = 10 bonus pts |
| **Stand** | Automatisch bijgewerkte ranglijst |

---

## Puntensysteem

| Situatie | Punten |
|---|---|
| ⚽ Exacte score correct (bijv. 2-1) | **3 punten** |
| ✅ Juiste uitslag (win / gelijk / verlies) | **1 punt** |
| ❌ Fout | 0 punten |
| ⭐ Juiste wereldkampioen | **10 bonus punten** |

---

## Bestandsstructuur

```
WK_Pool_2026.exe    ← het programma
schema.json         ← wedstrijdschema (aanpasbaar)
wk_pool_data.dat    ← voorspellingen (automatisch aangemaakt, base64 gecodeerd)
```

> **Let op:** `wk_pool_data.dat` bevat alle voorspellingen. Maak er regelmatig een backup van.

---

## Wedstrijdschema — 12 groepen, 72 wedstrijden

Tijden zijn **CEST** (UTC+2). Speeldata: 11 juni – 28 juni 2026 (groepsfase).

| Groep | Teams |
|---|---|
| A | Mexico · Zuid-Afrika · Zuid-Korea · Tsjechië |
| B | Canada · Bosnië-Herzegovina · Qatar · Zwitserland |
| C | Brazilië · Marokko · Haïti · Schotland |
| D | VS · Paraguay · Australië · Turkije |
| E | Duitsland · Curaçao · Ivoorkust · Ecuador |
| F | Nederland · Japan · Zweden · Tunesië |
| G | België · Egypte · Iran · Nieuw-Zeeland |
| H | Spanje · Kaapverdië · Saudi-Arabië · Uruguay |
| I | Frankrijk · Senegal · Irak · Noorwegen |
| J | Argentinië · Algerije · Oostenrijk · Jordanië |
| K | Portugal · Congo DR · Oezbekistan · Colombia |
| L | Engeland · Kroatië · Ghana · Panama |

---

## Technische details

### Stack
- **Backend:** Python 3.11 + Flask (embedded single-page app)
- **Frontend:** Vanilla JS + CSS (geen externe dependencies)
- **Opslag:** Base64-gecodeerd JSON in `wk_pool_data.dat`
- **EXE:** PyInstaller 6.x + Tkinter controlvenster

### API endpoints
| Endpoint | Methode | Beschrijving |
|---|---|---|
| `/` | GET | HTML applicatie |
| `/api/schema` | GET | Wedstrijdschema |
| `/api/data` | GET | Voorspellingen + uitslagen + vergrendelstatus |
| `/api/standings` | GET | Ranglijst |
| `/api/gebruiker` | POST | Inloggen / registreren |
| `/api/voorspelling` | POST | Voorspelling opslaan |
| `/api/uitslag` | POST | Officiële uitslag invoeren |
| `/api/kampioen` | POST | Kampioenvoorspelling opslaan |
| `/api/kampioen_echt` | POST | Echte winnaar registreren |

---

## Automatische build

Bij elke push naar `main` bouwt GitHub Actions automatisch een nieuwe `WK_Pool_2026.exe` en publiceert deze als [GitHub Release](https://github.com/brennyc86/wk-pool/releases/latest).

```
push → GitHub Actions (Windows) → PyInstaller → EXE → Release (tag: latest)
```

---

*Gemaakt met Python (Flask + Tkinter) · GitHub Actions voor automatische builds*
