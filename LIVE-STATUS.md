# Solidservice – LIVE-STATUS (uppdaterad 2026-06-27)

Brorsans (Sardor Khikmatov) städfirma i Stockholm. Mapp: `C:\Users\Asus Rog\jword\stadlinjen\`.

## 🌐 LIVE-LÄNKAR
- **Publik sajt (DELA med kunder):** https://solidservicestad.onrender.com — ren URL, verifierad aktuell 2026-06-27 (hero + info@solidservice.se, ingen fejk). Render **Static Site** (CDN, ingen kallstart).
  - ⚠️ Render static-*deployen* är EFTER: serverar gammal `prospects.json` (15) + saknar `kunder.html` (404). Homepage funkar dock. Auto-deploy verkar av/trasig.
- **DASHBOARD (för dig – leads + färdiga svar):** https://bekbyn163-lang.github.io/solidservice/kunder.html
  - **GitHub Pages = alltid-på (somnar ALDRIG) + aktuell (39 prospekt).** DETTA är den pålitliga dashboard-länken (inte Render-static, som 404:ar).
- **Kontrollpanel/admin (leads, inställningar, priser, robotar):** https://solidservice.onrender.com/dashboard — Render web service `srv-d8uocrsvikkc73es2rrg`, **SOMNAR ~30s**. (Tabbar: Leads, Hitta kunder, Auto-agent, Lyssnare, Inställningar, Priser, Telegram.)
- Kundverktyg: /verktyg.html · Integritetspolicy: /integritetspolicy.html

## 📦 REPO
- GitHub **github.com/bekbyn163-lang/solidservice** (PUBLIC, master). Push: `git -c credential.helper=manager push origin master`. Robotarna auto-committar → vid rebase-konflikt i prospects.json: behåll robotens "Kontaktad" + nya rader.

## 🖥️ SAJTEN (statisk)
index.html, styles.css, script.js, chat.js, kunder.html, verktyg.html, integritetspolicy.html. Städad (ingen adress/telefon/fejk). Chatt + formulär POSTar leads → backend `/api/lead` (CORS på).

## 🤖 MEJLROBOT (B2B-utskick) – cloud_outreach.py + outreach.yml
- ⛔ **PAUSAD 2026-06-27 (på användarens begäran):** schema-cron avkommenterad i outreach.yml (manuell "Run workflow" finns kvar). **Återuppta:** avkommentera `schedule:`-raderna. Innan paus: vardagar 08:00 UTC, 8/varv.
- Skickar via **one.com SMTP** (send.one.com) från **info.solidservice@solidservice.se** (SPF/DKIM/DMARC OK). Mänsklig mall (`build_offer_email`), signerad "Sardor Khikmatov", BCC till egen inkorg.
- Status: **39 prospekt, ~26 i kö**. Secrets satta: SMTP_USER, SMTP_PASS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID=1738443387.

## 🧲 KUND-HITTARE (B2B, auto) – prospect_hunter.py + hunter-prospects.yml
- Frågar OpenStreetMap/Overpass (gratis, ingen nyckel) efter Stockholmsföretag med hemsida → besöker sidan → **skrapar publik mejl som faktiskt står där** (gissar aldrig; role-konto/domän-match; ambassad/myndighet/kyrka bortfiltrerade) → prospects.json som "Att kontakta". Stdlib, inga secrets.
- Schema **mån/ons/fre 06:00 UTC** (MAX_NEW=10). ~20% av besökta sidor ger verifierad mejl. (OBS: matar bara kön – utskicket självt är pausat, se ovan.)

## 🔍 KUND-BEVAKARE (privatpersoner) – cloud_hunter.py + hunter.yml
- Var 3:e timme → skriver träffar till **organic_leads.json** (dashboarden) + Telegram. Färdigt svar anpassas (flytt/kontor/hem/fönster).
- Källor: inbyggda Google News-RSS + **3 Google Alerts RSS** som Claude skapade 2026-06-27 (söker städhjälp / rekommendera städfirma / söker flyttstädning Sthlm, RSS+Alla resultat) och kopplade in via **alert_feeds.txt** (i repot; ALERT_FEEDS-secret behövs ej). Filter kräver BÅDE städ-ord OCH frågar-ord. Reddit = 403 från molnet.
- ⚠️ **Dashboarden är TOM, INTE trasig:** organic_leads.json=0 för att alertsen är nyskapade + få postar offentligt om städ (låg gratis-volym, känt). Fylls på efter hand. Stor volym = Meta lead-ads (budget).

## 📲 TELEGRAM
- Bot **@Solid27277bot**, chat_id **1738443387**. TODO: website-leads → Telegram kräver TELEGRAM-secrets som Render env-vars på web-servicen (ej satt).

## 🏷️ DOMÄN solidservice.se – BLOCKERAD
Ägs (one.com, förnyas 2027-02-24). Redan tillagd i Render (Custom Domains), väntar på DNS. **one.com LÅSER DNS bakom betald uppgradering = enda proppen.** Väg förbi: flytta DNS till **Cloudflare (gratis)**. Cloudflare-konto finns. Domän = DNS-fråga oavsett sajttyp.

## ▶️ NÄSTA STEG / ÖPPET
1. ⛔ Mejlutskick PAUSAT — vänta på användarens klartecken innan återstart (avkommentera schedule i outreach.yml).
2. ✅ Google Alerts skapade + inkopplade (alert_feeds.txt). Bevakaren rullar; dashboard fylls efter hand.
3. 🔀 **ÖPPET A/B-BESLUT (användaren obeslutad):** (A) behåll gratis kod-sajt → lös domänen via Cloudflare + bygg ut adminen (allt gratis, robotarna kvar); ELLER (B) byt till WordPress/hemsidebyggare (klick-admin + enkel domän, men kostar månadsvis + robotarna körs separat).
4. (valfritt) Google Företagsprofil (service-area) = bästa gratis SEO. Meta lead-ads (`/webhook/meta`) för privatvolym.

## ⚖️ REGLER
- Webbläsarstyrning: ENDAST Microsoft Edge (Claude-tillägget = "Browser 2", deviceId 484eb0fe...), ALDRIG Chrome.
- Aldrig fejka mejladresser. Bara inbound/opt-in + B2B med opt-out (företag, ej privatpersoner).
- Användaren skriver alla lösenord/secrets själv; Claude matar aldrig in token/lösen i fält.

## ▶️ STARTA NYA CHATTEN MED:
"Fortsätt Solidservice — läs LIVE-STATUS.md i jword/stadlinjen. Läge: mejlutskick PAUSAT; kund-hittare + organisk bevakare byggda & inkopplade (3 Google Alerts via alert_feeds.txt); dashboard = GitHub Pages /kunder.html (tom men EJ trasig). Öppet: A/B-beslut om sajt/domän (se NÄSTA STEG). Edge endast, aldrig Chrome, aldrig fejk-mejl."
