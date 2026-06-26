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
import urllib.request
import urllib.parse

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
LINK = os.environ.get("SITE_URL", "https://bekbyn163-lang.github.io/solidservice/").strip()
FEEDS = [f.strip() for f in os.environ.get("ALERT_FEEDS", "").split(",") if f.strip()]
MAX_PINGS = int(os.environ.get("HUNTER_MAX_PINGS", "6"))
SEEN_FILE = "hunter_seen.json"

REPLY = (
    "Hej! Vi på Solidservice tar städuppdrag i hela Stockholm – hem, flytt & kontor, "
    f"med 50% RUT-avdrag och nöjd-kund-garanti. Skicka ett PM eller kika på {LINK} "
    "så fixar vi en kostnadsfri offert! 🧽"
)

# Tecken på att någon FRÅGAR (inte bara nämner städ) – håller kvaliteten uppe.
INTENT = [
    "sök", "sökes", "rekommend", "tips på", "tips om", "någon som", "ngn som",
    "behöver", "letar", "letar efter", "vet ni", "kan ni rekommend", "hjälp med städ",
    "hjälp med flytt", "förslag på", "anlita",
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


def rss_items():
    out = []
    for feed in FEEDS:
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
    return any(w in blob for w in INTENT)


def main():
    if not TOKEN or not CHAT:
        print("STOPP: TELEGRAM_BOT_TOKEN/CHAT_ID saknas. Inget gjort.")
        return
    seen = seen_load()
    items = reddit_items() + rss_items()
    new = [i for i in items if i["id"] not in seen]
    pinged = 0
    for it in new:
        seen.add(it["id"])
        if pinged >= MAX_PINGS:
            continue
        if not is_lead(it):
            continue
        msg = (
            "🔎 Möjlig kund i Stockholm!\n\n"
            f"{it['title']}\n({it['src']})\n👉 {it['link']}\n\n"
            f"📋 Klistra in detta svar:\n{REPLY}"
        )
        if telegram(msg):
            pinged += 1
            time.sleep(2)
    seen_save(seen)
    print(f"Klart. {len(new)} nya inlägg hittade, {pinged} pingade till Telegram.")


if __name__ == "__main__":
    main()
