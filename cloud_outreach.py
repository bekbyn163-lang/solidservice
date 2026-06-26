#!/usr/bin/env python3
"""24/7 B2B-utskick (kontorsstädning) – körs av GitHub Actions, gratis.

Skickar några offert-mejl per varv via one.com SMTP (info@solidservice.se),
markerar prospekt som "Kontaktad", och pingar Telegram om token finns.
Allt strypt (få per varv) och varje mejl har opt-out, så det är lagligt B2B.

Avsändare + lösenord läses från miljövariabler (GitHub Secrets) – aldrig i koden:
  SMTP_USER, SMTP_PASS  (krävs)
  SMTP_HOST (default send.one.com), OUTREACH_PER_RUN (default 8)
  SITE_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (valfria)
"""
import os
import time
import datetime
import urllib.request
import urllib.parse

import app  # återanvänder build_offer_email, send_email, load_prospects, write/save_prospects

PER_RUN = int(os.environ.get("OUTREACH_PER_RUN", "8"))


def telegram(token, chat, text):
    if not token or not chat:
        return
    try:
        data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{token}/sendMessage", data=data, timeout=15
        )
    except Exception:
        pass


def _save_prospects(rows):
    # Funktionen heter write_prospects i app.py; fall tillbaka på save_prospects.
    fn = getattr(app, "write_prospects", None) or getattr(app, "save_prospects", None)
    if fn:
        fn(rows)


def main():
    cfg = app.load_config()
    cfg["smtp_host"] = os.environ.get("SMTP_HOST", "send.one.com")
    cfg["smtp_port"] = int(os.environ.get("SMTP_PORT", "587"))
    cfg["smtp_user"] = os.environ.get("SMTP_USER", "").strip()
    cfg["smtp_pass"] = os.environ.get("SMTP_PASS", "").strip()
    cfg["email"] = cfg["smtp_user"]
    if os.environ.get("SITE_URL"):
        cfg["site_url"] = os.environ["SITE_URL"].strip()

    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    tg_chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    if not cfg["smtp_user"] or not cfg["smtp_pass"]:
        print("STOPP: SMTP_USER/SMTP_PASS saknas. Lägg dem som GitHub Secrets. Inget skickat.")
        return

    rows = app.load_prospects()
    todo = [r for r in rows if r.get("email") and r.get("status") == "Att kontakta"]
    if not todo:
        print("Inga fler okontaktade prospekt med e-post. Klart (lägg till fler för mer volym).")
        return

    sent = 0
    today = datetime.date.today().isoformat()
    for p in todo:
        if sent >= PER_RUN:
            break
        subject, body = app.build_offer_email(cfg, p)
        ok, info = app.send_email(cfg, p["email"], subject, body)
        if ok:
            p["status"] = "Kontaktad"
            p["contacted"] = today
            sent += 1
            print(f"OK  -> {p['company']} <{p['email']}>")
            telegram(tg_token, tg_chat,
                     f"📧 Offert skickad till {p['company']} ({p['email']})")
        else:
            print(f"FEL -> {p['email']}: {info}")
        time.sleep(8)  # liten paus mellan utskick (snällare mot mejlservern)

    _save_prospects(rows)
    print(f"Klart. Skickade {sent} mejl. Kvar i kön: {len(todo) - sent}.")


if __name__ == "__main__":
    main()
