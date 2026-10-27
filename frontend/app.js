const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
let currentId = null;

const SAMPLES = {
  fake: "SHOCKING!!! Doctors HATE this one weird trick that cures all diseases overnight. Big pharma is hiding the secret from you, share this with 10 people before they delete it!",
  real: "The central bank held interest rates steady on Wednesday, citing moderating inflation, according to a statement released by the governor. Unemployment fell to 4.8 percent in the third quarter, officials said.",
};

async function api(path, options = {}) {
  const res = await fetch("/api" + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let msg = res.statusText;
    try {
      const j = await res.json();
      msg = Array.isArray(j.detail) ? j.detail.map((d) => d.msg).join("; ") : j.detail || msg;
    } catch {}
    throw new Error(msg);
  }
  return res.status === 204 ? null : res.json();
}

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const cls = (v) => (v === "Likely Fake" ? "fake" : v === "Likely Real" ? "real" : "uncertain");

/* ---------- Tabs ---------- */
$$(".tab").forEach((b) =>
  b.addEventListener("click", () => {
    $$(".tab").forEach((x) => x.classList.toggle("active", x === b));
    $$(".panel").forEach((p) => p.classList.toggle("active", p.id === "tab-" + b.dataset.tab));
    if (b.dataset.tab === "history") loadHistory();
    if (b.dataset.tab === "stats") loadStats();
  })
);

/* ---------- Analyze ---------- */
$$("input[name=mode]").forEach((r) =>
  r.addEventListener("change", () => {
    const url = r.value === "url" && r.checked;
    $("#inputText").classList.toggle("hidden", url);
    $("#inputUrl").classList.toggle("hidden", !url);
  })
);
$("#inputText").addEventListener("input", (e) => ($("#charCount").textContent = e.target.value.length + " characters"));
$("#sampleFake").onclick = () => setSample("fake");
$("#sampleReal").onclick = () => setSample("real");
function setSample(k) {
  document.querySelector("input[value=text]").click();
  $("#inputText").value = SAMPLES[k];
  $("#inputText").dispatchEvent(new Event("input"));
}

$("#analyzeBtn").onclick = async () => {
  const mode = document.querySelector("input[name=mode]:checked").value;
  const payload = mode === "url" ? { url: $("#inputUrl").value } : { text: $("#inputText").value };
  const err = $("#error");
  err.classList.add("hidden");
  const btn = $("#analyzeBtn");
  btn.disabled = true;
  btn.textContent = "Analyzing…";
  try {
    const r = await api("/analyze", { method: "POST", body: JSON.stringify(payload) });
    showResult(r);
  } catch (e) {
    err.textContent = e.message;
    err.classList.remove("hidden");
  } finally {
    btn.disabled = false;
    btn.textContent = "Analyze";
  }
};

function showResult(r) {
  currentId = r.id;
  $("#result").classList.remove("hidden");
  const c = cls(r.verdict);
  const color = c === "fake" ? "var(--fake)" : c === "real" ? "var(--real)" : "var(--warn)";
  const g = $("#gauge");
  g.style.setProperty("--p", r.credibility_score);
  g.style.setProperty("--c", color);
  $("#gaugeNum").textContent = r.credibility_score;
  const v = $("#verdict");
  v.textContent = r.verdict;
  v.className = "verdict " + c;
  $("#probLine").textContent = `Model confidence in fake: ${(r.model_fake_probability * 100).toFixed(1)}% · after linguistic checks: ${(r.fake_probability * 100).toFixed(1)}%`;
  $("#sourceLine").textContent = r.source_url ? "Source: " + r.source_url : "";
  const fp = (r.fake_probability * 100).toFixed(0), rp = (r.real_probability * 100).toFixed(0);
  $("#fakeBar").style.width = fp + "%";
  $("#realBar").style.width = rp + "%";
  $("#fakePct").textContent = fp + "%";
  $("#realPct").textContent = rp + "%";

  $("#signals").innerHTML = r.signals.length
    ? r.signals.map((s) => `<li class="${s.type}">${esc(s.name)}</li>`).join("")
    : '<li class="info">No strong linguistic red or green flags found; verdict is based on the model.</li>';
  const chips = (arr, k) => arr.map((t) => `<span class="chip ${k}">${esc(t.term)}</span>`).join("");
  $("#termsFake").innerHTML = r.top_terms.fake.length ? "<b class='muted'>→ fake:</b> " + chips(r.top_terms.fake, "fake") : "";
  $("#termsReal").innerHTML = r.top_terms.real.length ? "<b class='muted'>→ real:</b> " + chips(r.top_terms.real, "real") : "";
  $("#fbMsg").textContent = r.user_label ? `Thanks — you marked this as ${r.user_label}.` : "";
  $("#result").scrollIntoView({ behavior: "smooth", block: "start" });
}

$$("[data-fb]").forEach((b) =>
  b.addEventListener("click", async () => {
    if (!currentId) return;
    try {
      await api(`/feedback/${currentId}`, { method: "POST", body: JSON.stringify({ label: b.dataset.fb }) });
      $("#fbMsg").textContent = `Thanks — saved as "${b.dataset.fb}".`;
    } catch (e) {
      $("#fbMsg").textContent = e.message;
    }
  })
);

/* ---------- History ---------- */
$("#filterVerdict").onchange = loadHistory;
async function loadHistory() {
  const v = $("#filterVerdict").value;
  const items = await api("/history?limit=50" + (v ? "&verdict=" + encodeURIComponent(v) : ""));
  $("#historyEmpty").classList.toggle("hidden", items.length > 0);
  $("#historyList").innerHTML = items
    .map(
      (i) => `<div class="h-item" data-id="${i.id}">
        <span class="badge ${cls(i.verdict)}">${esc(i.verdict)} · ${i.credibility_score}</span>
        <div class="txt">${esc(i.excerpt)}<div class="meta">${new Date(i.created_at).toLocaleString()}${i.user_label ? " · you said: " + esc(i.user_label) : ""}</div></div>
        <button class="del" data-del="${i.id}" title="Delete">✕</button>
      </div>`
    )
    .join("");
}
$("#historyList").addEventListener("click", async (e) => {
  const del = e.target.closest("[data-del]");
  if (del) {
    e.stopPropagation();
    await api("/history/" + del.dataset.del, { method: "DELETE" });
    return loadHistory();
  }
  const item = e.target.closest(".h-item");
  if (item) {
    const r = await api("/analysis/" + item.dataset.id);
    document.querySelector('[data-tab="analyze"]').click();
    showResult(r);
  }
});

/* ---------- Stats ---------- */
async function loadStats() {
  const s = await api("/stats");
  $("#sTotal").textContent = s.total;
  $("#sFake").textContent = s.fake;
  $("#sReal").textContent = s.real;
  $("#sAvg").textContent = s.avg_credibility;
  const m = s.model || {};
  $("#modelInfo").textContent = m.n_samples
    ? `Trained on ${m.n_samples} samples (${m.data_source}). Test accuracy: ${(m.accuracy * 100).toFixed(1)}%, F1: ${(m.f1 * 100).toFixed(1)}%. Feedback labels collected: ${s.feedback_count}.`
    : "No model metrics yet.";
  drawChart(s.last_7_days);
}

$("#retrainBtn").onclick = async () => {
  $("#retrainMsg").textContent = "Retraining…";
  try {
    const r = await api("/retrain", { method: "POST" });
    $("#retrainMsg").textContent = `Done. Accuracy ${(r.metrics.accuracy * 100).toFixed(1)}% on ${r.metrics.n_samples} samples.`;
    loadStats();
  } catch (e) {
    $("#retrainMsg").textContent = e.message;
  }
};

/* Tiny stacked bar chart on <canvas> (no libraries) */
function drawChart(days) {
  const cv = $("#chart");
  const dpr = window.devicePixelRatio || 1;
  const W = cv.clientWidth, H = 180;
  cv.width = W * dpr; cv.height = H * dpr;
  const ctx = cv.getContext("2d");
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, W, H);
  const css = getComputedStyle(document.body);
  const colors = { fake: "#e03131", real: "#2f9e44", uncertain: "#f59f00" };
  const max = Math.max(1, ...days.map((d) => d.fake + d.real + d.uncertain));
  const bw = W / days.length, pad = 16, base = H - 24;
  ctx.font = "11px system-ui"; ctx.textAlign = "center"; ctx.fillStyle = css.getPropertyValue("--muted");
  days.forEach((d, i) => {
    let y = base;
    for (const k of ["real", "uncertain", "fake"]) {
      const h = (d[k] / max) * (base - 14);
      ctx.fillStyle = colors[k];
      ctx.fillRect(i * bw + pad, y - h, bw - pad * 2, h);
      y -= h;
    }
    ctx.fillStyle = css.getPropertyValue("--muted");
    ctx.fillText(d.date.slice(5), i * bw + bw / 2, H - 6);
    const tot = d.fake + d.real + d.uncertain;
    if (tot) ctx.fillText(tot, i * bw + bw / 2, y - 4);
  });
}