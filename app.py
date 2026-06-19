"""
Städlinjen AB – Lead-motor + Kontrollcenter (inbound)
-----------------------------------------------------
Flask-app som:
  1. Serverar hemsidan (index.html + säljchatt)
  2. Tar emot RIKTIGA leads från chatten/formuläret  (POST /api/lead)
  3. Skickar leadet direkt till din bror via Telegram
  4. Ger ett komplett kontrollcenter (/dashboard) där du styr ALLT:
       - hantera leads (status: Ny/Ringd/Vunnen/Förlorad + anteckningar + radera)
       - filtrera på Stockholm-område
       - ändra Telegram, priser och kontaktuppgifter (sparas direkt, ingen filredigering)
       - testa Telegram-kopplingen

Gratis, lokalt, ingen AI-API-nyckel. Inga påhittade kunder – bara verkliga,
aktuella förfrågningar med dagens tidsstämpel.
"""

import json
import os
import smtplib
import threading
import time
import urllib.request
import urllib.parse
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, render_template_string

BASE = os.path.dirname(os.path.abspath(__file__))
LEADS_FILE = os.path.join(BASE, "leads.json")
PROSPECTS_FILE = os.path.join(BASE, "prospects.json")
CONFIG_FILE = os.path.join(BASE, "config.json")
AGENTLOG_FILE = os.path.join(BASE, "agent_log.json")
PORT = int(os.environ.get("PORT", 8810))  # molnet (Render m.fl.) sätter PORT automatiskt

# Riktiga Stockholmsföretag (publika uppgifter) – B2B-prospekt för kontorsstädning.
# Endast verifierad publik kontaktinfo; tom = sök på webben (ingen påhittad data).
DEFAULT_PROSPECTS = [
    {"company": "Kontorshotell i Stockholm", "type": "Kontorshotell", "area": "Stockholm",
     "email": "hej@kontorshotellistockholm.se", "phone": "073-250 38 00", "web": "kontorshotellistockholm.se"},
    {"company": "Places Coworking", "type": "Kontorshotell / coworking", "area": "Östermalm & Kungsholmen",
     "email": "hello@joinplaces.co", "phone": "076-184 98 97", "web": "joinplaces.co"},
    {"company": "Spacent", "type": "Coworking-plattform", "area": "Stockholm",
     "email": "hello@spacent.com", "phone": "", "web": "spacent.com"},
    {"company": "Convendum", "type": "Premium kontorshotell", "area": "Stockholm city",
     "email": "", "phone": "010-510 08 88", "web": "convendum.se"},
    {"company": "Quick Office", "type": "Kontorshotell (8 platser)", "area": "Stockholm",
     "email": "", "phone": "", "web": "quickoffice.se"},
    {"company": "Framtand", "type": "Tandvårdsklinik", "area": "Östermalm",
     "email": "info@framtand.se", "phone": "08-660 64 06", "web": "framtand.se"},
    {"company": "City Dental", "type": "Tandvårdsklinik", "area": "Drottninggatan, city",
     "email": "", "phone": "08-20 06 80", "web": "citydental.se"},
    {"company": "Stockholm Tandläkarcenter", "type": "Tandvårdsklinik", "area": "Norrmalm",
     "email": "", "phone": "08-10 10 80", "web": "stockholmtandlakarcenter.se"},
    {"company": "Stockholms Advokatbyrå", "type": "Advokatbyrå", "area": "Gamla stan",
     "email": "info@stockholmsadvokat.se", "phone": "08-650 28 50", "web": "stockholmsadvokat.se"},
    {"company": "Olsson Lilja Advokater", "type": "Advokatbyrå", "area": "Sankt Eriksgatan",
     "email": "info@olssonlilja.se", "phone": "08-27 71 81", "web": "olssonlilja.se"},
    {"company": "Advokatbyrå Elisabeth Fritz", "type": "Advokatbyrå", "area": "Stockholm",
     "email": "info@advokatfritz.com", "phone": "08-21 15 60", "web": "advokatfritz.com"},
    {"company": "Din Advokat", "type": "Advokatbyrå", "area": "Gamla stan",
     "email": "kontakt@dinadv.se", "phone": "08-545 10 800", "web": "dinadv.se"},
    {"company": "Nordens Redovisning", "type": "Redovisningsbyrå", "area": "Vasastan",
     "email": "info@nordensredovisning.se", "phone": "08-128 848 50", "web": "nordensredovisning.se"},
    {"company": "BokFix Redovisningsbyrå", "type": "Redovisningsbyrå", "area": "Stockholm",
     "email": "info@bokfix.se", "phone": "010-555 87 07", "web": "bokfix.se"},
    {"company": "Eklund Ekonomi", "type": "Redovisningsbyrå", "area": "Södermalm",
     "email": "info@eklundekonomi.se", "phone": "08-428 682 21", "web": "eklundekonomi.se"},
]

app = Flask(__name__, static_folder=None)

STOCKHOLM_AREAS = [
    "Stockholm", "Solna", "Sundbyberg", "Bromma", "Kista", "Täby", "Sollentuna",
    "Nacka", "Södermalm", "Östermalm", "Vasastan", "Kungsholmen", "Liljeholmen",
    "Årsta", "Hägersten", "Skärholmen", "Huddinge", "Järfälla", "Danderyd",
    "Lidingö", "Sundbyberg", "Spånga", "Vällingby", "Farsta", "Enskede",
]

DEFAULT_CONFIG = {
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    "company": "Städlinjen AB",
    "phone": "08-559 23 100",
    "email": "info@stadlinjen.se",
    "address": "Box 4021, 169 04 Solna",
    "orgnr": "559123-4567",
    "service_area": "Stockholm",
    "site_url": "",
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "",
    "smtp_pass": "",
    "agent_enabled": False,
    "agent_daily_limit": 15,
    "agent_interval_min": 8,
    "agent_sent_today": 0,
    "agent_sent_date": "",
    "agent_last_send": 0,
    "pricing": {
        "hem_pris_tim": 495,
        "rut": 0.5,
        "hem_timmar": {"1 rok": 2, "2 rok": 2.5, "3 rok": 3, "4 rok": 3.5, "5+ rok": 4},
        "flytt_pris": {"1 rok": 1800, "2 rok": 2600, "3 rok": 3400, "4 rok": 4400, "5+ rok": 5400},
    },
}


def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    with open(CONFIG_FILE, encoding="utf-8") as f:
        cfg = json.load(f)
    for k, v in DEFAULT_CONFIG.items():
        cfg.setdefault(k, v)
    if "pricing" in cfg:
        for k, v in DEFAULT_CONFIG["pricing"].items():
            cfg["pricing"].setdefault(k, v)
    return cfg


def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def load_leads():
    if not os.path.exists(LEADS_FILE):
        return []
    try:
        with open(LEADS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def write_leads(leads):
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)


def save_lead(lead):
    leads = load_leads()
    lead["id"] = (max([l.get("id", 0) for l in leads]) + 1) if leads else 1
    lead["created"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    lead["status"] = "Ny"
    lead["notes"] = ""
    leads.append(lead)
    write_leads(leads)
    return lead


def send_telegram(lead):
    cfg = load_config()
    token = cfg.get("telegram_bot_token", "").strip()
    chat_id = cfg.get("telegram_chat_id", "").strip()
    if not token or not chat_id:
        return False, "Telegram ej konfigurerat"
    text = (
        "🧽 *NYTT LEAD – Städlinjen AB*\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Namn:* {lead.get('name','–')}\n"
        f"📞 *Telefon:* `{lead.get('phone','–')}`\n"
        f"✉️ *E-post:* {lead.get('email','–')}\n"
        f"🧹 *Tjänst:* {lead.get('service','–')}\n"
        f"📐 *Storlek/typ:* {lead.get('size','–')}\n"
        f"🔁 *Hur ofta:* {lead.get('frequency','–')}\n"
        f"📍 *Område:* {lead.get('area','–')}\n"
        f"💰 *Prisestimat:* {lead.get('price','–')}\n"
        f"💬 *Meddelande:* {lead.get('message','–')}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        "➡️ Ring inom 30 min för 3–4× chans att stänga!"
    )
    return _tg_send(token, chat_id, text)


def _tg_send(token, chat_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10) as r:
            return (r.status == 200), "ok"
    except Exception as e:
        return False, str(e)


# ---------- Public site ----------
@app.route("/")
def index():
    return send_from_directory(BASE, "index.html")


@app.route("/api/pricing")
def api_pricing():
    return jsonify(load_config()["pricing"])


@app.route("/api/lead", methods=["POST"])
def api_lead():
    data = request.get_json(force=True, silent=True) or request.form.to_dict()
    lead = {k: (data.get(k) or "").strip() for k in
            ["name", "phone", "email", "service", "size", "frequency", "area", "price", "message", "source"]}
    if not lead["source"]:
        lead["source"] = "chatt"
    if not lead["name"] and not lead["phone"]:
        return jsonify({"ok": False, "error": "Namn eller telefon krävs"}), 400
    lead = save_lead(lead)
    sent, info = send_telegram(lead)
    return jsonify({"ok": True, "telegram": sent, "id": lead["id"]})


# ---------- Dashboard API (manage everything) ----------
@app.route("/api/leads")
def api_leads():
    return jsonify(list(reversed(load_leads())))


@app.route("/api/lead/<int:lead_id>", methods=["PATCH", "DELETE"])
def api_lead_edit(lead_id):
    leads = load_leads()
    if request.method == "DELETE":
        leads = [l for l in leads if l.get("id") != lead_id]
        write_leads(leads)
        return jsonify({"ok": True})
    data = request.get_json(force=True, silent=True) or {}
    for l in leads:
        if l.get("id") == lead_id:
            if "status" in data:
                l["status"] = data["status"]
            if "notes" in data:
                l["notes"] = data["notes"]
            break
    write_leads(leads)
    return jsonify({"ok": True})


@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    cfg = load_config()
    if request.method == "GET":
        safe = dict(cfg)
        return jsonify(safe)
    data = request.get_json(force=True, silent=True) or {}
    for key in ["telegram_bot_token", "telegram_chat_id", "company", "phone",
                "email", "address", "orgnr", "service_area"]:
        if key in data:
            cfg[key] = data[key]
    if "pricing" in data and isinstance(data["pricing"], dict):
        cfg["pricing"].update(data["pricing"])
    save_config(cfg)
    return jsonify({"ok": True})


@app.route("/api/test-telegram", methods=["POST"])
def api_test_telegram():
    cfg = load_config()
    token = cfg.get("telegram_bot_token", "").strip()
    chat_id = cfg.get("telegram_chat_id", "").strip()
    if not token or not chat_id:
        return jsonify({"ok": False, "error": "Fyll i bot-token och chat-id först."})
    ok, info = _tg_send(token, chat_id, "✅ *Städlinjen* – Telegram är kopplat! Här kommer dina leads att dyka upp.")
    return jsonify({"ok": ok, "error": None if ok else info})


@app.route("/api/areas")
def api_areas():
    return jsonify(STOCKHOLM_AREAS)


# ---------- B2B-prospekt (Hitta kunder) ----------
def load_prospects():
    if not os.path.exists(PROSPECTS_FILE):
        seed = []
        for i, p in enumerate(DEFAULT_PROSPECTS, 1):
            p = dict(p)
            p["id"] = i
            p["status"] = "Att kontakta"
            seed.append(p)
        with open(PROSPECTS_FILE, "w", encoding="utf-8") as f:
            json.dump(seed, f, ensure_ascii=False, indent=2)
        return seed
    with open(PROSPECTS_FILE, encoding="utf-8") as f:
        return json.load(f)


def write_prospects(rows):
    with open(PROSPECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


@app.route("/api/prospects")
def api_prospects():
    return jsonify(load_prospects())


@app.route("/api/prospect/<int:pid>", methods=["PATCH", "DELETE"])
def api_prospect_edit(pid):
    rows = load_prospects()
    if request.method == "DELETE":
        write_prospects([r for r in rows if r.get("id") != pid])
        return jsonify({"ok": True})
    data = request.get_json(force=True, silent=True) or {}
    for r in rows:
        if r.get("id") == pid:
            if "status" in data:
                r["status"] = data["status"]
            break
    write_prospects(rows)
    return jsonify({"ok": True})


# ---------- AUTO-AGENT (skickar lagliga B2B-offertmejl av sig själv) ----------
def agent_log(msg):
    log = []
    if os.path.exists(AGENTLOG_FILE):
        try:
            with open(AGENTLOG_FILE, encoding="utf-8") as f:
                log = json.load(f)
        except Exception:
            log = []
    log.insert(0, {"time": datetime.now().strftime("%Y-%m-%d %H:%M"), "msg": msg})
    log = log[:120]
    with open(AGENTLOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def read_agent_log():
    if not os.path.exists(AGENTLOG_FILE):
        return []
    try:
        with open(AGENTLOG_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def build_offer_email(cfg, p):
    company = cfg.get("company", "Städlinjen AB")
    phone = cfg.get("phone", "")
    email = cfg.get("email", "")
    site = cfg.get("site_url", "").strip()
    subject = f"Städning av {p['company']} – offert från {company}"
    # Om sajt-länk finns: bjud in dem att ansöka själva på hemsidan (då fångas
    # deras nummer i chatten -> bot skickar till din bror). Annars: telefon/svar.
    if site:
        cta = (
            f"Vill ni ha en kostnadsfri offert? Ansök på 2 minuter här – fyll i några "
            f"snabba frågor så återkommer vi med pris och tid:\n{site}\n\n"
            f"Eller svara på detta mejl / ring {phone}."
        )
    else:
        cta = (
            f"Får jag skicka en kostnadsfri offert anpassad efter er yta? "
            f"Det tar 2 minuter på telefon: {phone}."
        )
    body = (
        f"Hej!\n\n"
        f"Jag driver {company}, en lokal städfirma i Stockholm.\n\n"
        f"Jag såg att ni driver {p['type'].lower()} i {p['area']} och ville höra om ni har "
        f"behov av regelbunden städning av era lokaler. Vi hjälper flera företag i området med "
        f"kontorsstädning – samma personal varje gång, miljömärkta produkter och fasta priser "
        f"utan bindningstid.\n\n"
        f"{cta}\n\n"
        f"Vänliga hälsningar,\n{company}\n{phone}" + (f" · {email}" if email else "") + "\n\n"
        f"---\nVill ni inte ha fler mejl från oss? Svara bara \"avregistrera\" så tar vi bort er direkt."
    )
    return subject, body


def send_email(cfg, to_addr, subject, body):
    host = cfg.get("smtp_host", "smtp.gmail.com")
    port = int(cfg.get("smtp_port", 587))
    user = cfg.get("smtp_user", "").strip()
    pwd = cfg.get("smtp_pass", "").strip()
    if not user or not pwd:
        return False, "SMTP ej konfigurerat"
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = formataddr((cfg.get("company", "Städlinjen AB"), user))
    msg["To"] = to_addr
    msg["List-Unsubscribe"] = f"<mailto:{user}?subject=avregistrera>"
    try:
        with smtplib.SMTP(host, port, timeout=20) as s:
            s.starttls()
            s.login(user, pwd)
            s.sendmail(user, [to_addr], msg.as_string())
        return True, "ok"
    except Exception as e:
        return False, str(e)


def agent_tick():
    """Körs i bakgrunden. Skickar EN offert per varv om allt stämmer – säkert strypt."""
    cfg = load_config()
    if not cfg.get("agent_enabled"):
        return
    if not cfg.get("smtp_user") or not cfg.get("smtp_pass"):
        return
    today = datetime.now().strftime("%Y-%m-%d")
    if cfg.get("agent_sent_date") != today:
        cfg["agent_sent_date"] = today
        cfg["agent_sent_today"] = 0
        save_config(cfg)
    if cfg.get("agent_sent_today", 0) >= cfg.get("agent_daily_limit", 15):
        return
    if time.time() - cfg.get("agent_last_send", 0) < cfg.get("agent_interval_min", 8) * 60:
        return
    # nästa prospekt med e-post som inte kontaktats
    rows = load_prospects()
    target = next((r for r in rows if r.get("email") and r.get("status") == "Att kontakta"), None)
    if not target:
        return
    subject, body = build_offer_email(cfg, target)
    ok, info = send_email(cfg, target["email"], subject, body)
    if ok:
        target["status"] = "Kontaktad"
        write_prospects(rows)
        cfg["agent_sent_today"] = cfg.get("agent_sent_today", 0) + 1
        cfg["agent_last_send"] = time.time()
        save_config(cfg)
        agent_log(f"📤 Offert skickad till {target['company']} ({target['email']})")
        c2 = load_config()
        if c2.get("telegram_bot_token") and c2.get("telegram_chat_id"):
            _tg_send(c2["telegram_bot_token"], c2["telegram_chat_id"],
                     f"🤖 *Agenten skickade offert*\nTill: {target['company']}\n{target['email']}\nIdag: {cfg['agent_sent_today']}/{cfg.get('agent_daily_limit',15)}")
    else:
        agent_log(f"⚠️ Kunde inte skicka till {target['company']}: {info}")
        # pausa agenten vid inloggningsfel så vi inte loopar
        if "auth" in info.lower() or "login" in info.lower() or "password" in info.lower():
            cfg["agent_enabled"] = False
            save_config(cfg)
            agent_log("⏸️ Agenten pausad – kontrollera e-post/app-lösenord.")


def agent_loop():
    while True:
        try:
            agent_tick()
        except Exception as e:
            agent_log(f"Fel i agent-loop: {e}")
        time.sleep(30)


@app.route("/api/agent", methods=["GET", "POST"])
def api_agent():
    cfg = load_config()
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        for k in ["smtp_user", "smtp_pass", "smtp_host", "site_url"]:
            if k in data:
                cfg[k] = (data[k] or "").strip()
        if "smtp_port" in data:
            cfg["smtp_port"] = int(data["smtp_port"] or 587)
        if "agent_enabled" in data:
            cfg["agent_enabled"] = bool(data["agent_enabled"])
        if "agent_daily_limit" in data:
            cfg["agent_daily_limit"] = int(data["agent_daily_limit"] or 15)
        if "agent_interval_min" in data:
            cfg["agent_interval_min"] = int(data["agent_interval_min"] or 8)
        save_config(cfg)
        if cfg.get("agent_enabled"):
            agent_log("▶️ Agenten startad.")
        else:
            agent_log("⏸️ Agenten stoppad.")
    cfg = load_config()
    rows = load_prospects()
    queue = len([r for r in rows if r.get("email") and r.get("status") == "Att kontakta"])
    return jsonify({
        "enabled": cfg.get("agent_enabled", False),
        "configured": bool(cfg.get("smtp_user") and cfg.get("smtp_pass")),
        "smtp_user": cfg.get("smtp_user", ""),
        "site_url": cfg.get("site_url", ""),
        "smtp_host": cfg.get("smtp_host", "smtp.gmail.com"),
        "smtp_port": cfg.get("smtp_port", 587),
        "daily_limit": cfg.get("agent_daily_limit", 15),
        "interval_min": cfg.get("agent_interval_min", 8),
        "sent_today": cfg.get("agent_sent_today", 0),
        "queue": queue,
        "log": read_agent_log()[:40],
    })


@app.route("/dashboard")
def dashboard():
    return render_template_string(DASHBOARD_HTML)


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(BASE, filename)


DASHBOARD_HTML = r"""
<!DOCTYPE html><html lang="sv"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kontrollcenter – Städlinjen AB</title>
<style>
 *{box-sizing:border-box;margin:0;font-family:'Segoe UI',system-ui,sans-serif}
 body{background:#f1f5f9;color:#0f172a}
 .top{background:linear-gradient(120deg,#0b5a6e,#0891b2);color:#fff;padding:20px 28px;display:flex;align-items:center;gap:14px}
 .top .mark{width:42px;height:42px;background:#fff;color:#0e7490;border-radius:11px;display:grid;place-items:center;font-weight:800;font-size:22px}
 .top h1{font-size:21px}.top span{opacity:.85;font-size:13px;display:block}
 .live{margin-left:auto;background:rgba(255,255,255,.18);padding:7px 14px;border-radius:999px;font-size:13px;font-weight:600}
 .live b{color:#86efac}
 .tabs{display:flex;gap:4px;background:#fff;padding:0 28px;border-bottom:1px solid #e2e8f0;position:sticky;top:0;z-index:5}
 .tab{padding:15px 18px;border:0;background:none;cursor:pointer;font-size:15px;font-weight:600;color:#64748b;border-bottom:3px solid transparent}
 .tab.active{color:#0e7490;border-bottom-color:#0e7490}
 .wrap{padding:26px 28px;max-width:1200px;margin:0 auto}
 .page{display:none}.page.active{display:block}
 .stats{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:20px}
 .stat{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:16px 22px;min-width:120px}
 .stat b{font-size:28px;display:block}.stat span{color:#64748b;font-size:13px}
 .stat.ny b{color:#0891b2}.stat.ringd b{color:#d97706}.stat.vunnen b{color:#16a34a}.stat.forlorad b{color:#dc2626}
 .toolbar{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}
 .toolbar input,.toolbar select{padding:10px 14px;border:1px solid #cbd5e1;border-radius:10px;font-size:14px}
 .toolbar input{flex:1;min-width:180px}
 .card{background:#fff;border:1px solid #e2e8f0;border-radius:14px;padding:16px 18px;margin-bottom:12px;box-shadow:0 6px 18px -14px rgba(15,23,42,.3)}
 .lead-head{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
 .lead-head .name{font-size:17px;font-weight:700}
 .lead-head .phone{font-weight:700;color:#0e7490;font-size:16px}
 .lead-head .time{color:#94a3b8;font-size:13px;margin-left:auto}
 .pill{display:inline-block;padding:3px 11px;border-radius:999px;font-size:12px;font-weight:700}
 .pill.tjanst{background:#e0f2fe;color:#0369a1}
 .pill.area{background:#dcfce7;color:#166534}
 .meta{color:#475569;font-size:14px;margin:8px 0 12px;display:flex;gap:18px;flex-wrap:wrap}
 .meta b{color:#0f172a}
 .row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
 .statusbtns{display:flex;gap:6px;flex-wrap:wrap}
 .sbtn{border:1px solid #cbd5e1;background:#fff;padding:7px 13px;border-radius:999px;font-size:13px;font-weight:600;cursor:pointer;color:#475569}
 .sbtn.on[data-s="Ny"]{background:#0891b2;color:#fff;border-color:#0891b2}
 .sbtn.on[data-s="Ringd"]{background:#d97706;color:#fff;border-color:#d97706}
 .sbtn.on[data-s="Vunnen"]{background:#16a34a;color:#fff;border-color:#16a34a}
 .sbtn.on[data-s="Förlorad"]{background:#dc2626;color:#fff;border-color:#dc2626}
 .call{background:#16a34a;color:#fff;text-decoration:none;padding:8px 16px;border-radius:999px;font-weight:700;font-size:14px}
 .mailbtn{background:#0e7490;color:#fff;text-decoration:none;padding:8px 16px;border-radius:999px;font-weight:700;font-size:14px;border:0;cursor:pointer}
 .webbtn{background:#fff;border:1px solid #cbd5e1;color:#475569;text-decoration:none;padding:8px 14px;border-radius:999px;font-weight:600;font-size:13px}
 .del{margin-left:auto;background:none;border:0;color:#cbd5e1;cursor:pointer;font-size:18px}
 .del:hover{color:#dc2626}
 .note{margin-top:10px;width:100%;border:1px solid #e2e8f0;border-radius:10px;padding:9px 12px;font-size:13.5px;font-family:inherit;resize:vertical}
 .empty{text-align:center;color:#94a3b8;padding:60px}
 .form-card{background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:26px;max-width:620px;margin-bottom:20px}
 .form-card h3{margin-bottom:4px}.form-card .hint{color:#64748b;font-size:13.5px;margin-bottom:18px}
 .fld{margin-bottom:15px}.fld label{display:block;font-weight:600;font-size:13.5px;margin-bottom:6px}
 .fld input{width:100%;padding:11px 13px;border:1px solid #cbd5e1;border-radius:10px;font-size:14px}
 .grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
 .save{background:#0e7490;color:#fff;border:0;padding:12px 24px;border-radius:999px;font-weight:700;cursor:pointer;font-size:14px}
 .save:hover{background:#0b5a6e}
 .ghost{background:#fff;border:1px solid #0e7490;color:#0e7490;padding:11px 20px;border-radius:999px;font-weight:700;cursor:pointer}
 .ok-msg{color:#16a34a;font-weight:600;margin-left:12px}
 .warn{background:#fef3c7;border:1px solid #fcd34d;color:#92400e;padding:12px 16px;border-radius:10px;margin-bottom:18px;font-size:14px}
 .steps{background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:16px 20px;font-size:14px;line-height:1.8;margin-top:10px}
 .steps code{background:#0f172a;color:#a5f3fc;padding:2px 7px;border-radius:5px;font-size:13px}
 @media(max-width:640px){.grid2{grid-template-columns:1fr}.wrap{padding:18px}}
</style></head><body>
 <div class="top">
   <div class="mark">S</div>
   <div><h1>Kontrollcenter</h1><span>Städlinjen AB · allt på ett ställe</span></div>
   <div class="live">🟢 <b id="liveCount">0</b> leads · uppdateras live</div>
 </div>
 <div class="tabs">
   <button class="tab active" data-p="leads">📋 Leads</button>
   <button class="tab" data-p="prospekt">🎯 Hitta kunder</button>
   <button class="tab" data-p="agent">🤖 Auto-agent</button>
   <button class="tab" data-p="settings">⚙️ Inställningar</button>
   <button class="tab" data-p="pricing">💰 Priser</button>
   <button class="tab" data-p="telegram">📲 Telegram</button>
 </div>

 <div class="wrap">
   <!-- LEADS -->
   <div class="page active" id="p-leads">
     <div class="stats" id="stats"></div>
     <div class="toolbar">
       <input id="search" placeholder="🔍 Sök namn, telefon, område...">
       <select id="fstatus"><option value="">Alla statusar</option><option>Ny</option><option>Ringd</option><option>Vunnen</option><option>Förlorad</option></select>
       <select id="farea"><option value="">Alla områden</option></select>
     </div>
     <div id="leadList"></div>
   </div>

   <!-- HITTA KUNDER (B2B-prospekt) -->
   <div class="page" id="p-prospekt">
     <div class="warn">🎯 Riktiga Stockholmsföretag (kontorsstädning). B2B-mejl är lagligt om det är relevant + har avregistrering – det fixar mallen åt dig. Tryck <b>"Skriv mejl"</b> så öppnas ditt e-postprogram färdigifyllt.</div>
     <div class="stats" id="pstats"></div>
     <div id="prospectList"></div>
   </div>

   <!-- AUTO-AGENT -->
   <div class="page" id="p-agent">
     <div class="form-card" style="max-width:680px">
       <div style="display:flex;align-items:center;gap:14px;margin-bottom:6px">
         <h3 style="margin:0">🤖 Auto-agent</h3>
         <span id="agentBadge" class="pill" style="background:#fee2e2;color:#b91c1c">AV</span>
         <label style="margin-left:auto;display:flex;align-items:center;gap:8px;cursor:pointer">
           <input type="checkbox" id="agentToggle" onchange="toggleAgent()" style="width:20px;height:20px"> <b>På / Av</b>
         </label>
       </div>
       <p class="hint">Agenten skickar dina lagliga offertmejl till företagen i "Hitta kunder" – helt själv, dygnet runt, i säker takt. Din bror sköter svaren.</p>

       <div class="stats" style="margin:6px 0 16px">
         <div class="stat ny"><b id="agQueue">0</b><span>I kö att maila</span></div>
         <div class="stat ringd"><b id="agSent">0</b><span>Skickade idag</span></div>
         <div class="stat vunnen"><b id="agLimit">15</b><span>Dagsgräns</span></div>
       </div>

       <div id="agentWarn" class="warn" style="display:none">⚠️ Lägg in din e-post + app-lösenord nedan så börjar agenten skicka. Utan det kan den inte logga in i din mejl.</div>

       <h4 style="margin:8px 0">Din e-post (avsändare)</h4>
       <p class="hint">Gmail rekommenderas. Skapa ett gratis <b>app-lösenord</b>: Google-konto → Säkerhet → 2-stegsverifiering → App-lösenord. Klistra in det (inte ditt vanliga lösenord).</p>
       <div class="grid2">
         <div class="fld"><label>E-postadress (Gmail)</label><input id="a_user" placeholder="dittnamn@gmail.com"></div>
         <div class="fld"><label>App-lösenord</label><input id="a_pass" type="password" placeholder="16 tecken från Google"></div>
         <div class="fld"><label>Max mejl per dag</label><input id="a_limit" type="number" value="15"></div>
         <div class="fld"><label>Minuter mellan mejl</label><input id="a_interval" type="number" value="8"></div>
         <div class="fld" style="grid-column:1/-1"><label>Din hemsidas länk (skickas i mejlet → kunden ansöker själv)</label><input id="a_site" placeholder="https://...trycloudflare.com  eller din Render-länk"></div>
       </div>
       <button class="save" onclick="saveAgent(this)">Spara & aktivera</button>
       <span class="ok-msg" id="agentOk"></span>

       <h4 style="margin:22px 0 8px">Aktivitetslogg (live)</h4>
       <div id="agentLog" class="steps" style="max-height:240px;overflow:auto"></div>
     </div>
   </div>

   <!-- SETTINGS -->
   <div class="page" id="p-settings">
     <div class="form-card">
       <h3>Företagsuppgifter</h3>
       <p class="hint">Det här visas på hemsidan och i leads. Inga påhittade uppgifter – sätt era riktiga.</p>
       <div class="grid2">
         <div class="fld"><label>Företagsnamn</label><input id="s_company"></div>
         <div class="fld"><label>Org.nr</label><input id="s_orgnr"></div>
         <div class="fld"><label>Telefon</label><input id="s_phone"></div>
         <div class="fld"><label>E-post</label><input id="s_email"></div>
         <div class="fld"><label>Adress</label><input id="s_address"></div>
         <div class="fld"><label>Serviceområde</label><input id="s_service_area"></div>
       </div>
       <button class="save" onclick="saveSettings(this)">Spara</button><span class="ok-msg" id="setOk"></span>
     </div>
   </div>

   <!-- PRICING -->
   <div class="page" id="p-pricing">
     <div class="form-card">
       <h3>Priser (styr chattens offert)</h3>
       <p class="hint">Ändra här – chatten på hemsidan räknar direkt med dina nya priser. RUT dras automatiskt.</p>
       <div class="grid2">
         <div class="fld"><label>Hemstädning kr/timme (före RUT)</label><input id="pr_hem" type="number"></div>
         <div class="fld"><label>RUT-avdrag (%)</label><input id="pr_rut" type="number"></div>
       </div>
       <h4 style="margin:14px 0 8px">Flyttstädning – fast pris före RUT (kr)</h4>
       <div class="grid2">
         <div class="fld"><label>1 rok</label><input id="pr_f1" type="number"></div>
         <div class="fld"><label>2 rok</label><input id="pr_f2" type="number"></div>
         <div class="fld"><label>3 rok</label><input id="pr_f3" type="number"></div>
         <div class="fld"><label>4 rok</label><input id="pr_f4" type="number"></div>
         <div class="fld"><label>5+ rok</label><input id="pr_f5" type="number"></div>
       </div>
       <button class="save" onclick="savePricing(this)">Spara priser</button><span class="ok-msg" id="priceOk"></span>
     </div>
   </div>

   <!-- TELEGRAM -->
   <div class="page" id="p-telegram">
     <div class="form-card">
       <h3>Telegram till din bror</h3>
       <p class="hint">Varje nytt lead skickas direkt hit. Gratis att sätta upp.</p>
       <div class="fld"><label>Bot-token (från @BotFather)</label><input id="s_token" placeholder="8123456:AAH..."></div>
       <div class="fld"><label>Chat-id (din brors / gruppens id)</label><input id="s_chat" placeholder="123456789"></div>
       <button class="save" onclick="saveTelegram(this)">Spara</button>
       <button class="ghost" onclick="testTelegram(this)" style="margin-left:8px">Skicka testmeddelande</button>
       <span class="ok-msg" id="tgOk"></span>
       <div class="steps">
         <b>Så kopplar din bror (1 gång):</b><br>
         1. Öppna Telegram → sök <code>@BotFather</code> → skicka <code>/newbot</code> → kopiera bot-token.<br>
         2. Sök upp er nya bot → tryck <b>Start</b>.<br>
         3. Öppna <code>api.telegram.org/bot&lt;TOKEN&gt;/getUpdates</code> → hitta <code>"chat":{"id":...}</code>.<br>
         4. Klistra in token + chat-id ovan → Spara → "Skicka testmeddelande".
       </div>
     </div>
   </div>
 </div>

<script>
let LEADS=[], PROSPECTS=[], SETTINGS={company:'Städlinjen AB',phone:'',email:''};
const $=s=>document.querySelector(s);
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));
  t.classList.add('active');$('#p-'+t.dataset.p).classList.add('active');
});

async function loadLeads(){
  LEADS=await (await fetch('/api/leads')).json();
  $('#liveCount').textContent=LEADS.length;
  renderStats();renderLeads();
}
function renderStats(){
  const c={Ny:0,Ringd:0,Vunnen:0,'Förlorad':0};
  LEADS.forEach(l=>c[l.status]=(c[l.status]||0)+1);
  $('#stats').innerHTML=
   `<div class="stat"><b>${LEADS.length}</b><span>Totalt</span></div>
    <div class="stat ny"><b>${c.Ny}</b><span>Nya</span></div>
    <div class="stat ringd"><b>${c.Ringd}</b><span>Ringda</span></div>
    <div class="stat vunnen"><b>${c.Vunnen}</b><span>Vunna</span></div>
    <div class="stat forlorad"><b>${c['Förlorad']}</b><span>Förlorade</span></div>`;
  const areas=[...new Set(LEADS.map(l=>l.area).filter(Boolean))];
  const sel=$('#farea');const cur=sel.value;
  sel.innerHTML='<option value="">Alla områden</option>'+areas.map(a=>`<option>${a}</option>`).join('');
  sel.value=cur;
}
function renderLeads(){
  const q=($('#search').value||'').toLowerCase();
  const fs=$('#fstatus').value, fa=$('#farea').value;
  const list=LEADS.filter(l=>{
    const blob=`${l.name} ${l.phone} ${l.area} ${l.service}`.toLowerCase();
    return (!q||blob.includes(q))&&(!fs||l.status===fs)&&(!fa||l.area===fa);
  });
  if(!list.length){$('#leadList').innerHTML='<div class="empty">Inga leads matchar. Riktiga förfrågningar dyker upp här direkt när någon använder chatten på hemsidan. 🟢</div>';return;}
  $('#leadList').innerHTML=list.map(l=>{
    const tel=(l.phone||'').replace(/\s/g,'');
    const st=s=>`<button class="sbtn ${l.status===s?'on':''}" data-s="${s}" onclick="setStatus(${l.id},'${s}')">${s}</button>`;
    return `<div class="card">
      <div class="lead-head">
        <span class="name">${l.name||'(namn saknas)'}</span>
        <span class="phone">📞 ${l.phone||'–'}</span>
        ${l.service?`<span class="pill tjanst">${l.service}</span>`:''}
        ${l.area?`<span class="pill area">📍 ${l.area}</span>`:''}
        <span class="time">${l.created}</span>
      </div>
      <div class="meta">
        ${l.size?`<span><b>Storlek:</b> ${l.size}</span>`:''}
        ${l.frequency?`<span><b>Ofta:</b> ${l.frequency}</span>`:''}
        ${l.price?`<span><b>Pris:</b> ${l.price}</span>`:''}
        ${l.email?`<span><b>E-post:</b> ${l.email}</span>`:''}
        <span><b>Källa:</b> ${l.source||'chatt'}</span>
      </div>
      <div class="row">
        <div class="statusbtns">${st('Ny')}${st('Ringd')}${st('Vunnen')}${st('Förlorad')}</div>
        ${tel?`<a class="call" href="tel:${tel}">Ring nu</a>`:''}
        <button class="del" title="Radera" onclick="delLead(${l.id})">🗑</button>
      </div>
      <textarea class="note" placeholder="Anteckning (sparas automatiskt)..." onchange="saveNote(${l.id},this.value)">${l.notes||''}</textarea>
    </div>`;
  }).join('');
}
['search','fstatus','farea'].forEach(id=>$('#'+id).addEventListener('input',renderLeads));

async function setStatus(id,s){await fetch('/api/lead/'+id,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:s})});loadLeads();}
async function saveNote(id,v){await fetch('/api/lead/'+id,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({notes:v})});}
async function delLead(id){if(!confirm('Radera detta lead?'))return;await fetch('/api/lead/'+id,{method:'DELETE'});loadLeads();}

// ---- Hitta kunder (B2B-prospekt) ----
async function loadProspects(){
  PROSPECTS=await (await fetch('/api/prospects')).json();
  renderProspects();
}
function prospectEmail(p){
  const company=SETTINGS.company||'Städlinjen AB';
  const phone=SETTINGS.phone||'';const email=SETTINGS.email||'';
  const subject=`Städning av ${p.company} – offert från ${company}`;
  const body=`Hej!

Jag driver ${company}, en lokal städfirma i Stockholm.

Jag såg att ni driver ${p.type.toLowerCase()} i ${p.area} och ville höra om ni har behov av regelbunden städning av era lokaler. Vi hjälper flera företag i området med kontorsstädning – samma personal varje gång, miljömärkta produkter och fasta priser utan bindningstid.

Får jag skicka en kostnadsfri offert anpassad efter er yta? Det tar 2 minuter på telefon: ${phone}.

Vänliga hälsningar,
${company}
${phone}${email?' · '+email:''}

---
Vill ni inte ha fler mejl från oss? Svara bara "avregistrera" så tar vi bort er direkt.`;
  return {subject,body};
}
function renderProspects(){
  const c={'Att kontakta':0,'Kontaktad':0,'Svar':0,'Kund':0};
  PROSPECTS.forEach(p=>c[p.status]=(c[p.status]||0)+1);
  $('#pstats').innerHTML=
   `<div class="stat"><b>${PROSPECTS.length}</b><span>Prospekt</span></div>
    <div class="stat ny"><b>${c['Att kontakta']}</b><span>Att kontakta</span></div>
    <div class="stat ringd"><b>${c['Kontaktad']}</b><span>Kontaktade</span></div>
    <div class="stat vunnen"><b>${c['Kund']}</b><span>Blev kund</span></div>`;
  $('#prospectList').innerHTML=PROSPECTS.map(p=>{
    const tel=(p.phone||'').replace(/\s/g,'');
    const st=s=>`<button class="sbtn ${p.status===s?'on':''}" data-s="${s==='Kund'?'Vunnen':s==='Att kontakta'?'Ny':'Ringd'}" onclick="setProspect(${p.id},'${s}')">${s}</button>`;
    let action='';
    if(p.email){action=`<button class="mailbtn" onclick="writeMail(${p.id})">✉️ Skriv mejl</button>`;}
    else{action=`<a class="webbtn" href="https://${p.web}" target="_blank">🔎 Hitta e-post på ${p.web}</a>`;}
    return `<div class="card">
      <div class="lead-head">
        <span class="name">${p.company}</span>
        <span class="pill tjanst">${p.type}</span>
        <span class="pill area">📍 ${p.area}</span>
      </div>
      <div class="meta">
        ${p.email?`<span><b>E-post:</b> ${p.email}</span>`:''}
        ${p.phone?`<span><b>Tel:</b> ${p.phone}</span>`:''}
        <span><b>Webb:</b> ${p.web}</span>
      </div>
      <div class="row">
        <div class="statusbtns">${st('Att kontakta')}${st('Kontaktad')}${st('Svar')}${st('Kund')}</div>
        ${action}
        ${tel?`<a class="call" href="tel:${tel}">Ring</a>`:''}
        <button class="del" title="Ta bort" onclick="delProspect(${p.id})">🗑</button>
      </div>
    </div>`;
  }).join('');
}
function writeMail(id){
  const p=PROSPECTS.find(x=>x.id===id);if(!p)return;
  const m=prospectEmail(p);
  window.location.href=`mailto:${p.email}?subject=${encodeURIComponent(m.subject)}&body=${encodeURIComponent(m.body)}`;
  setProspect(id,'Kontaktad');
}
async function setProspect(id,s){await fetch('/api/prospect/'+id,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:s})});loadProspects();}
async function delProspect(id){if(!confirm('Ta bort detta prospekt?'))return;await fetch('/api/prospect/'+id,{method:'DELETE'});loadProspects();}

// ---- Auto-agent ----
async function loadAgent(){
  const a=await (await fetch('/api/agent')).json();
  $('#agentToggle').checked=a.enabled;
  const b=$('#agentBadge');
  b.textContent=a.enabled?'PÅ':'AV';
  b.style.background=a.enabled?'#dcfce7':'#fee2e2';
  b.style.color=a.enabled?'#166534':'#b91c1c';
  $('#agQueue').textContent=a.queue;
  $('#agSent').textContent=a.sent_today;
  $('#agLimit').textContent=a.daily_limit;
  if(!a.smtp_user)$('#a_user').value=''; else if(document.activeElement!==$('#a_user'))$('#a_user').value=a.smtp_user;
  if(document.activeElement!==$('#a_limit'))$('#a_limit').value=a.daily_limit;
  if(document.activeElement!==$('#a_interval'))$('#a_interval').value=a.interval_min;
  if(document.activeElement!==$('#a_site'))$('#a_site').value=a.site_url||'';
  $('#agentWarn').style.display=a.configured?'none':'block';
  $('#agentLog').innerHTML=a.log.length?a.log.map(l=>`<div><b>${l.time}</b> &nbsp;${l.msg}</div>`).join(''):'<i>Inget än. Aktivera agenten så loggas varje utskick här.</i>';
}
async function saveAgent(b){
  await post('/api/agent',{smtp_user:$('#a_user').value.trim(),smtp_pass:$('#a_pass').value.trim(),
    site_url:$('#a_site').value.trim(),
    agent_daily_limit:+$('#a_limit').value,agent_interval_min:+$('#a_interval').value,agent_enabled:true});
  $('#a_pass').value='';
  $('#agentOk').textContent='✓ Sparat & aktiverat';setTimeout(()=>$('#agentOk').textContent='',2500);
  loadAgent();
}
async function toggleAgent(){
  await post('/api/agent',{agent_enabled:$('#agentToggle').checked});loadAgent();
}

async function loadSettings(){
  const c=await (await fetch('/api/settings')).json();
  SETTINGS=c;
  s_company.value=c.company||'';s_orgnr.value=c.orgnr||'';s_phone.value=c.phone||'';
  s_email.value=c.email||'';s_address.value=c.address||'';s_service_area.value=c.service_area||'';
  s_token.value=c.telegram_bot_token||'';s_chat.value=c.telegram_chat_id||'';
  const p=c.pricing||{};pr_hem.value=p.hem_pris_tim;pr_rut.value=Math.round((p.rut||.5)*100);
  const f=p.flytt_pris||{};pr_f1.value=f['1 rok'];pr_f2.value=f['2 rok'];pr_f3.value=f['3 rok'];pr_f4.value=f['4 rok'];pr_f5.value=f['5+ rok'];
}
async function post(url,body){return fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});}
async function saveSettings(b){await post('/api/settings',{company:s_company.value,orgnr:s_orgnr.value,phone:s_phone.value,email:s_email.value,address:s_address.value,service_area:s_service_area.value});$('#setOk').textContent='✓ Sparat';setTimeout(()=>$('#setOk').textContent='',2000);}
async function saveTelegram(b){await post('/api/settings',{telegram_bot_token:s_token.value.trim(),telegram_chat_id:s_chat.value.trim()});$('#tgOk').textContent='✓ Sparat';setTimeout(()=>$('#tgOk').textContent='',2000);}
async function testTelegram(b){$('#tgOk').textContent='...skickar';const r=await (await post('/api/test-telegram',{})).json();$('#tgOk').textContent=r.ok?'✓ Skickat! Kolla Telegram':'✗ '+(r.error||'fel');}
async function savePricing(b){
  await post('/api/settings',{pricing:{hem_pris_tim:+pr_hem.value,rut:(+pr_rut.value)/100,
    flytt_pris:{'1 rok':+pr_f1.value,'2 rok':+pr_f2.value,'3 rok':+pr_f3.value,'4 rok':+pr_f4.value,'5+ rok':+pr_f5.value}}});
  $('#priceOk').textContent='✓ Sparat';setTimeout(()=>$('#priceOk').textContent='',2000);
}

loadSettings().then(loadProspects);
loadLeads();loadAgent();
setInterval(loadLeads,15000); // live-uppdatering var 15:e sek
setInterval(loadAgent,15000); // agentstatus + logg live
</script>
</body></html>
"""

if __name__ == "__main__":
    load_config()
    # starta auto-agenten i bakgrunden (jobbar medan du sover)
    threading.Thread(target=agent_loop, daemon=True).start()
    print("=" * 52)
    print("  Stadlinjen AB - Kontrollcenter + Auto-agent kor!")
    print(f"   Hemsida:    http://localhost:{PORT}")
    print(f"   Dashboard:  http://localhost:{PORT}/dashboard")
    print("   Auto-agent: aktiveras i fliken 'Auto-agent'")
    print("=" * 52)
    app.run(host="0.0.0.0", port=PORT, debug=False)
