#!/usr/bin/env python3
"""Auto-hittare av B2B-kunder i Stockholm (24/7, gratis, ingen API-nyckel).

Gör exakt det Claude gjorde för hand, men automatiskt:
  1. Frågar OpenStreetMap (Overpass API, gratis) efter företag i Stockholm
     som har en hemsida (restauranger, kliniker, advokat-/redovisningsbyråer,
     gym, frisörer, kontor m.m.).
  2. Hämtar varje företags egen sida och PLOCKAR UT den publika mejladressen
     som FAKTISKT står där (gissar ALDRIG en adress – då studsar mejlen).
  3. Lägger nya, dubblettkollade prospekt i prospects.json med
     status "Att kontakta" – så tar mejlroboten (cloud_outreach.py) vid.

Körs av GitHub Actions (.github/workflows/hunter-prospects.yml). Bara stdlib.
Sätt DRY_RUN=1 för att bara skriva ut vad den HADE lagt till (sparar inget).
"""
import os
import re
import json
import time
import urllib.request
import urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
PROSPECTS_FILE = os.path.join(BASE, "prospects.json")

DRY_RUN = os.environ.get("DRY_RUN") == "1"
MAX_NEW = int(os.environ.get("HUNTER_MAX_NEW", "12"))       # nya prospekt per varv
MAX_VISIT = int(os.environ.get("HUNTER_MAX_VISIT", "90"))    # hur många sidor vi besöker

OVERPASS = "https://overpass-api.de/api/interpreter"
# Innerstaden + närförorter (syd, väst, nord, öst).
BBOX = (59.28, 17.95, 59.38, 18.18)
UA = "SolidserviceProspectFinder/1.0 (+info@solidservice.se)"

# Role-konton vi litar på som "företagets egen" även om domänen inte matchar sajten.
ROLE = {"info", "kontakt", "hej", "hello", "bokning", "boka", "mail", "kontor",
        "reception", "order", "kund", "kundtjanst", "office", "kansli", "post"}
# Domäner att aldrig plocka (tredjeparts-widgets, exempel, bildfiler m.m.).
JUNK_DOM = ("sentry", "example.", "wixpress", "schema.org", "w3.org", "googleapis",
            "google.com", "gstatic", "cloudflare", "jquery", "gravatar", "facebook",
            "instagram", "youtube", "twitter", "linkedin", "googlemail", "domain.com",
            "yourdomain", "email.com", "sentry.io", "wix.com", "squarespace")
EMAIL_RE = re.compile(r"[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}", re.I)


def reg_domain(host):
    """Registrerbar domän, t.ex. www.foo.se -> foo.se (funkar bra för .se/.com)."""
    host = host.lower().split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read(700_000)  # tak: läs inte jättesidor
        return raw.decode("utf-8", "ignore")


def type_label(tags):
    a = tags.get("amenity", "")
    o = tags.get("office", "")
    s = tags.get("shop", "")
    h = tags.get("healthcare", "")
    if a in ("restaurant", "fast_food", "bar", "pub", "biergarten"):
        return "Restaurang"
    if a == "cafe":
        return "Kafé"
    if a == "dentist" or h == "dentist":
        return "Tandvårdsklinik"
    if a == "veterinary":
        return "Veterinärklinik"
    if a in ("doctors", "clinic") or h in ("clinic", "doctor", "centre"):
        return "Klinik"
    if h == "physiotherapist":
        return "Fysioterapiklinik"
    if o == "lawyer":
        return "Advokatbyrå"
    if o == "accountant":
        return "Redovisningsbyrå"
    if o == "estate_agent":
        return "Mäklarbyrå"
    if o in ("coworking", "coworking_space") or a == "coworking_space":
        return "Kontorshotell"
    if s == "hairdresser":
        return "Frisörsalong"
    if s == "beauty":
        return "Skönhetssalong"
    if s == "massage":
        return "Massageklinik"
    if tags.get("leisure") == "fitness_centre":
        return "Gym"
    if o:
        return "Kontor"
    return ""


def overpass_elements():
    q = f"""[out:json][timeout:90];
(
  nwr["amenity"~"^(restaurant|cafe|bar|pub|fast_food|dentist|clinic|doctors|veterinary)$"]["website"]{BBOX};
  nwr["office"]["website"]{BBOX};
  nwr["shop"~"^(hairdresser|beauty|massage)$"]["website"]{BBOX};
  nwr["leisure"="fitness_centre"]["website"]{BBOX};
  nwr["healthcare"]["website"]{BBOX};
);
out center tags 500;"""
    data = urllib.parse.urlencode({"data": q}).encode()
    req = urllib.request.Request(OVERPASS, data=data, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8", "ignore")).get("elements", [])


def site_email(website):
    """Hämtar företagets sida och returnerar en publik mejl som FAKTISKT står där."""
    if not website.startswith("http"):
        website = "https://" + website
    try:
        host = urllib.parse.urlparse(website).netloc
    except Exception:
        return ""
    sitedom = reg_domain(host)
    pages = [website.rstrip("/")]
    for p in ("/kontakt", "/kontakta-oss", "/kontakt-oss", "/contact", "/om-oss"):
        pages.append(website.rstrip("/") + p)
    found = []
    for url in pages[:4]:
        try:
            htmltext = fetch(url, timeout=15)
        except Exception:
            continue
        for m in EMAIL_RE.findall(htmltext):
            e = m.lower().strip(".")
            if any(j in e for j in JUNK_DOM):
                continue
            if e.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
                continue
            if e not in found:
                found.append(e)
        if found:
            break
        time.sleep(0.6)
    # Föredra adress vars domän matchar sajten, annars ett role-konto.
    for e in found:
        if reg_domain(e.split("@")[1]) == sitedom:
            return e
    for e in found:
        if e.split("@")[0] in ROLE:
            return e
    return ""


def main():
    # Befintliga prospekt – för dubblettkoll och nästa id.
    rows = []
    if os.path.exists(PROSPECTS_FILE):
        with open(PROSPECTS_FILE, encoding="utf-8") as f:
            rows = json.load(f)
    have_email = {(r.get("email") or "").lower() for r in rows if r.get("email")}
    have_dom = {reg_domain(r.get("web", "")) for r in rows if r.get("web")}
    next_id = max([r.get("id", 0) for r in rows], default=0) + 1

    try:
        els = overpass_elements()
    except Exception as e:
        print("Overpass-fel (försök igen nästa varv):", e)
        return
    print(f"OpenStreetMap gav {len(els)} företag med hemsida i Stockholm.")

    added = []
    visited = 0
    for el in els:
        if len(added) >= MAX_NEW or visited >= MAX_VISIT:
            break
        tags = el.get("tags", {})
        name = (tags.get("name") or "").strip()
        web = (tags.get("website") or tags.get("contact:website") or "").strip()
        if not name or not web:
            continue
        label = type_label(tags)
        if not label:
            continue
        # Hoppa över myndigheter/ambassader/religiösa lokaler (olämpliga B2B-mål).
        if tags.get("office") in ("government", "diplomatic", "religion", "political_party"):
            continue
        if any(b in name.lower() for b in (
                "ambassad", "embassy", "konsulat", "kommun", "myndighet", "polis",
                "kyrka", "församling", "moské", "synagog", "region stockholm",
                "landsting", "skatteverk")):
            continue
        webdom = reg_domain(urllib.parse.urlparse(
            web if web.startswith("http") else "https://" + web).netloc)
        if not webdom or webdom in have_dom:
            continue  # redan i listan (eller konstig domän)

        # Mejl: använd OSM-taggen om den finns, annars skrapa sidan.
        email = (tags.get("email") or tags.get("contact:email") or "").strip().lower()
        if email and any(j in email for j in JUNK_DOM):
            email = ""
        if not email:
            visited += 1
            email = site_email(web)
            time.sleep(0.8)
        if not email or email in have_email:
            continue

        area = (tags.get("addr:suburb") or tags.get("addr:city") or "Stockholm").strip()
        phone = (tags.get("contact:phone") or tags.get("phone") or "").strip()
        p = {
            "company": name,
            "type": label,
            "area": area,
            "email": email,
            "phone": phone,
            "web": webdom,
            "id": next_id,
            "status": "Att kontakta",
        }
        added.append(p)
        have_email.add(email)
        have_dom.add(webdom)
        next_id += 1
        print(f"  + {name}  [{label}, {area}]  <{email}>")

    if not added:
        print("Inga nya verifierade mejl denna gång (allt redan i listan eller inga publika adresser).")
        return
    if DRY_RUN:
        print(f"\nDRY_RUN: hade lagt till {len(added)} nya prospekt (sparar inget).")
        return
    rows.extend(added)
    with open(PROSPECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print(f"\nKlart. La till {len(added)} nya prospekt. Totalt nu: {len(rows)}.")


if __name__ == "__main__":
    main()
