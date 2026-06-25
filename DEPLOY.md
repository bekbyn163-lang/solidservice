# Lägga Solidsurvice LIVE 🌐

Du har **två sätt**. Börja med det snabba, gå till det permanenta när du vill.

---

## ⚡ Sätt 1: Live direkt (gratis, ingen registrering)

**Dubbelklicka `GO-LIVE.bat`.**

Det startar sajten och skapar en publik länk som ser ut så här:
```
https://nagot-nagot.trycloudflare.com
```
- Dela den länken / lägg in den där kunder ser den.
- Kunder öppnar den, chattar → du + din bror får leadet (Telegram + dashboard).
- **Låt fönstret vara öppet** så länge du vill vara live.

> Bra för att testa och köra igång snabbt. Nackdel: länken byts varje gång du startar om, och sajten är bara uppe medan din dator + fönstret är på.

---

## 🏆 Sätt 2: Permanent adress (gratis, alltid på) – Render

Sajten ligger då på nätet dygnet runt, även när din dator är avstängd. Tar ~10 min en gång.

### Steg
1. Skapa gratis konto på **https://github.com** och **https://render.com** (logga in på Render med GitHub).
2. Skapa ett nytt repo på GitHub (t.ex. `stadlinjen`) – **Public**.
3. Ladda upp alla filer i den här mappen till repot (dra-och-släpp funkar på github.com → "uploading an existing file").
   - Hoppa över `cloudflared.exe` (för stor och behövs inte i molnet).
4. På Render: **New → Web Service → Build and deploy from a Git repository →** välj ditt repo.
   - Render läser `render.yaml` automatiskt. Tryck **Create**.
5. Efter ~2 min får du en adress: `https://stadlinjen.onrender.com` ← **det är din live-sajt.**
6. Gå till `https://stadlinjen.onrender.com/dashboard → Telegram` och klistra in bot-token + chat-id. Klart!

### Egen domän (stadlinjen.se)
Köp domänen (~150 kr/år hos t.ex. Loopia/one.com) → i Render: **Settings → Custom Domain →** följ instruktionen. Säg till så hjälper jag dig.

> ⚠️ **Obs om gratis-Render:** efter 15 min utan besök "somnar" sajten och första besöket tar ~30 sek att vakna. Och dashboardens lead-historik kan nollställas vid omstart – men **din bror missar aldrig ett lead, för allt skickas direkt till Telegram.** Vill du ha permanent lead-historik fixar jag en gratis databas – säg bara till.

---

## Vad händer med leads?
Oavsett sätt: varje lead → **Telegram till din bror direkt** + syns i **/dashboard**. Telegram är den säkra kanalen som alltid funkar.
