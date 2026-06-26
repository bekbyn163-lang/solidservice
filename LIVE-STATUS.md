# Solidservice – LIVE-status (2026-06-25)

## ✅ SAJTEN ÄR LIVE
**https://solidservice.onrender.com** — fungerar, testad, laddar perfekt.

- **Hosting:** Render (gratis-plan, inget kreditkort). Sover efter 15 min inaktivitet, ~30–50 s kallstart.
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

## Regler
- Webbläsarstyrning: ENDAST Microsoft Edge (Browser 2, deviceId 484eb0fe-ca99-4181-a3a8-131531d1b8dd). ALDRIG Chrome (Browser 1).
- Användaren skriver alla lösenord själv + klickar alla Authorize/OAuth/godkännanden.
- Gränsen (5h) nollställs 2026-06-26 ~02:20 svensk tid.
