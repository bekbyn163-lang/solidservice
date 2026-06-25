# Solidservice – Projektöversikt (handoff)

**Vad:** Brorsans städfirma i Stockholm. Snygg hemsida (samma vibe som noxgroup.se fast för städ) + lead-maskin. Företaget heter **Solidservice** (ett ord, -service). Tidigare placeholder-namn "Städlinjen AB" är borta.

**Mapp:** `C:\Users\Asus Rog\jword\stadlinjen\` (mappnamnet är fortfarande "stadlinjen")
**Kör:** dubbelklicka `START.bat` → hemsida http://localhost:8810 · kontrollcenter http://localhost:8810/dashboard

---

## ✅ Klart och funkar
1. **Hemsida** (index.html, styles.css, chat.js) – hero "Städfirma Stockholm", tjänster, om oss, 12-tjänst-rutnät, galleri, omdömen, kontakt, footer. Blågrön design, riktiga bilder.
2. **Säljchatt** – frågar tjänst→storlek→hur ofta→område→namn→telefon, räknar RUT-pris, skickar lead → Telegram till brorsan.
3. **Kontrollcenter** (/dashboard): flikar Leads, Hitta kunder, Auto-agent, Lyssnar, Inställningar, Priser, Telegram.
4. **Hitta kunder** – 15 RIKTIGA Stockholmsföretag (kontorshotell, tandkliniker, advokat-/redovisningsbyråer) + färdiga lagliga offertmejl.
5. **Meta Lead-annons webhook** (`/webhook/meta`) – byggd, redo. Behöver FB-annons + Page-token + budget.
6. **Lyssnar-agent** – bevakar Google News/Alerts RSS efter folk som söker städ, intent-filter, pingar Telegram med färdigt svar. Byggd, parkerad.
7. **Auto-mejl-agent** (SMTP) – byggd MEN användaren valde bort mejl (spam/ban-rädsla).

## ⚙️ Måste fyllas i (config.json – allt är platshållare nu)
- Telefon (08-559 23 100), e-post (info@solidservice.se), org.nr – byt till riktiga
- Telegram bot-token + chat-id (så brorsan får leads) – via @BotFather, se README.md

## 🧭 Strategi-beslut (viktigt)
- **Mejl-utskick = NEJ** (rädd för spam/ban). 
- Sanning: kall kontakt är olaglig på ALLA kanaler (SMS/WhatsApp/samtal kräver opt-in). Bara inbound/opt-in är säkert.
- Kunden väljer ALLTID själv innan något når Telegram. Brorsan sköter closing.
- **De 4 vägarna:** 1) Lyssnar-agent, 2) Meta-annons, 3) Google/organiskt, 4) **Mäklare/flyttfirma-partnerskap** (gratis, varma, återkommande) = REKOMMENDERAD, ej byggd än.

## 🌐 LIVE-KOPPLING (pågår, blockerad)
- **Plan:** appen på Render (gratis) → peka one.com-domänen mot Render.
- **Domän:** solidservice (köpt på one.com, TLD antagligen .se – obekräftad).
- **Status:** koden är committad lokalt i git. `gh` ej installerat, ingen GitHub-remote än. Render hämtar från GitHub (user: bekbyn163-lang). render.yaml + Procfile finns (gunicorn app:app).
- **BLOCKER:** webbläsar-styrning. Bara "Browser 1" är ansluten till Claude-tillägget (troligen hans Chrome – FÅR EJ röras). Edge ("Browser 2") är INTE ansluten. För att styra Edge: installera/aktivera Claude-tillägget i Edge först.
- **Regler:** användaren skriver alla lösenord själv; användaren klickar Authorize/OAuth.

## ⚠️ Ärliga caveats för live
- Render gratis: filer nollställs vid omstart (leads.json försvinner – MEN Telegram behåller varje lead); sover efter 15 min inaktivitet (kallstart ~30–60 s).

## ▶️ Nästa steg
1. Få koden till GitHub (installera gh, eller via Edge-webbläsaren).
2. Deploya till Render.
3. Peka one.com-domänen.
4. Fyll riktig config (telefon, e-post, org.nr, Telegram-token).
5. Överväg Väg 4 (mäklare/flyttfirma-partnerskap) för varma kunder.
