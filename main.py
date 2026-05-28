#!/usr/bin/env python3
"""WK Pool 2026 — lokale web-app voor WK-voorspellingen (groepsfase)"""

import os, sys, json, base64, threading, webbrowser, datetime, time
from pathlib import Path
from flask import Flask, request, jsonify, Response

# ─── Paden ──────────────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    APP_DIR = Path(os.path.dirname(os.path.abspath(sys.executable)))
else:
    APP_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

SCHEMA_FILE = APP_DIR / "schema.json"
DATA_FILE   = APP_DIR / "wk_pool_data.dat"
PORT = 5026

# ─── Data beheer ────────────────────────────────────────────────────────────

def _schema() -> dict:
    with open(SCHEMA_FILE, encoding='utf-8') as f:
        return json.load(f)

def _laad() -> dict:
    if not DATA_FILE.exists():
        return {"gebruikers": {}, "uitslagen": {}}
    try:
        raw = DATA_FILE.read_text(encoding='utf-8').strip()
        return json.loads(base64.b64decode(raw.encode()).decode('utf-8'))
    except Exception:
        return {"gebruikers": {}, "uitslagen": {}}

def _sla(d: dict):
    s = json.dumps(d, ensure_ascii=False, separators=(',', ':'))
    DATA_FILE.write_text(base64.b64encode(s.encode()).decode('ascii'), encoding='utf-8')

def _vergrendeld(match: dict) -> bool:
    try:
        dt = datetime.datetime.strptime(f"{match['datum']} {match['tijd']}", "%Y-%m-%d %H:%M")
        return datetime.datetime.now() >= dt
    except Exception:
        return False

def _punten(v: str, u: str) -> int:
    if not v or not u:
        return 0
    try:
        vh, vt = map(int, v.split('-'))
        uh, ut = map(int, u.split('-'))
        if vh == uh and vt == ut:
            return 3
        if (vh > vt) == (uh > ut) and (vh == vt) == (uh == ut):
            return 1
        return 0
    except Exception:
        return 0

def _totaal(naam: str, data: dict, schema: dict) -> dict:
    geb = data.get("gebruikers", {}).get(naam, {})
    uit = data.get("uitslagen", {})
    p = ex = co = inv = tot = 0
    for g in schema.get("groepen", []):
        for m in g.get("wedstrijden", []):
            tot += 1
            mid = m["id"]
            v = geb.get(mid, "")
            u = uit.get(mid, "")
            if v:
                inv += 1
            pts = _punten(v, u)
            if pts == 3:
                ex += 1; p += 3
            elif pts == 1:
                co += 1; p += 1
    bok = 0
    k = geb.get("__kampioen__", "")
    ek = uit.get("__kampioen__", "")
    if k and ek and k == ek:
        bok = 10
    return {"naam": naam, "punten": p + bok, "basis": p, "bonus": bok,
            "exact": ex, "correct": co, "ingevuld": inv, "totaal": tot,
            "kampioen": k}

# ─── Flask ───────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route('/')
def index():
    return Response(HTML_TEMPLATE, mimetype='text/html; charset=utf-8')

@app.route('/api/schema')
def api_schema():
    return jsonify(_schema())

@app.route('/api/data')
def api_data():
    data = _laad()
    schema = _schema()
    verg = {}
    for g in schema.get("groepen", []):
        for m in g.get("wedstrijden", []):
            verg[m["id"]] = _vergrendeld(m)
    return jsonify({**data, "vergrendeld": verg})

@app.route('/api/standings')
def api_standings():
    data = _laad()
    schema = _schema()
    standen = [_totaal(n, data, schema) for n in data.get("gebruikers", {})]
    standen.sort(key=lambda x: (-x["punten"], -x["exact"], -x["correct"]))
    return jsonify(standen)

@app.route('/api/gebruiker', methods=['POST'])
def api_gebruiker():
    naam = (request.json or {}).get("naam", "").strip()
    if not naam:
        return jsonify({"ok": False, "msg": "Naam vereist"}), 400
    data = _laad()
    if naam not in data["gebruikers"]:
        data["gebruikers"][naam] = {}
        _sla(data)
    return jsonify({"ok": True})

@app.route('/api/voorspelling', methods=['POST'])
def api_voorspelling():
    body = request.json or {}
    naam  = body.get("naam", "").strip()
    mid   = body.get("id", "").strip()
    score = body.get("score", "").strip()
    if not naam or not mid:
        return jsonify({"ok": False}), 400
    schema = _schema()
    for g in schema.get("groepen", []):
        for m in g.get("wedstrijden", []):
            if m["id"] == mid and _vergrendeld(m):
                return jsonify({"ok": False, "msg": "Wedstrijd is al begonnen"}), 403
    data = _laad()
    if naam not in data["gebruikers"]:
        data["gebruikers"][naam] = {}
    if score:
        data["gebruikers"][naam][mid] = score
    elif mid in data["gebruikers"].get(naam, {}):
        del data["gebruikers"][naam][mid]
    _sla(data)
    return jsonify({"ok": True})

@app.route('/api/uitslag', methods=['POST'])
def api_uitslag():
    body  = request.json or {}
    mid   = body.get("id", "").strip()
    score = body.get("score", "").strip()
    if not mid:
        return jsonify({"ok": False}), 400
    data = _laad()
    if score:
        data["uitslagen"][mid] = score
    elif mid in data["uitslagen"]:
        del data["uitslagen"][mid]
    _sla(data)
    return jsonify({"ok": True})

@app.route('/api/kampioen', methods=['POST'])
def api_kampioen():
    body = request.json or {}
    naam = body.get("naam", "").strip()
    team = body.get("team", "").strip()
    if not naam:
        return jsonify({"ok": False}), 400
    data = _laad()
    if naam not in data["gebruikers"]:
        data["gebruikers"][naam] = {}
    if team:
        data["gebruikers"][naam]["__kampioen__"] = team
    elif "__kampioen__" in data["gebruikers"].get(naam, {}):
        del data["gebruikers"][naam]["__kampioen__"]
    _sla(data)
    return jsonify({"ok": True})

@app.route('/api/kampioen_echt', methods=['POST'])
def api_kampioen_echt():
    body = request.json or {}
    team = body.get("team", "").strip()
    data = _laad()
    if team:
        data["uitslagen"]["__kampioen__"] = team
    elif "__kampioen__" in data["uitslagen"]:
        del data["uitslagen"]["__kampioen__"]
    _sla(data)
    return jsonify({"ok": True})

# ─── HTML (embedded single-page app) ────────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WK Pool 2026 🏆</title>
<style>
:root {
  --bg:      #0d1117;
  --surf:    #161b22;
  --surf2:   #21262d;
  --surf3:   #2d333b;
  --accent:  #00c896;
  --gold:    #f0b429;
  --text:    #e6edf3;
  --dim:     #8b949e;
  --green:   #3fb950;
  --red:     #f85149;
  --border:  #30363d;
  --shadow:  0 4px 24px rgba(0,0,0,.5);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--text); font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px; min-height: 100vh; }
a { color: var(--accent); }
button { cursor: pointer; border: none; font-family: inherit; }
input, select { font-family: inherit; }

/* ─── Login ─────────────────────────────────────────────────────────── */
#login-screen {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: 100vh; padding: 24px;
}
.login-card {
  background: var(--surf); border: 1px solid var(--border); border-radius: 16px;
  padding: 40px 48px; width: 100%; max-width: 440px; box-shadow: var(--shadow);
}
.login-title { font-size: 28px; font-weight: 700; color: var(--gold); text-align: center; margin-bottom: 4px; }
.login-sub   { color: var(--dim); text-align: center; margin-bottom: 32px; font-size: 13px; }
.login-card label { display: block; color: var(--dim); font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .5px; margin-bottom: 6px; }
.login-card input[type=text] {
  width: 100%; padding: 12px 16px; background: var(--surf2); border: 1px solid var(--border);
  border-radius: 8px; color: var(--text); font-size: 16px; outline: none; transition: border-color .2s;
}
.login-card input[type=text]:focus { border-color: var(--accent); }
.btn-primary {
  width: 100%; margin-top: 16px; padding: 12px; background: var(--accent); color: #000;
  font-size: 15px; font-weight: 700; border-radius: 8px; transition: opacity .2s;
}
.btn-primary:hover { opacity: .85; }
.deelnemers-blok { margin-top: 32px; }
.deelnemers-blok h3 { color: var(--dim); font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .5px; margin-bottom: 10px; }
.deelnemer-rij {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 14px; background: var(--surf2); border-radius: 8px; margin-bottom: 4px;
  cursor: pointer; transition: background .15s;
}
.deelnemer-rij:hover { background: var(--surf3); }
.deelnemer-naam { font-weight: 600; }
.deelnemer-pts  { color: var(--gold); font-weight: 700; }

/* ─── App shell ─────────────────────────────────────────────────────── */
#app { display: none; }
.topbar {
  background: var(--surf); border-bottom: 1px solid var(--border);
  padding: 0 20px; display: flex; align-items: center; gap: 16px; height: 52px;
  position: sticky; top: 0; z-index: 100;
}
.topbar-title { font-size: 18px; font-weight: 700; color: var(--gold); flex: 1; }
.topbar-user  { color: var(--dim); font-size: 13px; }
.btn-logout {
  padding: 6px 14px; background: var(--surf2); border: 1px solid var(--border);
  border-radius: 6px; color: var(--dim); font-size: 12px; transition: color .15s;
}
.btn-logout:hover { color: var(--text); }

/* ─── Tab nav ────────────────────────────────────────────────────────── */
.tab-nav {
  background: var(--surf); border-bottom: 1px solid var(--border);
  display: flex; gap: 2px; padding: 0 16px;
}
.tab-btn {
  padding: 12px 20px; background: transparent; color: var(--dim);
  font-size: 13px; font-weight: 600; border-bottom: 2px solid transparent;
  transition: color .15s, border-color .15s;
}
.tab-btn:hover  { color: var(--text); }
.tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); }

/* ─── Content area ──────────────────────────────────────────────────── */
.tab-content { padding: 20px; }

/* ─── Groep sub-tabs ─────────────────────────────────────────────────── */
.groep-nav {
  display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 20px;
}
.groep-btn {
  padding: 6px 14px; background: var(--surf2); border: 1px solid var(--border);
  border-radius: 20px; color: var(--dim); font-size: 12px; font-weight: 600;
  transition: all .15s;
}
.groep-btn:hover  { border-color: var(--accent); color: var(--text); }
.groep-btn.active { background: var(--accent); border-color: var(--accent); color: #000; }

/* ─── Groep header ────────────────────────────────────────────────────── */
.groep-header { margin-bottom: 12px; }
.groep-naam   { font-size: 18px; font-weight: 700; color: var(--accent); }
.teams-strip  { display: block; color: var(--dim); font-size: 12px; margin-top: 4px; }

/* ─── Match table ────────────────────────────────────────────────────── */
.match-table { display: table; width: 100%; border-collapse: collapse; }
.match-header, .match-row { display: table-row; }
.match-header > span, .match-row > span { display: table-cell; padding: 8px 10px; vertical-align: middle; }
.match-header > span { color: var(--dim); font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .4px; border-bottom: 1px solid var(--border); }
.match-row { border-bottom: 1px solid var(--border); transition: background .1s; }
.match-row:hover { background: var(--surf2); }
.match-row.locked { opacity: .7; }
.col-datum { width: 90px; color: var(--dim); font-size: 12px; }
.col-teams { width: auto; }
.team      { font-weight: 600; }
.team.thuis { text-align: right; }
.vs        { color: var(--dim); font-size: 11px; padding: 0 8px; }
.teams-cell { display: flex; align-items: center; }
.col-voorsp { width: 120px; }
.col-uitslag { width: 80px; color: var(--dim); text-align: center; }
.col-pts    { width: 60px; font-weight: 700; text-align: center; }
.pts-green  { color: var(--gold); }
.pts-ok     { color: var(--green); }
.pts-fout   { color: var(--red); }

/* ─── Score input ─────────────────────────────────────────────────────── */
.score-input {
  width: 72px; padding: 5px 8px; background: var(--surf2); border: 1px solid var(--border);
  border-radius: 6px; color: var(--accent); font-size: 14px; font-weight: 700;
  text-align: center; outline: none; transition: border-color .15s;
}
.score-input:focus { border-color: var(--accent); }
.score-input.invalid { border-color: var(--red); color: var(--red); }
.locked-val { color: var(--dim); font-size: 13px; }
.lock-icon  { margin-left: 4px; font-size: 11px; }

/* ─── Bonus card ─────────────────────────────────────────────────────── */
.bonus-card {
  max-width: 560px; background: var(--surf); border: 1px solid var(--border);
  border-radius: 12px; padding: 28px 32px;
}
.bonus-card h2 { font-size: 20px; color: var(--gold); margin-bottom: 6px; }
.bonus-card .sub { color: var(--dim); margin-bottom: 28px; font-size: 13px; }
.bonus-row { display: flex; align-items: center; gap: 16px; margin-bottom: 24px; }
.bonus-row label { color: var(--dim); font-weight: 600; font-size: 13px; min-width: 140px; }
.bonus-row select {
  padding: 8px 12px; background: var(--surf2); border: 1px solid var(--border);
  border-radius: 8px; color: var(--text); font-size: 14px; outline: none; cursor: pointer;
}
.bonus-row select:focus { border-color: var(--accent); }
.pts-badge { font-weight: 700; font-size: 16px; }
.pts-badge.green { color: var(--green); }

.punten-tabel { margin-top: 8px; }
.punten-tabel h3 { color: var(--dim); font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .4px; margin-bottom: 12px; }
.punten-rij { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 13px; }
.punten-rij:last-child { border-bottom: none; }
.punten-rij span { color: var(--dim); }
.punten-rij strong { font-weight: 700; }
.gold  { color: var(--gold); }
.groen { color: var(--green); }
.dim   { color: var(--dim); }

/* ─── Stand ──────────────────────────────────────────────────────────── */
.stand-container { max-width: 700px; }
.stand-title { font-size: 22px; font-weight: 700; margin-bottom: 20px; }
.stand-table { width: 100%; border-collapse: collapse; }
.stand-table th {
  text-align: left; padding: 10px 14px; color: var(--dim);
  font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .4px;
  border-bottom: 1px solid var(--border);
}
.stand-table td { padding: 12px 14px; border-bottom: 1px solid var(--border); }
.stand-table tr.me { background: rgba(0,200,150,.06); }
.stand-table tr.me .naam-cel { color: var(--accent); font-weight: 700; }
.stand-table tr:hover { background: var(--surf2); }
.pts-cel { font-size: 18px; font-weight: 700; }
.medal { font-size: 20px; }
.geen-data { color: var(--dim); padding: 40px 0; text-align: center; }

/* ─── Uitslagen tab ──────────────────────────────────────────────────── */
.uitslag-header { margin-bottom: 16px; }
.uitslag-header h2 { font-size: 18px; font-weight: 700; margin-bottom: 4px; }
.uitslag-header p  { color: var(--dim); font-size: 13px; }
.uitslag-groep-blok { margin-bottom: 32px; }
.uitslag-groep-blok h3 { color: var(--accent); font-size: 15px; font-weight: 700; margin-bottom: 10px; padding-bottom: 6px; border-bottom: 1px solid var(--border); }
.uitslag-rij {
  display: flex; align-items: center; gap: 12px; padding: 8px 0;
  border-bottom: 1px solid var(--border);
}
.uitslag-rij:last-child { border-bottom: none; }
.uitslag-teams { flex: 1; display: flex; align-items: center; gap: 6px; }
.uitslag-teams .thuis { font-weight: 600; text-align: right; min-width: 120px; }
.uitslag-teams .uit   { font-weight: 600; min-width: 120px; }
.uitslag-datum { color: var(--dim); font-size: 12px; min-width: 90px; }
.uitslag-input {
  width: 72px; padding: 5px 8px; background: var(--surf2); border: 1px solid var(--border);
  border-radius: 6px; color: var(--green); font-size: 14px; font-weight: 700;
  text-align: center; outline: none; transition: border-color .15s;
}
.uitslag-input:focus { border-color: var(--green); }
.uitslag-input.invalid { border-color: var(--red); }
.opgeslagen { color: var(--green); font-size: 16px; opacity: 0; transition: opacity .3s; }
.opgeslagen.show { opacity: 1; }

/* ─── Kampioen echt ──────────────────────────────────────────────────── */
.kampioen-echt-blok {
  background: var(--surf); border: 1px solid var(--border); border-radius: 10px;
  padding: 20px 24px; margin-bottom: 28px; display: flex; align-items: center; gap: 16px;
}
.kampioen-echt-blok label { color: var(--gold); font-weight: 700; white-space: nowrap; }
.kampioen-echt-blok select {
  padding: 8px 12px; background: var(--surf2); border: 1px solid var(--border);
  border-radius: 8px; color: var(--text); font-size: 14px; cursor: pointer; outline: none;
}

/* ─── Responsive ─────────────────────────────────────────────────────── */
@media(max-width:600px) {
  .login-card { padding: 28px 20px; }
  .tab-btn { padding: 10px 12px; font-size: 12px; }
  .match-table { font-size: 12px; }
  .col-datum { display: none; }
  .bonus-card { padding: 20px; }
}
</style>
</head>
<body>

<!-- ──────────────── LOGIN ──────────────────────────────────────────── -->
<div id="login-screen">
  <div class="login-card">
    <div class="login-title">🏆 WK Pool 2026</div>
    <div class="login-sub">FIFA WK • VS / Canada / Mexico • 11 jun – 19 jul 2026</div>

    <label for="naam-input">Jouw naam</label>
    <input type="text" id="naam-input" placeholder="Typ je naam…" maxlength="32"
           onkeydown="if(event.key==='Enter')login()">
    <button class="btn-primary" onclick="login()">Inloggen →</button>

    <div class="deelnemers-blok" id="deelnemers-blok"></div>
  </div>
</div>

<!-- ──────────────── MAIN APP ───────────────────────────────────────── -->
<div id="app">
  <div class="topbar">
    <span class="topbar-title">🏆 WK Pool 2026</span>
    <span class="topbar-user">👤 <span id="topbar-naam"></span></span>
    <button class="btn-logout" onclick="logout()">Uitloggen</button>
  </div>

  <div class="tab-nav">
    <button class="tab-btn active" data-tab="voorspellingen" onclick="showTab('voorspellingen')">📋 Mijn Voorspellingen</button>
    <button class="tab-btn"       data-tab="stand"          onclick="showTab('stand')">🏅 Stand</button>
    <button class="tab-btn"       data-tab="uitslagen"      onclick="showTab('uitslagen')">⚽ Uitslagen invoeren</button>
  </div>

  <!-- Voorspellingen -->
  <div id="tab-voorspellingen" class="tab-content">
    <div class="groep-nav" id="groep-nav"></div>
    <div id="groep-content"></div>
  </div>

  <!-- Stand -->
  <div id="tab-stand" class="tab-content" style="display:none"></div>

  <!-- Uitslagen -->
  <div id="tab-uitslagen" class="tab-content" style="display:none"></div>
</div>

<script>
// ── State ──────────────────────────────────────────────────────────────────
let currentUser = null;
let schema = null;
let poolData = null;
let currentTab = 'voorspellingen';
let currentGroep = 'bonus';

// ── Init ───────────────────────────────────────────────────────────────────
window.onload = async () => {
  await loadAll();
  const saved = localStorage.getItem('wkpool_user');
  if (saved && poolData.gebruikers && poolData.gebruikers[saved] !== undefined) {
    currentUser = saved;
    showApp();
  } else {
    showLogin();
  }
  setInterval(async () => {
    await loadAll();
    if (currentTab === 'stand') renderStand();
    if (currentTab === 'uitslagen') renderUitslagen();
  }, 30000);
};

async function loadAll() {
  const [s, d] = await Promise.all([fetch('/api/schema'), fetch('/api/data')]);
  schema   = await s.json();
  poolData = await d.json();
}

// ── Login / logout ─────────────────────────────────────────────────────────
function showLogin() {
  document.getElementById('login-screen').style.display = '';
  document.getElementById('app').style.display = 'none';
  renderDeelnemers();
}

function showApp() {
  document.getElementById('login-screen').style.display = 'none';
  document.getElementById('app').style.display = '';
  document.getElementById('topbar-naam').textContent = currentUser;
  showTab(currentTab);
}

async function login() {
  const naam = document.getElementById('naam-input').value.trim();
  if (!naam) return;
  await post('/api/gebruiker', {naam});
  await loadAll();
  currentUser = naam;
  localStorage.setItem('wkpool_user', naam);
  showApp();
}

async function logout() {
  currentUser = null;
  localStorage.removeItem('wkpool_user');
  await loadAll();
  showLogin();
}

async function renderDeelnemers() {
  const r = await fetch('/api/standings');
  const stand = await r.json();
  const blok = document.getElementById('deelnemers-blok');
  if (!stand.length) { blok.innerHTML = ''; return; }

  const medals = ['🥇','🥈','🥉'];
  let html = '<div class="deelnemers-blok"><h3>Huidige deelnemers</h3>';
  stand.forEach((s, i) => {
    html += `<div class="deelnemer-rij" onclick="snel('${esc(s.naam)}')">
      <span class="deelnemer-naam">${medals[i] || (i+1)+'.'}  ${esc(s.naam)}</span>
      <span class="deelnemer-pts">${s.punten} pts</span>
    </div>`;
  });
  html += '</div>';
  blok.innerHTML = html;
}

function snel(naam) {
  document.getElementById('naam-input').value = naam;
  login();
}

// ── Tabs ───────────────────────────────────────────────────────────────────
function showTab(tab) {
  currentTab = tab;
  document.querySelectorAll('.tab-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.tab === tab));
  ['voorspellingen','stand','uitslagen'].forEach(t => {
    document.getElementById('tab-'+t).style.display = t === tab ? '' : 'none';
  });
  if (tab === 'voorspellingen') renderVoorspellingen();
  if (tab === 'stand')          renderStand();
  if (tab === 'uitslagen')      renderUitslagen();
}

// ── Voorspellingen ─────────────────────────────────────────────────────────
function renderVoorspellingen() {
  const nav = document.getElementById('groep-nav');
  nav.innerHTML = '';

  const mkBtn = (id, label) => {
    const b = document.createElement('button');
    b.className = 'groep-btn' + (currentGroep === id ? ' active' : '');
    b.dataset.groep = id;
    b.textContent = label;
    b.onclick = () => { currentGroep = id; renderVoorspellingen(); };
    nav.appendChild(b);
  };

  mkBtn('bonus', '⭐ Bonus');
  schema.groepen.forEach(g => mkBtn(g.naam.replace('Groep ',''), g.naam));
  renderGroepContent();
}

function renderGroepContent() {
  if (currentGroep === 'bonus') { renderBonus(); return; }
  const groep = schema.groepen.find(g => g.naam.includes('Groep ' + currentGroep));
  if (!groep) return;

  const geb  = (poolData.gebruikers || {})[currentUser] || {};
  const uit  = poolData.uitslagen  || {};
  const verg = poolData.vergrendeld || {};

  let html = `
    <div class="groep-header">
      <span class="groep-naam">${groep.naam}</span>
      <span class="teams-strip">${groep.teams.join(' &nbsp;·&nbsp; ')}</span>
    </div>
    <div class="match-table">
      <div class="match-header">
        <span class="col-datum">Datum</span>
        <span class="col-teams">Wedstrijd</span>
        <span class="col-voorsp">Jouw score</span>
        <span class="col-uitslag">Uitslag</span>
        <span class="col-pts">Pts</span>
      </div>`;

  groep.wedstrijden.forEach(m => {
    const locked = verg[m.id];
    const v = geb[m.id] || '';
    const u = uit[m.id] || '';
    const pts = calcPts(v, u);
    const datum = fmtDatum(m.datum, m.tijd);

    let ptsHtml = '—';
    let ptsCls = '';
    if (u) {
      ptsHtml = pts > 0 ? '+'+pts : '0';
      ptsCls  = pts===3 ? 'pts-green' : pts===1 ? 'pts-ok' : 'pts-fout';
    }

    let voorspHtml;
    if (locked) {
      voorspHtml = `<span class="locked-val">${v || '—'}<span class="lock-icon">🔒</span></span>`;
    } else {
      voorspHtml = `<input type="text" class="score-input" id="si-${m.id}"
        value="${v}" placeholder="2-1" maxlength="5"
        oninput="validateInput(this)"
        onchange="saveVoorsp('${m.id}',this.value)"
        onkeydown="if(event.key==='Enter')this.blur()">`;
    }

    html += `
      <div class="match-row ${locked?'locked':''}">
        <span class="col-datum">${datum}</span>
        <span class="col-teams">
          <span class="teams-cell">
            <span class="team thuis" style="min-width:120px;text-align:right">${esc(m.thuis)}</span>
            <span class="vs">vs</span>
            <span class="team uit">${esc(m.uit)}</span>
          </span>
        </span>
        <span class="col-voorsp">${voorspHtml}</span>
        <span class="col-uitslag">${u || '—'}</span>
        <span class="col-pts ${ptsCls}">${ptsHtml}</span>
      </div>`;
  });

  html += '</div>';
  document.getElementById('groep-content').innerHTML = html;
}

function renderBonus() {
  const geb  = (poolData.gebruikers || {})[currentUser] || {};
  const uit  = poolData.uitslagen  || {};
  const hk   = geb['__kampioen__'] || '';
  const ek   = uit['__kampioen__'] || '';
  const juist = hk && ek && hk === ek;

  const teams = schema.groepen.flatMap(g => g.teams).sort((a,b) => a.localeCompare(b,'nl'));
  const opties = teams.map(t => `<option value="${esc(t)}" ${t===hk?'selected':''}>${esc(t)}</option>`).join('');

  document.getElementById('groep-content').innerHTML = `
    <div class="bonus-card">
      <h2>⭐ Bonusvoorspelling</h2>
      <p class="sub">Raad de wereldkampioen — correcte keuze = <strong>10 bonus punten</strong></p>
      <div class="bonus-row">
        <label>🏆 Wereldkampioen:</label>
        <select onchange="saveKampioen(this.value)">
          <option value="">— selecteer —</option>
          ${opties}
        </select>
        ${juist ? '<span class="pts-badge green">+10 ✓</span>' : ''}
      </div>
      <div class="punten-tabel">
        <h3>Puntensysteem</h3>
        <div class="punten-rij"><span>⚽ Exacte score (bijv. 2-1):</span><strong class="gold">3 punten</strong></div>
        <div class="punten-rij"><span>✅ Juiste uitslag (W / G / V):</span><strong class="groen">1 punt</strong></div>
        <div class="punten-rij"><span>❌ Fout:</span><strong class="dim">0 punten</strong></div>
        <div class="punten-rij"><span>⭐ Juiste wereldkampioen:</span><strong class="gold">10 bonus punten</strong></div>
      </div>
    </div>`;
}

// ── Stand ──────────────────────────────────────────────────────────────────
async function renderStand() {
  const r = await fetch('/api/standings');
  const stand = await r.json();
  const medals = ['🥇','🥈','🥉'];
  const container = document.getElementById('tab-stand');

  if (!stand.length) {
    container.innerHTML = '<p class="geen-data">Nog geen deelnemers.</p>';
    return;
  }

  let html = '<div class="stand-container"><h2 class="stand-title">🏅 Klassement</h2>';
  html += `<table class="stand-table">
    <tr>
      <th>#</th><th>Naam</th><th>Punten</th>
      <th>Exact</th><th>Correct</th><th>Kampioen</th><th>Ingevuld</th>
    </tr>`;

  stand.forEach((s, i) => {
    const me = s.naam === currentUser;
    const bns = s.bonus > 0 ? `<span style="color:var(--gold);font-size:11px"> +${s.bonus}⭐</span>` : '';
    html += `<tr class="${me?'me':''}">
      <td class="medal">${medals[i] || (i+1)}</td>
      <td class="naam-cel">${esc(s.naam)}</td>
      <td class="pts-cel gold">${s.punten}${bns}</td>
      <td class="green">${s.exact}</td>
      <td>${s.correct}</td>
      <td class="dim">${s.kampioen ? esc(s.kampioen) : '—'}</td>
      <td class="dim">${s.ingevuld}/${s.totaal}</td>
    </tr>`;
  });
  html += '</table></div>';
  container.innerHTML = html;
}

// ── Uitslagen ─────────────────────────────────────────────────────────────
function renderUitslagen() {
  const uit  = poolData.uitslagen  || {};
  const teams = schema.groepen.flatMap(g => g.teams).sort((a,b) => a.localeCompare(b,'nl'));
  const opties = teams.map(t => `<option value="${esc(t)}" ${t===uit['__kampioen__']?'selected':''}>${esc(t)}</option>`).join('');

  let html = `
    <div class="uitslag-header">
      <h2>⚽ Uitslagen invoeren</h2>
      <p>Iedereen kan uitslagen invoeren. Na invoer worden punten automatisch berekend.</p>
    </div>
    <div class="kampioen-echt-blok">
      <label>🏆 Echte wereldkampioen:</label>
      <select onchange="saveKampioEcht(this.value)">
        <option value="">— nog niet bekend —</option>
        ${opties}
      </select>
    </div>`;

  schema.groepen.forEach(g => {
    html += `<div class="uitslag-groep-blok"><h3>${g.naam}</h3>`;
    g.wedstrijden.forEach(m => {
      const u = uit[m.id] || '';
      const datum = fmtDatum(m.datum, m.tijd);
      html += `
        <div class="uitslag-rij">
          <span class="uitslag-datum">${datum}</span>
          <span class="uitslag-teams">
            <span class="thuis">${esc(m.thuis)}</span>
            <span class="vs">vs</span>
            <span class="uit">${esc(m.uit)}</span>
          </span>
          <input type="text" class="uitslag-input" id="ui-${m.id}"
            value="${u}" placeholder="2-1" maxlength="5"
            oninput="validateInput(this,'uitslag-input')"
            onchange="saveUitslag('${m.id}',this.value)"
            onkeydown="if(event.key==='Enter')this.blur()">
          <span class="opgeslagen" id="ops-${m.id}">✓</span>
        </div>`;
    });
    html += '</div>';
  });

  document.getElementById('tab-uitslagen').innerHTML = html;
}

// ── API calls ─────────────────────────────────────────────────────────────
async function saveVoorsp(mid, score) {
  score = score.trim();
  if (score && !geldig(score)) return;
  await post('/api/voorspelling', {naam: currentUser, id: mid, score});
  await loadAll();
  renderGroepContent();
}

async function saveKampioen(team) {
  await post('/api/kampioen', {naam: currentUser, team});
  await loadAll();
  renderBonus();
}

async function saveUitslag(mid, score) {
  score = score.trim();
  if (score && !geldig(score)) return;
  await post('/api/uitslag', {id: mid, score});
  await loadAll();
  const el = document.getElementById('ops-'+mid);
  if (el) { el.classList.add('show'); setTimeout(() => el.classList.remove('show'), 2000); }
}

async function saveKampioEcht(team) {
  await post('/api/kampioen_echt', {team});
  await loadAll();
}

async function post(url, data) {
  return fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(data)});
}

// ── Helpers ────────────────────────────────────────────────────────────────
function calcPts(v, u) {
  if (!v || !u) return 0;
  const parts = s => s.split('-').map(Number);
  const [vh,vt] = parts(v); const [uh,ut] = parts(u);
  if (isNaN(vh)||isNaN(vt)||isNaN(uh)||isNaN(ut)) return 0;
  if (vh===uh && vt===ut) return 3;
  if ((vh>vt)===(uh>ut) && (vh===vt)===(uh===ut)) return 1;
  return 0;
}

function geldig(s) { return /^\d{1,2}-\d{1,2}$/.test(s); }

function validateInput(el, cls) {
  cls = cls || 'score-input';
  const v = el.value.trim();
  el.classList.toggle('invalid', v.length > 0 && !geldig(v));
}

function fmtDatum(datum, tijd) {
  const mnd = ['jan','feb','mrt','apr','mei','jun','jul','aug','sep','okt','nov','dec'];
  const d = new Date(datum + 'T00:00:00');
  return `${d.getDate()} ${mnd[d.getMonth()]}<br><small style="color:var(--dim)">${tijd} CEST</small>`;
}

function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
</script>
</body>
</html>"""

# ─── Startup ─────────────────────────────────────────────────────────────────

def _start_flask():
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='127.0.0.1', port=PORT, debug=False, use_reloader=False)


def main():
    if not SCHEMA_FILE.exists():
        try:
            import tkinter as tk
            from tkinter import messagebox
            r = tk.Tk(); r.withdraw()
            messagebox.showerror("WK Pool 2026",
                f"schema.json niet gevonden!\n\nPlaats schema.json in dezelfde map als dit programma:\n{APP_DIR}")
            r.destroy()
        except Exception:
            print(f"FOUT: schema.json niet gevonden in {APP_DIR}")
        return

    flask_thread = threading.Thread(target=_start_flask, daemon=True)
    flask_thread.start()
    time.sleep(1.2)
    webbrowser.open(f'http://localhost:{PORT}')

    try:
        import tkinter as tk
        root = tk.Tk()
        root.title("WK Pool 2026")
        root.geometry("340x140")
        root.configure(bg='#0d1117')
        root.resizable(False, False)

        try:
            root.iconbitmap(default='')
        except Exception:
            pass

        tk.Label(root, text="🏆  WK Pool 2026", bg='#0d1117', fg='#f0b429',
                 font=('Segoe UI', 17, 'bold')).pack(pady=(18, 4))
        tk.Label(root, text=f"Server actief  •  localhost:{PORT}",
                 bg='#0d1117', fg='#8b949e', font=('Segoe UI', 9)).pack()

        f = tk.Frame(root, bg='#0d1117')
        f.pack(pady=12, padx=24, fill='x')

        tk.Button(f, text="🌐  Open Browser",
                  bg='#00c896', fg='#000', font=('Segoe UI', 10, 'bold'),
                  relief='flat', padx=10, pady=6, cursor='hand2',
                  command=lambda: webbrowser.open(f'http://localhost:{PORT}')
                  ).pack(side='left', fill='x', expand=True, padx=(0, 6))

        tk.Button(f, text="Sluiten",
                  bg='#21262d', fg='#8b949e', font=('Segoe UI', 10),
                  relief='flat', padx=10, pady=6, cursor='hand2',
                  command=root.destroy
                  ).pack(side='left')

        root.mainloop()

    except ImportError:
        print(f"WK Pool 2026 draait op http://localhost:{PORT}")
        print("Druk CTRL+C om te stoppen.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
