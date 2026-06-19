# Städlinjen AB – Lead-motor 🧽

En komplett, gratis och **laglig** lead-maskin för städfirman.

## Vad den gör
1. Visar hemsidan med en **säljchatt** nere i hörnet.
2. Chatten frågar kunden om tjänst, storlek, hur ofta och område, **räknar ut ett RUT-pris direkt**, och fångar namn + telefon.
3. Hela leadet skickas **direkt till din bror på Telegram** + sparas i en dashboard.
4. Kontaktformuläret skickar också leads samma väg.

> ⚖️ **Lagligt:** Den här motorn jobbar bara med kunder som **själva** hör av sig (inbound). Den ringer/SMSar aldrig kalla privatpersoner – det vore olagligt (NIX, GDPR, Marknadsföringslagen).

---

## 🚀 Kom igång (2 minuter)

1. **Dubbelklicka `START.bat`**
2. Öppna **http://localhost:8810** → hemsidan med chatten
3. Öppna **http://localhost:8810/dashboard** → alla leads

Första gången skapas `config.json` automatiskt.

---

## 📲 Koppla Telegram till din bror (engångs, gratis)

Så att din bror får varje lead direkt i mobilen:

1. Be din bror öppna Telegram och söka upp **@BotFather**.
2. Skicka `/newbot` → följ stegen → kopiera **bot-token** (typ `8123456:AAH...`).
3. Sök upp er nya bot i Telegram och tryck **Start**.
4. Hämta **chat-id:t**: öppna i webbläsaren
   `https://api.telegram.org/bot<DIN_TOKEN>/getUpdates`
   och leta efter `"chat":{"id": 123456789`. Det numret är chat-id:t.
5. Öppna **`config.json`** och klistra in:
   ```json
   {
     "telegram_bot_token": "8123456:AAH...",
     "telegram_chat_id": "123456789"
   }
   ```
6. Starta om `START.bat`. Klart! Nästa lead plingar i din brors Telegram. 📲

*(Vill din bror ha det i en grupp där ni båda ser leads – lägg till boten i en Telegram-grupp och använd gruppens chat-id istället.)*

---

## ⚙️ Justera priser
Öppna `chat.js` högst upp – ändra `HEM_PRIS_TIM` (kr/tim) och `FLYTT_PRIS` till era riktiga priser.

## 🔧 Byt kontaktuppgifter
Telefon, e-post, adress, org.nr finns i `index.html` (sök efter `08-559` och `info@stadlinjen`).

---

## Nästa steg (säg till så bygger jag)
- 📤 B2B-mejl-agent för kontorsstädning (lagligt, mot företag)
- 🔍 Bevakning av Offerta/Servicefinder/Städa.se
- 🌐 Lägga sajten live på en riktig domän (stadlinjen.se)
