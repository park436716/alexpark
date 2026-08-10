"""Build a self-contained prototype HTML with rules + 100 contexts embedded.

Reads ../data/rules.json and ../data/contexts.json, injects both as JSON
script blocks, writes index.html next to this file. Re-run whenever data
changes.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE.parent / "data"
OUT = HERE / "index.html"

RULES = (DATA / "rules.json").read_text()
CONTEXTS = (DATA / "contexts.json").read_text()

TEMPLATE = r"""<title>Chargeback Triage — Prototype</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {
    --ground: #F5F6F8;
    --surface: #FFFFFF;
    --surface-2: #FAFBFC;
    --ink: #0E1420;
    --ink-2: #2B3444;
    --muted: #5B6577;
    --hairline: #EEF0F3;
    --border: #DFE3EA;
    --accent: #2F5FE0;
    --accent-ink: #FFFFFF;
    --accent-tint: #EAF0FE;
    --focus: #2F5FE0;

    --cat-fraud: #B23A48;
    --cat-fraud-tint: #FCEEF0;
    --cat-auth: #B67B00;
    --cat-auth-tint: #FBF3E1;
    --cat-proc: #5E5B7B;
    --cat-proc-tint: #EEEDF5;
    --cat-consumer: #2F7A5E;
    --cat-consumer-tint: #E8F3EE;

    --net-visa: #1A1F71;
    --net-mc:   #B8001A;
    --net-amex: #2E77BB;

    --shadow-1: 0 1px 0 rgba(14,20,32,.03), 0 1px 2px rgba(14,20,32,.04);
    --shadow-2: 0 2px 4px rgba(14,20,32,.04), 0 8px 24px rgba(14,20,32,.06);

    --radius: 10px;
    --radius-sm: 6px;
    --gap: 16px;

    --font-ui: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, "Helvetica Neue", Arial, sans-serif;
    --font-mono: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
    --font-serif: "Iowan Old Style", "Palatino Linotype", Georgia, serif;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --ground: #0B0F17;
      --surface: #141A25;
      --surface-2: #10151E;
      --ink: #E7EAF0;
      --ink-2: #C1C7D2;
      --muted: #8A93A3;
      --hairline: #1A2130;
      --border: #232B3D;
      --accent: #7A9BFF;
      --accent-ink: #0B0F17;
      --accent-tint: #1A2340;
      --focus: #7A9BFF;

      --cat-fraud: #E88893;
      --cat-fraud-tint: #2B1519;
      --cat-auth: #E5B457;
      --cat-auth-tint: #2A2210;
      --cat-proc: #A8A4C7;
      --cat-proc-tint: #1E1B2B;
      --cat-consumer: #7BC3A2;
      --cat-consumer-tint: #14251E;

      --net-visa: #6C74C7;
      --net-mc:   #E86775;
      --net-amex: #6FA9DF;

      --shadow-1: 0 1px 0 rgba(0,0,0,.4);
      --shadow-2: 0 2px 4px rgba(0,0,0,.3), 0 12px 32px rgba(0,0,0,.35);
    }
  }
  :root[data-theme="dark"] {
    --ground: #0B0F17;
    --surface: #141A25;
    --surface-2: #10151E;
    --ink: #E7EAF0;
    --ink-2: #C1C7D2;
    --muted: #8A93A3;
    --hairline: #1A2130;
    --border: #232B3D;
    --accent: #7A9BFF;
    --accent-ink: #0B0F17;
    --accent-tint: #1A2340;
    --focus: #7A9BFF;

    --cat-fraud: #E88893;
    --cat-fraud-tint: #2B1519;
    --cat-auth: #E5B457;
    --cat-auth-tint: #2A2210;
    --cat-proc: #A8A4C7;
    --cat-proc-tint: #1E1B2B;
    --cat-consumer: #7BC3A2;
    --cat-consumer-tint: #14251E;

    --net-visa: #6C74C7;
    --net-mc:   #E86775;
    --net-amex: #6FA9DF;

    --shadow-1: 0 1px 0 rgba(0,0,0,.4);
    --shadow-2: 0 2px 4px rgba(0,0,0,.3), 0 12px 32px rgba(0,0,0,.35);
  }

  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body {
    background: var(--ground);
    color: var(--ink);
    font-family: var(--font-ui);
    font-size: 14px;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
  }
  a { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }
  :focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; border-radius: 4px; }

  .app {
    display: grid;
    grid-template-rows: auto 1fr;
    min-height: 100vh;
  }

  header.top {
    position: sticky; top: 0; z-index: 10;
    background: color-mix(in srgb, var(--surface) 92%, transparent);
    backdrop-filter: saturate(140%) blur(8px);
    -webkit-backdrop-filter: saturate(140%) blur(8px);
    border-bottom: 1px solid var(--border);
    padding: 12px 24px;
    display: flex; align-items: center; gap: 24px;
  }
  .wordmark {
    display: flex; align-items: baseline; gap: 10px;
  }
  .wordmark .glyph {
    font-family: var(--font-serif);
    font-weight: 400;
    font-size: 22px;
    letter-spacing: -0.01em;
    color: var(--ink);
  }
  .wordmark .glyph em { font-style: italic; color: var(--accent); font-weight: 400; }
  .wordmark .kicker {
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
    padding: 3px 8px;
    border: 1px solid var(--border);
    border-radius: 999px;
  }
  .top .spacer { flex: 1; }
  .legend {
    display: flex; gap: 14px; align-items: center;
    font-family: var(--font-mono); font-size: 11px; color: var(--muted);
  }
  .legend .chip { display: inline-flex; align-items: center; gap: 6px; }
  .legend .swatch {
    width: 8px; height: 8px; border-radius: 2px; display: inline-block;
  }
  .swatch.visa { background: var(--net-visa); }
  .swatch.mc   { background: var(--net-mc); }
  .swatch.amex { background: var(--net-amex); }
  .theme-toggle {
    font: inherit; font-size: 12px;
    color: var(--muted); background: transparent; border: 1px solid var(--border);
    padding: 6px 10px; border-radius: 999px; cursor: pointer;
  }
  .theme-toggle:hover { color: var(--ink); border-color: var(--ink-2); }

  main {
    display: grid;
    grid-template-columns: 360px 1fr;
    gap: 24px;
    padding: 24px;
    max-width: 1400px;
    width: 100%;
    margin: 0 auto;
  }
  @media (max-width: 960px) {
    main { grid-template-columns: 1fr; }
  }

  aside.rail {
    display: flex; flex-direction: column; gap: 16px;
    align-self: start;
    position: sticky; top: 72px;
  }
  @media (max-width: 960px) { aside.rail { position: static; } }

  .panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 18px;
    box-shadow: var(--shadow-1);
  }
  .panel h2 {
    margin: 0 0 12px 0;
    font-size: 12px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    font-weight: 600;
  }

  label { display: block; font-size: 12px; color: var(--muted); margin-bottom: 6px; }
  textarea, input[type="text"], select {
    width: 100%;
    padding: 10px 12px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    color: var(--ink);
    border-radius: var(--radius-sm);
    font: inherit;
    font-size: 13.5px;
  }
  textarea { min-height: 84px; resize: vertical; }
  textarea:focus, input:focus, select:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-tint);
  }

  .row { display: flex; gap: 8px; }
  .row > * { flex: 1; min-width: 0; }

  button.primary {
    display: inline-flex; align-items: center; justify-content: center; gap: 8px;
    padding: 10px 14px;
    background: var(--accent);
    color: var(--accent-ink);
    border: 1px solid var(--accent);
    border-radius: var(--radius-sm);
    font: inherit; font-weight: 600; font-size: 13.5px;
    cursor: pointer;
    transition: transform .06s ease;
  }
  button.primary:hover { filter: brightness(1.02); }
  button.primary:active { transform: translateY(1px); }
  button.ghost {
    padding: 8px 12px;
    background: transparent; color: var(--ink-2);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    font: inherit; font-size: 12.5px;
    cursor: pointer;
  }
  button.ghost.active { background: var(--accent-tint); border-color: var(--accent); color: var(--accent); }
  button.ghost:hover { border-color: var(--ink-2); }

  .stack { display: flex; flex-direction: column; gap: 12px; }
  .field-stack { display: flex; flex-direction: column; gap: 10px; }

  .chip-row { display: flex; flex-wrap: wrap; gap: 6px; }
  .filter-chip {
    font-family: var(--font-mono); font-size: 11px;
    padding: 5px 9px; border-radius: 999px;
    border: 1px solid var(--border); background: var(--surface-2);
    color: var(--muted); cursor: pointer; letter-spacing: .02em;
  }
  .filter-chip[aria-pressed="true"] {
    background: var(--accent-tint); border-color: var(--accent); color: var(--accent);
  }
  .filter-chip:hover { border-color: var(--ink-2); color: var(--ink-2); }

  .quick-help {
    font-size: 12px; color: var(--muted);
    padding-top: 4px;
  }
  .quick-help code {
    font-family: var(--font-mono); font-size: 11.5px;
    background: var(--surface-2); border: 1px solid var(--border);
    padding: 1px 5px; border-radius: 4px; color: var(--ink-2);
  }

  section.results { display: flex; flex-direction: column; gap: 18px; min-width: 0; }

  .result-meta {
    display: flex; align-items: center; justify-content: space-between;
    color: var(--muted); font-size: 12px;
  }
  .result-meta .count {
    font-family: var(--font-mono); font-variant-numeric: tabular-nums;
    color: var(--ink-2);
  }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow-1);
    overflow: hidden;
    display: grid;
    grid-template-columns: 4px 1fr;
  }
  .card .stripe { background: var(--border); }
  .card.net-visa .stripe { background: var(--net-visa); }
  .card.net-mc   .stripe { background: var(--net-mc); }
  .card.net-amex .stripe { background: var(--net-amex); }
  .card.net-comparison .stripe {
    background: linear-gradient(180deg, var(--net-visa) 0%, var(--net-visa) 33%, var(--net-mc) 33%, var(--net-mc) 66%, var(--net-amex) 66%, var(--net-amex) 100%);
  }
  .card .body { padding: 18px 20px; display: flex; flex-direction: column; gap: 14px; }

  .card-header {
    display: flex; align-items: flex-start; justify-content: space-between; gap: 16px;
  }
  .card-title {
    font-size: 15px; font-weight: 600; color: var(--ink); margin: 0;
    text-wrap: balance;
  }
  .card-sub {
    font-family: var(--font-mono); font-size: 11px; color: var(--muted);
    letter-spacing: 0.04em; text-transform: uppercase; margin-top: 3px;
  }
  .card-score {
    font-family: var(--font-mono); font-size: 11px; color: var(--muted);
    white-space: nowrap;
  }

  .question {
    font-size: 13.5px; color: var(--ink-2);
    padding: 12px 14px;
    background: var(--surface-2);
    border-left: 2px solid var(--border);
    border-radius: 4px;
  }
  .question .q-mark {
    font-family: var(--font-serif); font-style: italic; font-size: 15px;
    color: var(--muted); margin-right: 6px;
  }

  .answer-grid {
    display: grid;
    grid-template-columns: auto 1fr;
    column-gap: 14px;
    row-gap: 10px;
    align-items: baseline;
    font-size: 13.5px;
  }
  .answer-grid dt {
    color: var(--muted);
    font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase;
    font-weight: 600;
    padding-top: 2px;
    white-space: nowrap;
  }
  .answer-grid dd { margin: 0; color: var(--ink); }

  .mono { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
  .code-pill {
    display: inline-block;
    font-family: var(--font-mono);
    font-size: 13px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 4px;
    background: var(--accent-tint);
    color: var(--accent);
    letter-spacing: 0.02em;
  }

  .cat {
    display: inline-block;
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 999px;
    font-weight: 600;
    letter-spacing: 0.02em;
  }
  .cat-fraud            { background: var(--cat-fraud-tint);    color: var(--cat-fraud); }
  .cat-authorization    { background: var(--cat-auth-tint);     color: var(--cat-auth); }
  .cat-processing_error { background: var(--cat-proc-tint);     color: var(--cat-proc); }
  .cat-consumer_dispute { background: var(--cat-consumer-tint); color: var(--cat-consumer); }

  .net-label {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 12px; font-weight: 600;
  }
  .net-label .dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
  .net-label.visa .dot { background: var(--net-visa); }
  .net-label.mc   .dot { background: var(--net-mc); }
  .net-label.amex .dot { background: var(--net-amex); }

  ul.evidence {
    margin: 0; padding: 0; list-style: none;
    display: grid; grid-template-columns: 1fr 1fr; gap: 4px 20px;
  }
  @media (max-width: 720px) { ul.evidence { grid-template-columns: 1fr; } }
  ul.evidence li {
    font-size: 12.5px; color: var(--ink-2);
    padding-left: 16px; position: relative;
    line-height: 1.45;
  }
  ul.evidence li::before {
    content: ""; position: absolute; left: 0; top: 0.6em;
    width: 4px; height: 4px; background: var(--muted); border-radius: 50%;
  }

  .compare-grid {
    display: grid; grid-template-columns: repeat(3, minmax(0,1fr));
    gap: 12px;
  }
  @media (max-width: 720px) { .compare-grid { grid-template-columns: 1fr; } }
  .compare-cell {
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 12px 14px;
    background: var(--surface-2);
    display: flex; flex-direction: column; gap: 8px;
    border-top: 3px solid var(--border);
  }
  .compare-cell.visa { border-top-color: var(--net-visa); }
  .compare-cell.mc   { border-top-color: var(--net-mc); }
  .compare-cell.amex { border-top-color: var(--net-amex); }
  .compare-cell .code {
    font-family: var(--font-mono); font-size: 15px; font-weight: 600; color: var(--ink);
  }
  .compare-cell .t {
    font-size: 12.5px; color: var(--ink-2); line-height: 1.4;
  }
  .compare-cell .meta {
    font-family: var(--font-mono); font-size: 11px; color: var(--muted);
    display: flex; justify-content: space-between; gap: 8px;
  }

  .source {
    font-family: var(--font-mono); font-size: 11px; color: var(--muted);
    padding-top: 4px; border-top: 1px dashed var(--hairline);
    display: flex; justify-content: space-between; align-items: center;
  }
  .source .path { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

  .empty {
    padding: 40px 24px;
    text-align: center; color: var(--muted);
    border: 1px dashed var(--border);
    border-radius: var(--radius);
    background: var(--surface);
  }
  .empty .em {
    font-family: var(--font-serif); font-style: italic; font-size: 18px;
    color: var(--ink-2); display: block; margin-bottom: 6px;
  }

  footer.foot {
    max-width: 1400px; margin: 0 auto; padding: 12px 24px 32px;
    font-family: var(--font-mono); font-size: 11px; color: var(--muted);
    display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap;
  }

  @media (prefers-reduced-motion: reduce) {
    * { transition: none !important; animation: none !important; }
  }
</style>

<script id="rules-data" type="application/json">__RULES_JSON__</script>
<script id="contexts-data" type="application/json">__CONTEXTS_JSON__</script>

<div class="app">
  <header class="top">
    <div class="wordmark">
      <span class="glyph">Chargeback <em>Triage</em></span>
      <span class="kicker">Prototype · MCP-backed</span>
    </div>
    <div class="spacer"></div>
    <div class="legend" aria-hidden="true">
      <span class="chip"><span class="swatch visa"></span>Visa</span>
      <span class="chip"><span class="swatch mc"></span>Mastercard</span>
      <span class="chip"><span class="swatch amex"></span>Amex</span>
    </div>
    <button class="theme-toggle" id="themeToggle" type="button">Theme</button>
  </header>

  <main>
    <aside class="rail">
      <div class="panel">
        <h2>Ask</h2>
        <div class="field-stack">
          <div>
            <label for="ask">Describe the scenario</label>
            <textarea id="ask" placeholder="e.g. Cardholder never received the item, paid with Visa"></textarea>
          </div>
          <div class="chip-row" id="netFilters" role="group" aria-label="Network filter">
            <button class="filter-chip" data-net="all" aria-pressed="true">All networks</button>
            <button class="filter-chip" data-net="visa" aria-pressed="false">Visa</button>
            <button class="filter-chip" data-net="mastercard" aria-pressed="false">Mastercard</button>
            <button class="filter-chip" data-net="amex" aria-pressed="false">Amex</button>
            <button class="filter-chip" data-net="comparison" aria-pressed="false">Cross-network</button>
          </div>
          <div class="row">
            <button class="primary" id="searchBtn" type="button">Find matches</button>
            <button class="ghost" id="clearBtn" type="button">Clear</button>
          </div>
          <div class="quick-help">
            Try: <code>duplicate</code>, <code>counterfeit</code>, <code>subscription cancelled</code>,
            <code>chargeback for defective</code>
          </div>
        </div>
      </div>

      <div class="panel">
        <h2>Direct lookup</h2>
        <div class="field-stack">
          <div class="row">
            <div>
              <label for="netSel">Network</label>
              <select id="netSel">
                <option value="visa">Visa</option>
                <option value="mastercard">Mastercard</option>
                <option value="amex">Amex</option>
              </select>
            </div>
            <div>
              <label for="codeSel">Reason code</label>
              <select id="codeSel"></select>
            </div>
          </div>
          <button class="primary" id="lookupBtn" type="button">Look up</button>
        </div>
      </div>

      <div class="panel">
        <h2>Scenario compare</h2>
        <div class="field-stack">
          <div>
            <label for="catSel">Scenario category</label>
            <select id="catSel"></select>
          </div>
          <button class="primary" id="compareBtn" type="button">Compare across networks</button>
        </div>
      </div>
    </aside>

    <section class="results" id="results" aria-live="polite">
      <!-- rendered by JS -->
    </section>
  </main>

  <footer class="foot">
    <div>chargeback-mcp/prototype · 48 codes · 100 contexts · rule PDFs served from internal://</div>
    <div>keyword-overlap retrieval — swap in embeddings for production</div>
  </footer>
</div>

<script>
(function () {
  "use strict";

  const RULES = JSON.parse(document.getElementById("rules-data").textContent);
  const CONTEXTS = JSON.parse(document.getElementById("contexts-data").textContent);

  const NET_NAME = { visa: "Visa", mastercard: "Mastercard", amex: "American Express" };
  const NET_CSS  = { visa: "visa",  mastercard: "mc",         amex: "amex" };

  // ---- Theme toggle ----------------------------------------------------
  const root = document.documentElement;
  const themeBtn = document.getElementById("themeToggle");
  function nextTheme() {
    const cur = root.getAttribute("data-theme");
    if (cur === "dark")  return "light";
    if (cur === "light") return "dark";
    // no attr yet — invert whatever the OS gave us
    return matchMedia("(prefers-color-scheme: dark)").matches ? "light" : "dark";
  }
  themeBtn.addEventListener("click", () => {
    root.setAttribute("data-theme", nextTheme());
  });

  // ---- Populate selects -----------------------------------------------
  const netSel = document.getElementById("netSel");
  const codeSel = document.getElementById("codeSel");
  const catSel = document.getElementById("catSel");

  function fillCodes(netKey) {
    const codes = RULES.networks[netKey].reason_codes;
    codeSel.innerHTML = "";
    Object.entries(codes).forEach(([code, rc]) => {
      const opt = document.createElement("option");
      opt.value = code;
      opt.textContent = `${code} — ${rc.title}`;
      codeSel.appendChild(opt);
    });
  }
  fillCodes(netSel.value);
  netSel.addEventListener("change", () => fillCodes(netSel.value));

  const categories = Array.from(new Set(CONTEXTS.map(c => c.category))).sort();
  categories.forEach(cat => {
    const opt = document.createElement("option");
    opt.value = cat;
    opt.textContent = cat.replace(/_/g, " ");
    catSel.appendChild(opt);
  });

  // ---- Filter chips ---------------------------------------------------
  let activeNet = "all";
  document.querySelectorAll("#netFilters .filter-chip").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#netFilters .filter-chip").forEach(b => b.setAttribute("aria-pressed", "false"));
      btn.setAttribute("aria-pressed", "true");
      activeNet = btn.dataset.net;
    });
  });

  // ---- Retrieval ------------------------------------------------------
  function tokenize(s) {
    return new Set(String(s).toLowerCase().split(/[^a-z0-9]+/).filter(t => t.length > 2));
  }
  function score(qTokens, ctx) {
    const c = tokenize(ctx.question);
    let s = 0;
    qTokens.forEach(t => { if (c.has(t)) s++; });
    return s;
  }
  function retrieve(query, netFilter, k = 4) {
    const q = tokenize(query);
    if (!q.size) return [];
    let pool = CONTEXTS;
    if (netFilter && netFilter !== "all") {
      pool = pool.filter(c => c.network === netFilter);
    }
    return pool
      .map(c => [score(q, c), c])
      .filter(([s]) => s > 0)
      .sort((a, b) => b[0] - a[0] || a[1].id.localeCompare(b[1].id))
      .slice(0, k)
      .map(([s, c]) => ({ score: s, ctx: c }));
  }

  // ---- Rendering helpers ----------------------------------------------
  const el = (tag, attrs = {}, ...children) => {
    const n = document.createElement(tag);
    Object.entries(attrs).forEach(([k, v]) => {
      if (k === "class") n.className = v;
      else if (k === "html") n.innerHTML = v;
      else n.setAttribute(k, v);
    });
    children.flat().forEach(c => {
      if (c == null) return;
      n.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
    return n;
  };

  function evidenceList(items) {
    const ul = el("ul", { class: "evidence" });
    (items || []).forEach(i => ul.appendChild(el("li", {}, i)));
    return ul;
  }

  function renderSingleAnswerCard(ctx, scoreVal) {
    const a = ctx.answer;
    const netCss = NET_CSS[ctx.network] || "";
    const netLabel = NET_NAME[ctx.network] || ctx.network;

    const card = el("article", { class: `card net-${netCss}` });
    card.appendChild(el("div", { class: "stripe" }));

    const body = el("div", { class: "body" });

    // header
    const header = el("div", { class: "card-header" });
    const title = el("div", {},
      el("h3", { class: "card-title" }, a.reason_title || "—"),
      el("div", { class: "card-sub" },
        el("span", { class: `net-label ${netCss}` }, el("span", { class: "dot" }), netLabel),
        " · ",
        a.framework || ""
      )
    );
    const scoreEl = scoreVal != null
      ? el("span", { class: "card-score" }, `match ${scoreVal}`)
      : null;
    header.appendChild(title);
    if (scoreEl) header.appendChild(scoreEl);
    body.appendChild(header);

    // question
    body.appendChild(el("div", { class: "question" },
      el("span", { class: "q-mark" }, "Q"),
      ctx.question
    ));

    // grid of facts
    const dl = el("dl", { class: "answer-grid" });
    dl.appendChild(el("dt", {}, "Reason code"));
    dl.appendChild(el("dd", {},
      el("span", { class: "code-pill" }, a.reason_code || "—")
    ));
    dl.appendChild(el("dt", {}, "Category"));
    dl.appendChild(el("dd", {},
      el("span", { class: `cat cat-${a.category}` }, (a.category || "").replace(/_/g, " "))
    ));
    dl.appendChild(el("dt", {}, "Filing window"));
    dl.appendChild(el("dd", { class: "mono" },
      a.time_limit_days != null ? `${a.time_limit_days} days` : "—"
    ));
    dl.appendChild(el("dt", {}, "Pre-arb"));
    dl.appendChild(el("dd", {}, a.requires_pre_arbitration ? "Required" : "Not required"));
    body.appendChild(dl);

    // evidence
    body.appendChild(el("div", {},
      el("div", { class: "card-sub", style: "margin-bottom: 8px" }, "Evidence to defend"),
      evidenceList(a.evidence_checklist)
    ));

    // source
    body.appendChild(el("div", { class: "source" },
      el("span", { class: "path" }, a.source_ref || ""),
      el("span", {}, ctx.id)
    ));

    card.appendChild(body);
    return card;
  }

  function renderComparisonCard(ctx) {
    const card = el("article", { class: "card net-comparison" });
    card.appendChild(el("div", { class: "stripe" }));

    const body = el("div", { class: "body" });
    body.appendChild(el("div", { class: "card-header" },
      el("div", {},
        el("h3", { class: "card-title" }, `Cross-network view: ${ctx.category.replace(/_/g, " ")}`),
        el("div", { class: "card-sub" }, "Visa · Mastercard · Amex")
      )
    ));
    body.appendChild(el("div", { class: "question" },
      el("span", { class: "q-mark" }, "Q"),
      ctx.question
    ));

    const grid = el("div", { class: "compare-grid" });
    ctx.answer.networks.forEach((n, idx) => {
      const cssKey = ["visa", "mc", "amex"][idx];
      const cell = el("div", { class: `compare-cell ${cssKey}` });
      cell.appendChild(el("div", { class: `net-label ${cssKey}` },
        el("span", { class: "dot" }), n.network
      ));
      cell.appendChild(el("div", { class: "code" }, n.reason_code));
      cell.appendChild(el("div", { class: "t" }, n.reason_title));
      cell.appendChild(el("div", { class: "meta" },
        el("span", {}, `${n.time_limit_days || "—"} days`),
        el("span", {}, n.requires_pre_arbitration ? "pre-arb" : "no pre-arb")
      ));
      grid.appendChild(cell);
    });
    body.appendChild(grid);

    if (ctx.answer.note) {
      body.appendChild(el("div", { class: "source" },
        el("span", { class: "path" }, ctx.answer.note),
        el("span", {}, ctx.id)
      ));
    }

    card.appendChild(body);
    return card;
  }

  // ---- Result orchestration ------------------------------------------
  const results = document.getElementById("results");

  function empty(title, msg) {
    return el("div", { class: "empty" },
      el("span", { class: "em" }, title),
      msg || ""
    );
  }

  function renderMeta(text) {
    return el("div", { class: "result-meta" },
      el("span", {}, ""),
      el("span", { class: "count" }, text)
    );
  }

  function clearResults() { results.replaceChildren(); }

  function renderCards(hits) {
    clearResults();
    if (!hits.length) {
      results.appendChild(empty("No matches", "Try different keywords, remove the network filter, or use Direct lookup."));
      return;
    }
    results.appendChild(renderMeta(`${hits.length} match${hits.length > 1 ? "es" : ""}`));
    hits.forEach(h => {
      const card = h.ctx.network === "comparison"
        ? renderComparisonCard(h.ctx)
        : renderSingleAnswerCard(h.ctx, h.score);
      results.appendChild(card);
    });
  }

  // ---- Actions --------------------------------------------------------
  document.getElementById("searchBtn").addEventListener("click", () => {
    const q = document.getElementById("ask").value.trim();
    if (!q) {
      clearResults();
      results.appendChild(empty("Ask a question", "Describe the dispute in a sentence — the app matches it against 100 pre-built contexts."));
      return;
    }
    renderCards(retrieve(q, activeNet, 5));
  });
  document.getElementById("ask").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      document.getElementById("searchBtn").click();
    }
  });

  document.getElementById("clearBtn").addEventListener("click", () => {
    document.getElementById("ask").value = "";
    clearResults();
    renderIntro();
  });

  document.getElementById("lookupBtn").addEventListener("click", () => {
    const netKey = netSel.value;
    const code = codeSel.value;
    const rc = RULES.networks[netKey].reason_codes[code];
    const evidence = RULES.evidence_matrix[rc.category] || [];
    const fake = {
      id: `lookup-${netKey}-${code}`,
      category: rc.category,
      network: netKey,
      question: `Direct lookup: ${NET_NAME[netKey]} reason code ${code}.`,
      answer: {
        network: RULES.networks[netKey].name,
        framework: RULES.networks[netKey].framework,
        reason_code: code,
        reason_title: rc.title,
        category: rc.category,
        time_limit_days: rc.time_limit_days,
        requires_pre_arbitration: !!rc.requires_pre_arbitration,
        evidence_checklist: evidence,
        source_ref: RULES.networks[netKey].source,
      },
    };
    clearResults();
    results.appendChild(renderMeta(`${NET_NAME[netKey]} · ${code}`));
    results.appendChild(renderSingleAnswerCard(fake, null));
  });

  document.getElementById("compareBtn").addEventListener("click", () => {
    const cat = catSel.value;
    const ctx = CONTEXTS.find(c => c.category === cat && c.network === "comparison");
    clearResults();
    if (!ctx) {
      results.appendChild(empty("No comparison", "That category has no cross-network view."));
      return;
    }
    results.appendChild(renderMeta(`Comparison · ${cat.replace(/_/g, " ")}`));
    results.appendChild(renderComparisonCard(ctx));
  });

  // ---- First view -----------------------------------------------------
  function renderIntro() {
    clearResults();
    // Show two illustrative starter cards: a comparison and a single-network match
    const comp = CONTEXTS.find(c => c.category === "not_received" && c.network === "comparison");
    const single = CONTEXTS.find(c => c.category === "duplicate" && c.network === "visa");
    results.appendChild(renderMeta("Starter view — try Ask, Direct lookup, or Compare"));
    if (comp) results.appendChild(renderComparisonCard(comp));
    if (single) results.appendChild(renderSingleAnswerCard(single, null));
  }
  renderIntro();
})();
</script>
"""


def main() -> None:
    html = TEMPLATE.replace("__RULES_JSON__", RULES).replace("__CONTEXTS_JSON__", CONTEXTS)
    OUT.write_text(html)
    print(f"Wrote {OUT} ({len(html):,} chars)")


if __name__ == "__main__":
    main()
