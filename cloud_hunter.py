#!/usr/bin/env python3
"""24/7 kund-bevakare för Stockholm.

Letar efter folk som söker städhjälp (Reddit + valfria Google Alerts-RSS) och
pingar din Telegram med LÄNKEN till inlägget + ett färdigt svar att klistra in.
Du går bara dit och klistrar in. Körs gratis av GitHub Actions.

Hemligheter via env/Secrets (redan satta): TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
Valfritt: ALERT_FEEDS = komma-separerade Google Alerts-RSS-URL:er (mer träffar).
"""
import os
import re
import json
import time
import html
import datetime
import urllib.request
import urllib.parse

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
LINK = os.environ.get("SITE_URL", "https://solidservicestad.onrender.com/").strip()
def _feedfile():
    # Google Alerts-RSS kan ligga i alert_feeds.txt (en URL per rad) i repot,
    # så boten kan kopplas på utan GitHub-secret. # = kommentar.
    try:
        return [l.strip() for l in open("alert_feeds.txt", encoding="utf-8")
                if l.strip() and not l.strip().startswith("#")]
    except Exception:
        return []


FEEDS = ([f.strip() for f in os.environ.get("ALERT_FEEDS", "").split(",") if f.strip()]
         + _feedfile())
MAX_PINGS = int(os.environ.get("HUNTER_MAX_PINGS", "6"))
SEEN_FILE = "hunter_seen.json"
LEADS_OUT = "organic_leads.json"   # visas på den lätta dashboarden (kunder.html)
KEEP = 60                          # hur många leads vi sparar på dashboarden


def suggest_reply(title):
    """Färdigt svar att klistra in, anpassat efter vad personen söker."""
    t = title.lower()
    if "flytt" in t:
        jobb = "flyttstädning"
    elif "kontor" in t or "lokal" in t or "företag" in t:
        jobb = "kontorsstädning"
    elif "fönster" in t or "fonster" in t:
        jobb = "fönsterputs"
    elif "trapp" in t or "förening" in t or "brf" in t:
        jobb = "trapp-/föreningsstädning"
    else:
        jobb = "hemstädning"
    return (
        f"Hej! Såg att du söker hjälp med städ. Vi på Solidservice tar {jobb} i hela "
        f"Stockholm, med 50% RUT-avdrag och nöjd-kund-garanti. Hör av dig så fixar jag "
        f"en kostnadsfri offert direkt: {LINK}  /Sardor, Solidservice"
    )


REPLY = suggest_reply("")  # generell fallback

# En riktig lead = någon som BÅDE pratar städ OCH frågar/söker. Annars = nyhet/brus.
CLEAN = [
    "städ", "stad", "flyttstäd", "hemstäd", "hemstädning", "kontorsstäd",
    "fönsterputs", "fonsterputs", "städfirma", "städhjälp", "städning", "flyttstädning",
    "trappstäd", "byggstäd", "storstäd",
]
INTENT = [
    "sök", "sökes", "letar", "letar efter", "tips på", "tips om", "rekommend",
    "någon som", "ngn som", "behöver", "vet ni", "förslag på", "anlita",
    "kan ni rekommend", "hjälp med", "tar emot",
]


def seen_load():
    try:
        with open(SEEN_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def seen_save(s):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(s)[-3000:], f, ensure_ascii=False)


def leads_load():
    try:
        with open(LEADS_OUT, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def leads_save(rows):
    with open(LEADS_OUT, "w", encoding="utf-8") as f:
        json.dump(rows[:KEEP], f, ensure_ascii=False, indent=2)


def telegram(text):
    if not TOKEN or not CHAT:
        return False
    try:
        data = urllib.parse.urlencode({"chat_id": CHAT, "text": text}).encode()
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage", data=data, timeout=15
        )
        return True
    except Exception as e:
        print("telegram-fel:", e)
        return False


def fetch(url):
    req = urllib.request.Request(
        url, headers={"User-Agent": "SolidserviceHunter/1.0 (kontakt: info@solidservice.se)"}
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", "ignore")


def reddit_items():
    out = []
    q = urllib.parse.quote(
        "städ OR städhjälp OR städfirma OR flyttstäd OR hemstäd OR hemstädning OR "
        "kontorsstäd OR städning OR fönsterputs"
    )
    for sub in ("stockholm", "sweden"):
        try:
            raw = fetch(
                f"https://www.reddit.com/r/{sub}/search.json?q={q}"
                f"&restrict_sr=on&sort=new&limit=25"
            )
            data = json.loads(raw)
            for ch in data.get("data", {}).get("children", []):
                d = ch.get("data", {})
                out.append({
                    "id": "reddit_" + d.get("id", ""),
                    "title": d.get("title", ""),
                    "text": (d.get("selftext", "") or "")[:300],
                    "link": "https://www.reddit.com" + d.get("permalink", ""),
                    "src": "Reddit r/" + sub,
                })
        except Exception as e:
            print(f"reddit r/{sub} misslyckades (kan vara blockerat fran molnet):", e)
        time.sleep(2)
    return out


# Inbyggda gratisflöden (funkar från molnet, ingen inloggning). Google News
# crawlar forum/bloggar; intent-filtret nedan rensar bort vanliga nyheter.
BUILTIN_FEEDS = [
    "https://news.google.com/rss/search?q=%22s%C3%B6ker+st%C3%A4dhj%C3%A4lp%22+stockholm&hl=sv&gl=SE&ceid=SE:sv",
    "https://news.google.com/rss/search?q=%22letar+efter+st%C3%A4dfirma%22+stockholm&hl=sv&gl=SE&ceid=SE:sv",
    "https://news.google.com/rss/search?q=rekommendera+st%C3%A4dfirma+stockholm&hl=sv&gl=SE&ceid=SE:sv",
]


def rss_items():
    out = []
    for feed in FEEDS + BUILTIN_FEEDS:
        try:
            xml = fetch(feed)
            entries = re.findall(r"<entry[\s>].*?</entry>", xml, re.S) \
                or re.findall(r"<item[\s>].*?</item>", xml, re.S)
            for e in entries:
                tm = re.search(r"<title[^>]*>(.*?)</title>", e, re.S)
                lm = re.search(r'<link[^>]*href="([^"]+)"', e) \
                    or re.search(r"<link[^>]*>(.*?)</link>", e, re.S)
                title = html.unescape(re.sub("<.*?>", "", tm.group(1)).strip()) if tm else ""
                link = (lm.group(1) if lm else "").strip()
                um = re.search(r"[?&]url=([^&]+)", link)
                if um:
                    link = urllib.parse.unquote(um.group(1))
                if title:
                    out.append({
                        "id": "rss_" + str(abs(hash(title + link))),
                        "title": title, "text": "", "link": link, "src": "Google Alert",
                    })
        except Exception as e:
            print("rss-feed misslyckades:", e)
    return out


def is_lead(item):
    blob = (item["title"] + " " + item["text"]).lower()
    return any(c in blob for c in CLEAN) and any(w in blob for w in INTENT)


def main():
    seen = seen_load()
    leads = leads_load()
    have = {l.get("id") for l in leads}
    items = reddit_items() + rss_items()
    new = [i for i in items if i["id"] not in seen]
    pinged = 0
    added = 0
    today = datetime.date.today().isoformat()
    for it in new:
        seen.add(it["id"])
        if not is_lead(it):
            continue
        reply = suggest_reply(it["title"])
        if it["id"] not in have:           # spara till dashboarden (kunder.html)
            leads.insert(0, {
                "id": it["id"],
                "source": it["src"],
                "title": it["title"],
                "link": it["link"],
                "message": reply,
                "date": today,
            })
            have.add(it["id"])
            added += 1
        if TOKEN and CHAT and pinged < MAX_PINGS:   # och pinga Telegram
            msg = (
                "🔎 Möjlig kund i Stockholm!\n\n"
                f"{it['title']}\n({it['src']})\n👉 {it['link']}\n\n"
                f"📋 Klistra in detta svar:\n{reply}"
            )
            if telegram(msg):
                pinged += 1
                time.sleep(2)
    seen_save(seen)
    leads_save(leads)
    if not TOKEN or not CHAT:
        print("(Telegram av – inga secrets. Leads sparas ändå till dashboarden.)")
    print(f"Klart. {len(new)} nya inlägg, {added} nya kund-leads till dashboarden, "
          f"{pinged} pingade till Telegram.")


if __name__ == "__main__":
    main()
