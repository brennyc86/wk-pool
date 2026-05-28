# CLAUDE.md — WK Pool 2026

Context voor Claude Code bij toekomstige sessies aan dit project.

## Project

Lokale web-app voor een WK voetbalpool (FIFA Wereldkampioenschap 2026, 48 teams, 72 groepswedstrijden).  
Werkt zowel als `.exe` (Windows, via PyInstaller + Tkinter) als rechtstreeks in de browser (Python + Flask).

**GitHub repo:** `https://github.com/brennyc86/wk-pool`

---

## Technische stack

| Component | Keuze |
|---|---|
| Backend | Python 3.11 + Flask |
| Frontend | Vanilla JS + CSS (embedded in main.py als HTML_TEMPLATE) |
| Opslag | Base64-gecodeerd JSON → `wk_pool_data.dat` (naast de exe) |
| Schema | `schema.json` (naast de exe, aanpasbaar) |
| Packaging | PyInstaller 6.x (spec: `wk_pool.spec`) |
| GUI (exe) | Tkinter controlvenster (houdt Flask-server in leven) |
| Build CI | GitHub Actions → Windows runner → EXE + GitHub Release |

---

## Bestandsstructuur

```
main.py             ← Flask app + embedded HTML/CSS/JS (single-file SPA)
schema.json         ← WK-schema: 12 groepen × 6 wedstrijden = 72 matches
wk_pool.spec        ← PyInstaller spec (PyInstaller 6.x compatibel)
requirements.txt    ← flask>=2.3.0, pyinstaller>=6.0.0
.github/
  workflows/
    build.yml       ← Windows runner: bouwen, committen naar exe/, GitHub Release
exe/
  WK_Pool_2026.exe  ← automatisch gebouwd door CI
  schema.json       ← automatisch gekopieerd door CI
```

**Databestanden (niet in repo, naast de exe):**
```
wk_pool_data.dat    ← voorspellingen + uitslagen (base64 JSON, automatisch aangemaakt)
```

---

## Architectuur van main.py

```
APP_DIR             ← map van de exe (of main.py bij directe Python-start)
SCHEMA_FILE         ← APP_DIR / "schema.json"
DATA_FILE           ← APP_DIR / "wk_pool_data.dat"
PORT = 5026

_schema()           → laad schema.json
_laad()             → lees + base64-decodeer wk_pool_data.dat
_sla(d)             → base64-encodeer + schrijf wk_pool_data.dat
_vergrendeld(match) → True als wedstrijd al begonnen is (datetime.now() >= starttijd)
_punten(v, u)       → 3 (exact), 1 (juiste uitslag), 0 (fout)
_totaal(naam, ...)  → dict met punten, exact, correct, bonus, ingevuld
```

### Data-formaat (wk_pool_data.dat)

```json
{
  "gebruikers": {
    "Brendan": {
      "A1": "2-1",
      "A2": "0-0",
      "__kampioen__": "Nederland"
    }
  },
  "uitslagen": {
    "A1": "2-1",
    "__kampioen__": "Brazilië"
  }
}
```
Dit JSON-object wordt base64-gecodeerd opgeslagen.

### API endpoints

| Method | Pad | Body | Beschrijving |
|---|---|---|---|
| GET | `/` | — | Serveert de HTML SPA |
| GET | `/api/schema` | — | Volledige schema.json |
| GET | `/api/data` | — | Voorspellingen + uitslagen + vergrendel-status per wedstrijd |
| GET | `/api/standings` | — | Ranglijst gesorteerd op punten |
| POST | `/api/gebruiker` | `{naam}` | Registreer/log in gebruiker |
| POST | `/api/voorspelling` | `{naam, id, score}` | Sla voorspelling op (geblokkeerd als vergrendeld) |
| POST | `/api/uitslag` | `{id, score}` | Sla officiële uitslag op |
| POST | `/api/kampioen` | `{naam, team}` | Sla kampioenvoorspelling op |
| POST | `/api/kampioen_echt` | `{team}` | Sla echte winnaar op |

### Puntensysteem
- Exacte score (bv. 2-1) → **3 punten**
- Juiste uitslag (win/gelijk/verlies) → **1 punt**
- Fout → 0 punten
- Juiste wereldkampioen → **10 bonus punten**

### Vergrendeling
`_vergrendeld(match)` vergelijkt `datetime.now()` met de aanvangstijd uit schema.json.  
Tijden zijn CEST (UTC+2). Zodra een wedstrijd is begonnen, kan die specifieke wedstrijd  
niet meer worden aangepast — andere wedstrijden dezelfde dag zijn nog steeds bewerkbaar.

---

## Schema-formaat (schema.json)

```json
{
  "toernooi": "FIFA Wereldkampioenschap 2026",
  "groepen": [
    {
      "naam": "Groep A",
      "teams": ["Mexico", "Zuid-Afrika", "Zuid-Korea", "Tsjechië"],
      "wedstrijden": [
        {"id": "A1", "datum": "2026-06-11", "tijd": "21:00", "thuis": "Mexico", "uit": "Zuid-Afrika"},
        ...
      ]
    }
  ]
}
```
12 groepen (A t/m L), elk 4 teams, elk 6 wedstrijden = 72 totaal.

---

## Build-proces (GitHub Actions)

`.github/workflows/build.yml` draait op `windows-latest`:
1. Checkout repo
2. Python 3.11 instellen
3. `pip install flask pyinstaller`
4. `pyinstaller wk_pool.spec` → `dist/WK_Pool_2026.exe`
5. Release-map aanmaken + ZIP
6. EXE committen naar `exe/` in de repo
7. GitHub Release aanmaken/overschrijven met tag `latest`
8. Artifact uploaden (30 dagen bewaard)

**Trigger:** push naar `main` als `main.py`, `schema.json`, `wk_pool.spec` of `build.yml` wijzigt; of handmatig via `workflow_dispatch`.

### PyInstaller spec — belangrijke noten
`wk_pool.spec` gebruikt `collect_all()` voor flask, werkzeug en jinja2.  
**Niet** teruggaan naar de oude API (`a.ztos`, `cipher=block_cipher`) — die bestaat niet meer in PyInstaller 6.x en crasht de build.

---

## Bekende problemen & fixes (chronologisch)

| Datum | Probleem | Oplossing |
|---|---|---|
| 2026-05-28 | Scherm zwart na inloggen | `showApp()` zette `display = ''` i.p.v. `display = 'block'`; CSS `#app {display:none}` bleef dan gelden |
| 2026-05-28 | PyInstaller build crashte op `a.ztos` | Spec herschreven voor PyInstaller 6.x: `PYZ(a.pure)`, geen `cipher`, `collect_all()` voor flask/werkzeug/jinja2 |

---

## Lokaal draaien (ontwikkeling)

```bash
pip install flask
python main.py
# → browser opent op http://localhost:5026
```

Schema.json en wk_pool_data.dat worden aangemaakt naast main.py.

---

## Roadmap / TODO

- [ ] Knockout-fase toevoegen (kwartfinales, halve finales, finale — 16 extra wedstrijden)
- [ ] Voorspelling knockout-fase met eigen puntensysteem
- [ ] Admin-modus (PIN) voor uitslag invoeren apart van gewone gebruikers
- [ ] Export van stand als PDF of CSV
- [ ] Mobiel-responsive verbeteren (kleinere score-inputs)
