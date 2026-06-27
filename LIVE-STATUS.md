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
- Status (2026-06-27): **39 prospekt, ~26 i kö** att mailas (kund-hittaren fyller på själv).
- GitHub Secrets satta: SMTP_USER=info.solidservice@solidservice.se, SMTP_PASS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID=1738443387.

## 🧲 KUND-HITTARE (NYTT 2026-06-27) – prospect_hunter.py + hunter-prospects.yml
- **Automatiserar det Claude gjorde för hand.** Frågar OpenStreetMap (Overpass, gratis, ingen nyckel) efter Stockholmsföretag med hemsida → besöker sidan → **skrapar ut den publika mejl som faktiskt står där** (gissar aldrig; role-konto eller domän-match krävs; ambassad/myndighet/kyrka filtreras bort). Dubblettkollar mot prospects.json, lägger nya som "Att kontakta". Stdlib, inga secrets (GITHUB_TOKEN committar).
- Schema: **mån/ons/fre 06:00 UTC** (HUNTER_MAX_NEW=10) → mejlroboten 08:00 tar vid. Testkört: ~20% av besökta sidor ger verifierad mejl; körde live 2026-06-27 → prospects.json **39 prospekt, 26 i kö**.

## 🔍 KUND-BEVAKARE (privatpersoner) – cloud_hunter.py + hunter.yml
- GitHub Actions var 3:e timme. Skriver nu träffar till **`organic_leads.json`** (visas på dashboarden) + pingar Telegram. Färdigt svar anpassas (flytt/kontor/hem/fönster).
- Filter skärpt: kräver BÅDE städ-ord OCH frågar-ord (slipper nyhetsbrus). Inbyggda Google News-RSS som gratiskälla; **Google Alerts RSS** (`ALERT_FEEDS`) = bästa bränslet, användaren sätter upp (se ORGANIC-GUIDE.md). Reddit = blockerat (403) från molnet.

## 🧽 LÄTT DASHBOARD – kunder.html
- **https://solidservicestad.onrender.com/kunder.html** — mobilvänlig. Visar privatkund-leads (länk "Öppna inlägget" + färdigt svar + "Kopiera"-knapp) + B2B-räknare (kö/mejlade/totalt). Helt filbaserad: läser organic_leads.json + prospects.json (serveras statiskt; hunters committar → static site auto-deployar). Ingen ny backend/secret/CORS.

## 📲 TELEGRAM
- Bot **@Solid27277bot**, chat_id **1738443387**. Robotarna pingar (via GitHub Secrets).
- TODO: website-leads → Telegram kräver `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` som **Render env-vars** på web-servicen (app.py load_config läser env). EJ satt än.

## 🏷️ DOMÄN solidservice.se – PAUSAD
Ägs av användaren (one.com, förnyas 2027-02-24). one.com LÅSER DNS + nameserver-byte bakom betald hosting (Nybörjare 29 kr/mån). one.coms prissida nämner INTE DNS → osäkert om uppgradering låser upp → PAUSAD (betala ej blint). Cloudflare-konto finns (dash hängde idag). Mejlkonton på domänen: info@, info.solidservice@ (avsändare), kudret@, sardor@, zivar@.

## ▶️ NÄSTA STEG
1. ✅ KLART/AUTOMATISERAT: hitta företag + mejla dem (kund-hittaren + mejlroboten gör det 24/7 nu, inget Claude-jobb behövs).
2. **Användaren själv (5 min, valfritt men ger fler privatkunder):** skapa Google Alerts → lägg RSS som `ALERT_FEEDS`-secret. Exakta steg i **ORGANIC-GUIDE.md**.
3. (valfritt) Google Företagsprofil som service-area-business (ingen adress behövs) = största gratis-källan; recensioner = #1 ranking.
4. (valfritt) Telegram → Render env för website-leads. Meta lead-ads (`/webhook/meta`) för stor privatkund-volym (kräver liten annonsbudget).

## ⚖️ REGLER
- Webbläsarstyrning: ENDAST Microsoft Edge, ALDRIG Chrome.
- Aldrig fejka mejladresser. Bara inbound/opt-in + B2B-utskick med opt-out (mot företag, ej privatpersoner).
- Användaren skriver alla lösenord/secrets själv; jag matar aldrig in token/lösen i fält.

## ▶️ STARTA NYA CHATTEN MED:
"Fortsätt Solidservice — läs LIVE-STATUS.md i jword/stadlinjen. Pipelinen är nu självgående (kund-hittaren prospect_hunter.py + mejlroboten + organisk hunter + kunder.html-dashboard). Kolla att robotarna kör grönt i GitHub Actions, fyll på fler kategorier vid behov. Edge endast, aldrig Chrome, aldrig fejk-mejl."
