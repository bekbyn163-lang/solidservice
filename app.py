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
import urllib.request
import urllib.parse
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, render_template_string

BASE = os.path.dirname(os.path.abspath(__file__))
LEADS_FILE = os.path.join(BASE, "leads.json")
CONFIG_FILE = os.path.join(BASE, "config.json")
PORT = int(os.environ.get("PORT", 8810))  # molnet (Render m.fl.) sätter PORT automatiskt

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
let LEADS=[];
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

async function loadSettings(){
  const c=await (await fetch('/api/settings')).json();
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

loadLeads();loadSettings();
setInterval(loadLeads,15000); // live-uppdatering var 15:e sek
</script>
</body></html>
"""

if __name__ == "__main__":
    load_config()
    print("=" * 52)
    print("  Städlinjen AB – Kontrollcenter körs!")
    print(f"   Hemsida:    http://localhost:{PORT}")
    print(f"   Dashboard:  http://localhost:{PORT}/dashboard")
    print("=" * 52)
    app.run(host="0.0.0.0", port=PORT, debug=False)
