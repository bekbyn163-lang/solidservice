# Solidservice – LIVE-status (2026-06-25)

## ✅ SAJTEN ÄR LIVE — SNABB (ingen kallstart)
**Publik sajt (DELA DENNA): https://bekbyn163-lang.github.io/solidservice/**
- Hostas på **GitHub Pages** (gratis, globalt CDN, HTTPS, **öppnas direkt varje gång — ingen 30s-väntan**). Inget extra konto.
- Statisk (index.html/styles.css/script.js/chat.js). Verifierat: CSS 182 regler, chatt-bubbla + kontaktformulär funkar, inga trasiga bilder.

**Backend (chatt/lead + dashboard): https://solidservice.onrender.com**
- Render gratis (sover efter 15 min, ~30–50s kallstart — men det märks BARA när någon skickar ett lead, inte när sidan öppnas).
- chat.js + script.js pekar på `https://solidservice.onrender.com/api/lead` (absolut URL). CORS påslaget i app.py (after_request `*` + OPTIONS-preflight). Commit 22b4552/9412f7b.
- Dashboard: https://solidservice.onrender.com/dashboard
- TODO (valfritt): keep-alive-ping var 10:e min så leads aldrig fastnar i kallstart.

- **Repo:** https://github.com/bekbyn163-lang/solidservice (PUBLIC), branch `master`.
- **Render service-id:** `srv-d8uocrsvikkc73es2rrg` (konto = inloggat via GitHub `bekbyn163-lang`, e-post bekbyn163@gmail.com).
- **Fix som gjordes:** start-kommando = `gunicorn app:app --bind 0.0.0.0:$PORT` (i render.yaml + Procfile + i Render-fältet). Utan `--bind` hittar Render inte appen.
- `config.json`, `leads.json`, `cloudflared.exe` är gitignorerade (följde EJ med — inga hemligheter i molnet). Appen återskapar config från DEFAULT_CONFIG.

## 🌐 EGEN DOMÄN solidservice.se — pågår
**Render-sidan:** Custom Domain `solidservice.se` ÄR redan tillagd i Render (Settings → Custom Domains), väntar på DNS-verifiering.
Render vill ha dessa poster:
| Typ | Namn | Värde |
|-----|------|-------|
| A | @ (root) | `216.24.57.1` |
| CNAME | www | `solidservice.onrender.com` |

### ⛔ BLOCKER hos one.com
- Domänen ligger på one.coms nameservers (`ns01.one.com`, `ns02.one.com`).
- Kontot har bara ett **"E-postpaket"** → one.com **låser DNS-post-editorn bakom betald uppgradering** (sidan dns.do visar bara "Uppgradera nu"; editor-koden finns men är avstängd).
- → Kan INTE lägga in A/CNAME hos one.com utan att betala.

### 🟢 VALD LÖSNING: flytta DNS till Cloudflare (gratis)
Användaren valde detta. Plan:
1. Användaren skapar gratis Cloudflare-konto (signup gör hen själv).
2. Lägg till `solidservice.se` i Cloudflare → den skannar & importerar befintliga poster.
3. **VERIFIERA att mejl-posterna kom med** (annars sluta mejlen funka — KRITISKT):
   - **MX** (pref 10): `mx1.mailpod15-cph3.g1i.one.com`, `mx2.…`, `mx3.…`, `mx4.mailpod15-cph3.g1i.one.com`
   - **TXT @ (SPF):** `v=spf1 include:_custspf.one.com ~all`
   - **TXT _dmarc:** `v=DMARC1; p=reject`
   - (ingen DKIM hittad — inget att missa)
4. Lägg till webb-posterna: **A @ → 216.24.57.1** och **CNAME www → solidservice.onrender.com** (sätt "DNS only"/grå moln så Renders SSL funkar).
5. Byt nameservers hos one.com → Cloudflares 2 nameservers.
6. Tillbaka i Render: klicka **Verify** på custom domain. ~1–2h propagering, sen funkar solidservice.se med gratis SSL.

### ❗ ÖPPEN FRÅGA (där gränsen tog slut)
Höll på att kolla i one.com → **Mina produkter → Hantera (solidservice.se)** om one.com **tillåter byte till externa nameservers**.
- one.com är känt för att ibland LÅSA nameserver-byte. Om det är låst → Cloudflare funkar inte → då återstår: (a) betala one.com-uppgradering, eller (b) använd onrender.com-länken.
- **NÄSTA STEG = bekräfta nameserver-bytet är möjligt hos one.com.**

## ▶️ Starta nästa chatt med
"Fortsätt Solidservice live — läs LIVE-STATUS.md i jword/stadlinjen. Sajten är live på onrender. Vi ska flytta DNS till Cloudflare (gratis) för solidservice.se. Använd Microsoft Edge (Browser 2), ALDRIG Chrome. Kolla först om one.com tillåter nameserver-byte."

## 📧 24/7 B2B-utskicksrobot (byggd 2026-06-25)
- `cloud_outreach.py` + `.github/workflows/outreach.yml` = GitHub Actions skickar 8 B2B-offertmejl/vardag (08:00 UTC) + "Run workflow"-knapp för manuell körning.
- Skickar via **one.com SMTP** (`send.one.com`) från **info@solidservice.se** → SPF/DKIM/DMARC stämmer = ej spam (INTE Gmail – då studsar det pga DMARC p=reject). Proffsig B2B-mall i `build_offer_email()`. Opt-out i varje mejl (lagligt B2B mot företag, ej privatpersoner).
- Återanvänder app.py (load_prospects/build_offer_email/send_email/write_prospects). Markerar "Kontaktad", committar prospects.json tillbaka. 15 riktiga Stockholmsföretag i kön (~2 dagar) – fyll på för mer.
- **GÅ SKARP (användaren gör, jag får ej skriva lösenord):**
  1. one.com → E-post → använd/skapa `info@solidservice.se`, sätt lösenord.
  2. GitHub repo → Settings → Secrets and variables → Actions → lägg `SMTP_USER`=info@solidservice.se och `SMTP_PASS`=lösenordet.
  3. (valfritt) Telegram: `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` som Secrets → leads/utskick pingas till brodern.
  4. Skicka ikväll: Actions-fliken → "B2B-utskick" → Run workflow.
- HEMSIDA städad 2026-06-25: bort med adress, telefon, fejk-recensioner, "600+/4,9", ID06, påhittad historik; "Läs mer"→"Begär offert"; döda länkar fixade; integritetspolicy.html tillagd.

## Regler
- Webbläsarstyrning: ENDAST Microsoft Edge (Browser 2, deviceId 484eb0fe-ca99-4181-a3a8-131531d1b8dd). ALDRIG Chrome (Browser 1).
- Användaren skriver alla lösenord själv + klickar alla Authorize/OAuth/godkännanden.
- Gränsen (5h) nollställs 2026-06-26 ~02:20 svensk tid.
