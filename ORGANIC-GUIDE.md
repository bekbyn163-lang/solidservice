# Hitta kunder – så funkar det nu (allt på autopilot)

Två robotar jobbar åt dig dygnet runt, gratis, på GitHub. Du behöver **inte** be Claude leta längre.

---

## 1. Företagskunder (B2B) – HELT automatiskt, du gör inget

- **Kund-hittaren** (`prospect_hunter.py`) kör mån/ons/fre. Den hittar nya
  Stockholmsföretag (restauranger, kliniker, byråer, gym m.m.) via en gratis
  öppen karttjänst, går in på deras egen hemsida och **plockar ut den riktiga
  mejladressen** (gissar aldrig – då studsar mejlen). Den sparar dem i listan.
- **Mejlroboten** (`cloud_outreach.py`) kör varje vardag 08:00 och mejlar 8 av dem
  med ett personligt erbjudande (signerat Sardor, med avregistrering = lagligt B2B).

👉 Du behöver inte göra något här. Listan fylls på och mejlas av sig själv.

---

## 2. Privatpersoner som söker städ – din "klistra in"-dashboard

**DIN DASHBOARD (öppna i mobilen, spara som bokmärke):**
### 👉 https://solidservicestad.onrender.com/kunder.html

Där dyker personer upp som söker städhjälp. För varje:
1. Tryck **"↗ Öppna inlägget"** → du kommer till deras inlägg.
2. Tryck **"📋 Kopiera svar"** → ett färdigt, vänligt svar kopieras.
3. Klistra in svaret hos dem. Klart. (Du skriver aldrig själv.)

Du får också en **Telegram-pling** direkt när en ny dyker upp.

---

## 3. Det ENDA du själv kan göra (5 min, gör fler privatkunder) – Google Alerts

Roboten kan inte logga in på Facebook/Reddit. Men **Google Alerts** är gratis och
hittar folk som frågar efter städ i forum, bloggar och grupper. Så här kopplar du på det:

**Steg 1 – Skapa bevakningar**
1. Gå till **https://www.google.com/alerts** (logga in med din Gmail).
2. Klistra in i sökrutan, en i taget, och tryck "Skapa avisering" för varje:
   - `söker städhjälp Stockholm`
   - `letar efter städfirma Stockholm`
   - `rekommendera städfirma Stockholm`
   - `flyttstädning Stockholm tips`
3. Innan du skapar, tryck **"Visa alternativ"** och ställ in:
   - Leverera till: **RSS-feed**
   - Hur ofta: **När det händer**
   - Källor: **Automatisk**

**Steg 2 – Kopiera RSS-länkarna**
- När aviseringen är skapad syns en liten **RSS-ikon** bredvid den. Högerklicka →
  "Kopiera länkadress". Gör det för varje avisering. Du får länkar som börjar med
  `https://www.google.com/alerts/feeds/...`

**Steg 3 – Klistra in dem som en "secret" (du gör det själv, jag rör aldrig dina lösenord)**
1. Gå till repo: **https://github.com/bekbyn163-lang/solidservice**
2. **Settings** → (vänster) **Secrets and variables** → **Actions**.
3. Tryck **New repository secret**.
   - Name: `ALERT_FEEDS`
   - Secret: klistra in dina RSS-länkar, **separerade med komma** (ingen mellanslag), t.ex.
     `https://www.google.com/alerts/feeds/123/abc,https://www.google.com/alerts/feeds/123/def`
4. **Add secret**. Klart!

Nu tankar bevakar-roboten dina Google Alerts var 3:e timme och lägger träffarna på
din dashboard + pingar Telegram.

---

## Ärligt om volym

Gratis privatkund-flöde i Sverige är **litet** – de flesta frågar i Facebook-grupper
som ingen robot får läsa lagligt. Google Alerts är den bästa gratis-kranen och fångar
det som går att fånga. Vill du ha **många** privatkunder snabbt är enda riktiga vägen
en liten **Meta-annons** (Facebook/Instagram lead-formulär) med budget – den är redan
förberedd i koden (`/webhook/meta`), säg till när du vill sätta igång den.

Företagssidan (B2B) däremot rullar på helt av sig själv och kostar 0 kr.
