# Solidservice – LIVE-STATUS (uppdaterad 2026-06-26)

Brorsans (Sardor Khikmatov) städfirma i Stockholm. Mapp: `C:\Users\Asus Rog\jword\stadlinjen\`.

## 🌐 LIVE-LÄNKAR
- **Publik sajt (DELA DENNA):** https://solidservicestad.onrender.com  ← ren URL, inget "bekbyn163"
  - Render **Static Site** (CDN, snabb, INGEN kallstart, gratis). service-id `srv-d8vdp1sm0tmc7396jk8g`.
- **Kundverktyg** (intern self-serve, färdiga meddelanden + kopiera-knapp): https://solidservicestad.onrender.com/verktyg.html
- **Integritetspolicy:** https://solidservicestad.onrender.com/integritetspolicy.html
- **Backend** (chatt/lead-API + /dashboard): https://solidservice.onrender.com  (Render web service `srv-d8uocrsvikkc73es2rrg`, gunicorn --bind fix)
- Gammal GitHub Pages-länk finns kvar men ANVÄNDS EJ: bekbyn163-lang.github.io/solidservice

## 📦 REPO
- GitHub: **github.com/bekbyn163-lang/solidservice** (PUBLIC, branch master). Push funkar (cachad cred via `git -c credential.helper=manager push`).

## 🖥️ SAJTEN (statisk)
index.html, styles.css, script.js, chat.js, integritetspolicy.html, verktyg.html.
Städad: INGEN adress/telefon, inga fejk-recensioner/"600 kunder", ingen ID06/påhittad historik ("sedan 2015"). SEO: CleaningService-schema (service-area Stockholm), Open Graph (snygg delning), lokala nyckelord, policy + cookie-info. Chatt + kontaktformulär POSTar leads → backend `/api/lead` (CORS på i app.py).

## 🤖 MEJLROBOT (B2B-utskick) – cloud_outreach.py + .github/workflows/outreach.yml
- GitHub Actions, schema **PÅ** (vardagar 08:00 UTC) + manuell "Run workflow".
- Skickar via **one.com SMTP** (send.one.com) från **info.solidservice@solidservice.se** → SPF/DKIM/DMARC stämmer = ej spam.
- Mänsklig 1-till-1-mall (`build_offer_email` i app.py), signeras **"Sardor Khikmatov"** (DEFAULT_CONFIG sender_name). **BCC till egen inkorg** → varje utskick syns i info.solidservice@-inkorgen.
- Status: **11 av 15 prospekt mailade.** 4 kvar saknar mejladress (kan ej mailas).
- GitHub Secrets satta: SMTP_USER=info.solidservice@solidservice.se, SMTP_PASS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID=1738443387.

## 🔍 KUND-BEVAKARE – cloud_hunter.py + .github/workflows/hunter.yml
- GitHub Actions var 3:e timme. Pingar Telegram med länk + färdigt svar när nån söker städ.
- Reddit = **BLOCKERAT (403)** från molnet, funkar ej. Behöver **Google Alerts RSS** (secret `ALERT_FEEDS`, ej satt) som bränsle.

## 📲 TELEGRAM
- Bot **@Solid27277bot**, chat_id **1738443387**. Robotarna pingar (via GitHub Secrets).
- TODO: website-leads → Telegram kräver `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` som **Render env-vars** på web-servicen (app.py load_config läser env). EJ satt än.

## 🏷️ DOMÄN solidservice.se – PAUSAD
Ägs av användaren (one.com, förnyas 2027-02-24). one.com LÅSER DNS + nameserver-byte bakom betald hosting (Nybörjare 29 kr/mån). one.coms prissida nämner INTE DNS → osäkert om uppgradering låser upp → PAUSAD (betala ej blint). Cloudflare-konto finns (dash hängde idag). Mejlkonton på domänen: info@, info.solidservice@ (avsändare), kudret@, sardor@, zivar@.

## ▶️ NÄSTA STEG (när usage-gränsen återställs ~02:30 svensk tid)
1. **HITTA MÅNGA RIKTIGA STOCKHOLMSFÖRETAG med verifierade publika mejladresser** (web-research: tandkliniker, advokat-/redovisningsbyråer, kontorshotell, kliniker, gym, restauranger) → lägg i prospects.json (fält: company, type, area, email, phone, web, status="Att kontakta") → roboten mailar dem. **ALDRIG fejka/gissa adresser** (studsar + bränner mejlen).
2. (valfritt) Google Företagsprofil som service-area-business (ingen adress behövs) = största gratis-källan; recensioner = #1 ranking.
3. (valfritt) Telegram → Render env för website-leads.
4. (valfritt) Google Alerts → ALERT_FEEDS secret för bevakaren.

## ⚖️ REGLER
- Webbläsarstyrning: ENDAST Microsoft Edge, ALDRIG Chrome.
- Aldrig fejka mejladresser. Bara inbound/opt-in + B2B-utskick med opt-out (mot företag, ej privatpersoner).
- Användaren skriver alla lösenord/secrets själv; jag matar aldrig in token/lösen i fält.

## ▶️ STARTA NYA CHATTEN MED:
"Fortsätt Solidservice — läs LIVE-STATUS.md i jword/stadlinjen. Hitta MÅNGA riktiga Stockholmsföretag med verifierade publika mejladresser och fyll på prospects.json så mejlroboten har nya att skicka till. Edge endast, aldrig Chrome, aldrig fejk-mejl."
