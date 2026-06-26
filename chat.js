/* ===== Solidservice – Säljchatt (skriptad, $0, ingen AI-nyckel) =====
   Kvalificerar kunden, räknar ut RUT-pris, fångar nummer,
   skickar leadet till backend -> Telegram till din bror. */

(function () {
  // Backend (chatt/lead -> Telegram) körs på Render; sidan kan ligga på CDN (Cloudflare Pages = blixtsnabb)
  const API = "https://solidservice.onrender.com";

  // ---- Prislogik (styrs från dashboarden /dashboard -> Priser) ----
  let HEM_PRIS_TIM = 495;            // kr/tim ord. pris hemstädning
  let RUT = 0.5;                     // 50 % RUT-avdrag
  let HEM_TIMMAR = { "1 rok": 2, "2 rok": 2.5, "3 rok": 3, "4 rok": 3.5, "5+ rok": 4 };
  let FLYTT_PRIS = { "1 rok": 1800, "2 rok": 2600, "3 rok": 3400, "4 rok": 4400, "5+ rok": 5400 };

  // Hämta aktuella priser från dashboarden (om servern kör)
  fetch(API + "/api/pricing").then(r => r.json()).then(p => {
    if (p.hem_pris_tim) HEM_PRIS_TIM = p.hem_pris_tim;
    if (typeof p.rut === "number") RUT = p.rut;
    if (p.hem_timmar) HEM_TIMMAR = p.hem_timmar;
    if (p.flytt_pris) FLYTT_PRIS = p.flytt_pris;
  }).catch(() => {});

  function kr(n) { return Math.round(n).toLocaleString("sv-SE") + " kr"; }

  // ---- Konversationsflöde ----
  const lead = { service: "", size: "", frequency: "", area: "", name: "", phone: "", email: "", price: "", message: "", source: "chatt" };
  let step = 0;

  const flow = [
    {
      bot: "Hej och välkommen till Solidservice! 👋 Vad behöver du hjälp med?",
      options: ["Hemstädning", "Flyttstädning", "Kontorsstädning", "Fönsterputs", "Annat"],
      key: "service",
    },
    {
      bot: (l) => l.service === "Kontorsstädning"
        ? "Toppen! Ungefär hur stor är lokalen?"
        : "Vad bra! Hur stor är bostaden?",
      options: (l) => l.service === "Kontorsstädning"
        ? ["< 100 m²", "100–300 m²", "300–600 m²", "> 600 m²"]
        : ["1 rok", "2 rok", "3 rok", "4 rok", "5+ rok"],
      key: "size",
    },
    {
      bot: (l) => (l.service === "Hemstädning" || l.service === "Kontorsstädning")
        ? "Hur ofta vill du ha städning?"
        : "När behöver du det utfört?",
      options: (l) => (l.service === "Hemstädning" || l.service === "Kontorsstädning")
        ? ["Varje vecka", "Varannan vecka", "En gång i månaden", "Engångsstäd"]
        : ["Så snart som möjligt", "Inom 1–2 veckor", "Flexibelt"],
      key: "frequency",
    },
    {
      bot: "I vilket område? (t.ex. Solna, Bromma, Södermalm...)",
      input: "text",
      placeholder: "Ditt område",
      key: "area",
      priceAfter: true,
    },
    {
      bot: "Perfekt – vi kan absolut hjälpa dig! 🙌 Vad heter du?",
      input: "text",
      placeholder: "Ditt namn",
      key: "name",
    },
    {
      bot: (l) => `Tack ${l.name.split(" ")[0]}! Vilket nummer når vi dig bäst på? Vi ringer och bokar in en tid som passar.`,
      input: "tel",
      placeholder: "07X-XXX XX XX",
      key: "phone",
    },
    {
      bot: "Sista frågan – din e-post? (frivilligt, för att skicka bekräftelse)",
      input: "email",
      placeholder: "din@epost.se",
      key: "email",
      optional: true,
    },
  ];

  function estimatePrice(l) {
    if (l.service === "Hemstädning") {
      const tim = HEM_TIMMAR[l.size] || 2.5;
      const ord = tim * HEM_PRIS_TIM;
      return `ca ${kr(ord * RUT)}/tillfälle efter RUT (${kr(ord)} före)`;
    }
    if (l.service === "Flyttstädning") {
      const p = FLYTT_PRIS[l.size] || 2600;
      return `ca ${kr(p * RUT)} efter RUT (${kr(p)} före)`;
    }
    if (l.service === "Fönsterputs") return "från 0 kr efter RUT – offert ges direkt";
    return "kostnadsfri offert inom 24h";
  }

  // ---- UI ----
  const wrap = document.createElement("div");
  wrap.className = "slc";
  wrap.innerHTML = `
    <button class="slc__bubble" id="slcBubble" aria-label="Öppna chatt">
      <span class="slc__bubble-icon">💬</span>
      <span class="slc__bubble-txt">Få offert direkt</span>
    </button>
    <div class="slc__panel" id="slcPanel">
      <div class="slc__head">
        <div class="slc__avatar">S</div>
        <div><strong>Solidservice</strong><span>Svarar direkt · ⭐ 4,9</span></div>
        <button class="slc__close" id="slcClose">✕</button>
      </div>
      <div class="slc__body" id="slcBody"></div>
      <div class="slc__foot" id="slcFoot"></div>
    </div>`;
  document.body.appendChild(wrap);

  const panel = wrap.querySelector("#slcPanel");
  const body = wrap.querySelector("#slcBody");
  const foot = wrap.querySelector("#slcFoot");

  function open() { panel.classList.add("open"); if (!body.dataset.started) { body.dataset.started = "1"; render(); } }
  function close() { panel.classList.remove("open"); }
  wrap.querySelector("#slcBubble").addEventListener("click", open);
  wrap.querySelector("#slcClose").addEventListener("click", close);

  function addBot(text) {
    const d = document.createElement("div");
    d.className = "slc__msg slc__msg--bot";
    d.textContent = text;
    body.appendChild(d);
    body.scrollTop = body.scrollHeight;
  }
  function addUser(text) {
    const d = document.createElement("div");
    d.className = "slc__msg slc__msg--user";
    d.textContent = text;
    body.appendChild(d);
    body.scrollTop = body.scrollHeight;
  }

  function val(x, l) { return typeof x === "function" ? x(l) : x; }

  function render() {
    foot.innerHTML = "";
    if (step >= flow.length) return finish();
    const s = flow[step];
    addBot(val(s.bot, lead));

    if (s.priceAfter && lead.service) {
      lead.price = estimatePrice(lead);
    }

    if (s.options) {
      const opts = val(s.options, lead);
      opts.forEach((o) => {
        const b = document.createElement("button");
        b.className = "slc__opt";
        b.textContent = o;
        b.addEventListener("click", () => {
          addUser(o);
          lead[s.key] = o;
          step++;
          maybePriceReveal(s);
          render();
        });
        foot.appendChild(b);
      });
    } else if (s.input) {
      const formEl = document.createElement("form");
      formEl.className = "slc__inputrow";
      formEl.innerHTML = `<input type="${s.input}" placeholder="${s.placeholder}" ${s.optional ? "" : "required"}>
        <button type="submit">→</button>`;
      formEl.addEventListener("submit", (e) => {
        e.preventDefault();
        const v = formEl.querySelector("input").value.trim();
        if (!v && !s.optional) return;
        if (v) { addUser(v); lead[s.key] = v; }
        else addUser("(hoppar över)");
        step++;
        maybePriceReveal(s);
        render();
      });
      foot.appendChild(formEl);
      setTimeout(() => formEl.querySelector("input").focus(), 50);
    }
  }

  function maybePriceReveal(s) {
    if (s.priceAfter) {
      lead.price = estimatePrice(lead);
      setTimeout(() => addBot(`💰 Ungefärligt pris för dig: ${lead.price}. (Exakt offert ges vid bokning – inga dolda avgifter.)`), 250);
    }
  }

  function finish() {
    addBot("Tusen tack! 🎉 Vi har tagit emot din förfrågan och ringer dig inom kort för att boka in en tid. Ha en fin dag!");
    // skicka till backend
    fetch(API + "/api/lead", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(lead),
    }).catch(() => {});
    const done = document.createElement("div");
    done.className = "slc__done";
    done.innerHTML = `✅ Skickat! Vi hör av oss på <b>${lead.phone || "ditt nummer"}</b>.`;
    foot.appendChild(done);
  }
})();
