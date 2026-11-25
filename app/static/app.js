// Kokoro Reader front end: plain-text reader + guided video workflow (transcribe → translate → review → voice → export).
const $ = (id) => document.getElementById(id);
const S = {
  ui: "en", voices: {}, mode: null,            // mode: null | "plain" | "project"
  // plain text
  raw: null, fileName: "", kind: "plain",
  // video / project
  video: null, pid: null, P: null, rev: null, step: 1, chunk: 0, filter: "all", editing: null, pendingRender: false,
  force4: false, playEnd: null, pollT: null,
  // voice job
  jobId: null, timer: null, files: {}, media: "", done: false, items: [], cur: -1, curW: null, jobLang: "", jobSrc: "tr",
  glossary: [], glossDirty: [],
};
const TONES = { neutral: ["1.0", "0.35"], calm: ["0.9", "0.7"], energetic: ["1.1", "0.15"], serious: ["0.95", "0.35"] };
const DEFAULT_VOICE = { "en-us": "af_bella", "en-gb": "bf_emma", zh: "zm_009" };

// ---------------------------------------------------------------- helpers
function t(key, vars = {}) {
  let s = (I18N[S.ui] && I18N[S.ui][key]) ?? I18N.en[key] ?? key;
  for (const [k, v] of Object.entries(vars)) s = s.split(`{${k}}`).join(v);
  return s;
}
function store(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
function recall(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
function fmt(sec) {
  if (!isFinite(sec)) return "0:00";
  const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = Math.floor(sec % 60);
  return h ? `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}` : `${m}:${String(s).padStart(2, "0")}`;
}
function fmtCue(sec) { return `${fmt(sec)}.${Math.floor((sec % 1) * 10)}`; }
function esc(s) { return String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
function say(key, vars, isErr = false) {
  const m = $("msg");
  m.textContent = key ? t(key, vars) : "";
  m.className = "msg" + (isErr ? " err" : "");
}
async function api(path, body, method) {
  const r = await fetch(path, body === undefined && !method ? {} : {
    method: method || "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body ?? {}),
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw Object.assign(new Error(j.error || r.status), { code: j.error, status: r.status });
  return j;
}
const isZh = (s) => /[一-鿿]/.test(s || "");
const stem = (n) => (n || "output").replace(/\.[^.]+$/, "");

// ---------------------------------------------------------------- interface language
function applyUI(lang) {
  S.ui = lang;
  store("kr-ui", lang);
  document.documentElement.lang = lang === "zh" ? "zh-Hant-TW" : "en";
  document.querySelectorAll("[data-t]").forEach((e) => (e.textContent = t(e.dataset.t)));
  document.querySelectorAll("[data-tp]").forEach((e) => (e.placeholder = t(e.dataset.tp)));
  document.querySelectorAll("[data-tip]").forEach((e) => (e.textContent = TIPS[lang][e.dataset.tip] || ""));
  document.querySelectorAll("[data-ui]").forEach((b) => b.classList.toggle("on", b.dataset.ui === lang));
  fillVoices(true);
  renderAll();
}

// ---------------------------------------------------------------- voices
function voiceLabel(v) { return `${v} (${v[1] === "f" ? "F" : "M"})`; }
function fillVoices(keep) {
  const lang = $("lang").value, list = S.voices[lang] || [];
  const prevV = keep ? $("voice").value : null, prevB = keep ? $("blend").value : null;
  $("voice").innerHTML = list.map((v) => `<option value="${v}">${voiceLabel(v)}</option>`).join("");
  const pick = [prevV, recall("kr-voice-" + lang), DEFAULT_VOICE[lang]].find((v) => v && list.includes(v));
  if (pick) $("voice").value = pick;
  $("blend").innerHTML = `<option value="">${t("none")}</option>` + list.map((v) => `<option value="${v}">${voiceLabel(v)}</option>`).join("");
  if (prevB && list.includes(prevB)) $("blend").value = prevB;
}
function setLang(lang) {
  if ($("lang").value !== lang) { $("lang").value = lang; fillVoices(false); }
}
function applyTone() {
  const p = TONES[$("tone").value];
  if (p) { $("speed").value = p[0]; $("pause").value = p[1]; }
}

// ---------------------------------------------------------------- mode + layout
function setMode(mode) {
  S.mode = mode;
  document.querySelectorAll(".proj-only").forEach((e) => (e.hidden = mode !== "project"));
  document.querySelectorAll(".plain-only").forEach((e) => (e.hidden = mode !== "plain"));
  $("welcome").hidden = !!mode;
  $("work").hidden = !mode;
  $("src").hidden = !mode;
  if (mode === "plain") {
    document.querySelectorAll(".step").forEach((s) => (s.hidden = s.dataset.p !== "4"));
    $("lang").disabled = false;
    showTab("play");
  }
}
function showTab(name) {
  document.querySelectorAll("#tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === name));
  $("t-rev").hidden = S.mode !== "project" || name !== "rev";
  $("t-play").hidden = S.mode === "project" && name !== "play";
  if (name !== "rev") $("rv-video").pause();
  if (name !== "play") $("media").pause();
}

// ---------------------------------------------------------------- steps
function unlocked(n) {
  const P = S.P;
  if (S.mode !== "project") return false;
  if (n === 1) return !P || !P.from_srt;
  if (!P) return false;
  const anyReady = P.chunks.some((c) => c.status === "ready");
  if (n === 2) return P.from_srt || P.chunks.some((c) => ["transcribed", "translating", "ready"].includes(c.status));
  if (n === 3) return anyReady;
  if (n === 4) return anyReady && (S.force4 || P.chunks.some((c) => c.reviewed));
  if (n === 5) return S.done && !!S.jobId;
  return false;
}
function go(n, force = false) {
  if (n === 4 && !unlocked(4) && unlocked(3)) {
    if (!confirm(t("confirm_unreviewed_step"))) return;
    S.force4 = true;
  }
  if (!force && !unlocked(n)) return;
  S.step = n;
  document.querySelectorAll(".step").forEach((s) => (s.hidden = +s.dataset.p !== n));
  if (n === 3) showTab("rev");
  if (n === 4) prepareVoiceStep();
  if (n === 5) renderExport();
  renderSteps();
  $("steps").scrollIntoView({ behavior: "smooth", block: "nearest" });
}
function renderSteps() {
  document.querySelectorAll("#steps button").forEach((b) => {
    const s = +b.dataset.s;
    b.className = s === S.step ? "now" : unlocked(s) ? (s < S.step || stepDone(s) ? "done" : "") : "lock";
    b.title = unlocked(s) ? "" : t("locked_" + s);
  });
  document.querySelectorAll("[data-go]").forEach((b) => (b.disabled = +b.dataset.go !== 4 && !unlocked(+b.dataset.go)));
  for (let k = 1; k <= 5; k++) {
    const g = document.querySelector(`.step[data-p="${k}"] .guide`);
    if (g) g.textContent = t("g" + k + (k === 2 && S.P?.from_srt ? "_srt" : ""));
  }
}
function stepDone(s) {
  const P = S.P;
  if (!P) return false;
  if (s === 1) return P.from_srt || P.done || P.chunks.length && P.chunks.every((c) => c.status === "ready");
  if (s === 2) return P.chunks.length && P.chunks.every((c) => c.status === "ready");
  if (s === 3) return P.chunks.length && P.chunks.every((c) => c.reviewed);
  if (s === 4) return S.done;
  return false;
}

// ---------------------------------------------------------------- opening files
async function readText(file) {
  const buf = await file.arrayBuffer();
  try { return new TextDecoder("utf-8", { fatal: true }).decode(buf).replace(/^﻿/, ""); }
  catch (e) { return new TextDecoder("big5").decode(buf); }
}
async function openFile(file) {
  const text = await readText(file);
  resetVoice();
  if (/\.srt$/i.test(file.name)) {
    stopPolling();
    S.fileName = file.name;
    const keepVideo = S.mode === "project" && S.P && !S.P.from_srt ? null : S.video;
    try {
      const r = await api("/api/project", { srt: text, name: file.name, target: $("target").value, video_id: keepVideo?.id });
      S.video = keepVideo;
      await loadProject(r.id);
      setMode("project");
      S.step = 2; S.chunk = 0; S.force4 = false;
      go(2, true);
      say("srt_opened", { n: file.name });
    } catch (e) { say(e.code === "no_cues" ? "err_parse" : "err_generic", { m: e.message }, true); }
    return;
  }
  // plain text
  stopPolling();
  S.pid = null; S.P = null; S.video = null;
  S.raw = text; S.fileName = file.name; S.kind = "plain";
  setMode("plain");
  const cjk = (text.match(/[一-鿿]/g) || []).length / Math.max(text.replace(/\s/g, "").length, 1);
  if (cjk > 0.3) setLang("zh"); else if (cjk < 0.05 && $("lang").value === "zh") setLang("en-us");
  await parsePlain();
}
async function parsePlain() {
  if (S.raw == null) return;
  try {
    const r = await api("/api/parse", { text: S.raw, kind: "plain", lang: $("lang").value, clean: $("clean").value === "1" });
    S.items = r.items;
    say("");
  } catch (e) { say("err_parse", {}, true); S.items = []; }
  renderAll();
}
async function uploadVideo(file) {
  say("uploading", { n: file.name });
  const fd = new FormData();
  fd.append("file", file);
  const r = await fetch("/api/video", { method: "POST", body: fd });
  if (!r.ok) { say("err_video", {}, true); return null; }
  return r.json();
}
async function openVideo(file) {
  const v = await uploadVideo(file);
  if (!v) return;
  resetVoice();
  // An opened .srt without a video: attach this video to it instead of transcribing.
  if (S.mode === "project" && S.P && S.P.from_srt && !S.P.video) {
    await api(`/api/project/${S.pid}/video`, { video_id: v.id });
    S.video = v;
    await refresh(true);
    say("video_attached", { n: v.name });
    return;
  }
  stopPolling();
  S.video = v; S.pid = null; S.P = null; S.rev = null; S.force4 = false; S.chunk = 0;
  S.fileName = v.name;
  setMode("project");
  S.step = 1;
  go(1, true);
  say(v.has_audio ? "video_ready" : "video_no_audio", { n: v.name, d: fmt(v.duration) }, !v.has_audio);
  renderAll();
}

// ---------------------------------------------------------------- project polling
async function loadProject(pid) {
  S.pid = pid; S.rev = null;
  store("kr-pid", pid);
  await refresh(true);
  startPolling();
}
function startPolling() {
  stopPolling();
  S.pollT = setInterval(() => refresh(false), 1000);
}
function stopPolling() { clearInterval(S.pollT); S.pollT = null; }
async function refresh(full) {
  if (!S.pid) return;
  let P;
  try { P = await api(`/api/project/${S.pid}` + (full || !S.P ? "" : `?rev=${S.rev}`)); } catch (e) { return; }
  const changed = !("lines" in P) ? false : true;
  if (!changed) P.lines = S.P.lines;
  const firstReady = S.P && !S.P.chunks.some((c) => c.status === "ready") && P.chunks.some((c) => c.status === "ready");
  S.P = P; S.rev = P.rev;
  if (P.target && $("target").value !== P.target && document.activeElement !== $("target")) $("target").value = P.target;
  if (!P.running && P.status !== "queued") stopPolling();
  if (firstReady && S.step === 1) say("first_ready");
  if (P.status === "error") say("err_generic", { m: P.message }, true);
  renderProgress();
  renderChunks();
  renderSteps();
  renderMeta();
  if (changed) {
    if (S.editing != null) S.pendingRender = true;
    else renderTable();
  }
}

// ---------------------------------------------------------------- step 1 + 2
async function startTranscribe() {
  if (!S.video) return say("err_novideo", {}, true);
  try {
    const r = await api("/api/project", { video_id: S.video.id, spoken: $("spoken").value, target: $("target").value,
      chunk_min: +$("chunk").value, accuracy: $("acc").value });
    await loadProject(r.id);
    say("transcribing_started", { d: fmt(S.video.duration / 2) });
  } catch (e) { say("err_generic", { m: e.message }, true); }
}
function srcLang() { return S.P?.lang === "zh" ? "zh" : "en"; }
function tgtLang() {
  const tg = S.P?.target || $("target").value;
  if (tg === "auto") return srcLang() === "zh" ? "en" : "zh";
  return tg === srcLang() ? "off" : tg;
}
function langName(l) { return l === "zh" ? t("l_zh") : t("l_en"); }
function renderProgress() {
  const P = S.P;
  const run = P && P.running;
  $("p1-start").hidden = !!P;
  $("p1-stop").hidden = !run;
  $("p1-resume").hidden = !(P && !run && !P.done && !P.from_srt && P.status !== "queued");
  document.querySelector('.step[data-p="1"] [data-go="2"]').hidden = !P;
  ["spoken", "chunk", "acc"].forEach((id) => ($(id).disabled = !!P));
  $("target").disabled = !!run;
  $("p2-again").disabled = !!run || !P;
  if (!P) {
    $("p1-bar").style.width = "0";
    $("p1-text").textContent = S.video ? t("p1_ready", { d: fmt(S.video.duration), e: fmt(S.video.duration / 2) }) : "";
    $("p2-text").textContent = "";
    return;
  }
  const ch = P.chunks;
  const total = P.duration || 1;
  const doneSec = ch.reduce((a, c) => a + (["transcribed", "translating", "ready"].includes(c.status) ? c.end - c.start
    : c.status === "transcribing" ? (c.progress || 0) * (c.end - c.start) : 0), 0);
  const pct = P.from_srt ? 100 : Math.round((doneSec / total) * 100);
  $("p1-bar").style.width = pct + "%";
  const cur = ch.find((c) => c.status === "transcribing");
  const speed = P.t_work > 0 ? (P.t_audio / P.t_work).toFixed(1) + "×" : "";
  let msg;
  if (P.status === "preparing") msg = t("p1_preparing");
  else if (cur) msg = t("p1_running", { i: cur.i + 1, n: ch.length, p: pct, lang: P.lang ? langName(P.lang) : "…", s: speed });
  else if (P.status === "stopped" || (!run && !P.done && !P.from_srt && P.status !== "error")) msg = t("p1_stopped", { p: pct });
  else if (P.status === "error") msg = t("err_generic", { m: P.message });
  else if (P.done || P.from_srt) msg = t("p1_done", { n: P.lines.length, lang: langName(srcLang()), s: speed });
  else msg = t("p1_wait");
  $("p1-text").textContent = msg;
  const tg = tgtLang();
  const lines = P.lines, trd = lines.filter((l) => l.tr).length;
  $("p2-bar").style.width = tg === "off" ? "100%" : `${lines.length ? Math.round((trd / lines.length) * 100) : 0}%`;
  $("p2-text").textContent = tg === "off" ? t("p2_off", { lang: langName(srcLang()) })
    : t("p2_status", { a: trd, n: lines.length, from: langName(srcLang()), to: langName(tg), s: P.t_translate.toFixed(1) });
  // step 3 meters
  const rev = lines.filter((l) => l.reviewed).length, fl = lines.filter((l) => l.flags.length).length,
    ed = lines.filter((l) => l.edited).length, cr = ch.filter((c) => c.reviewed).length;
  $("m-rev").textContent = `${rev} / ${lines.length}`;
  $("m-flag").textContent = fl;
  $("m-edit").textContent = ed;
  $("m-chunks").textContent = `${cr} / ${ch.length}`;
  const rp = lines.length ? Math.round((rev / lines.length) * 100) : 0;
  $("p3-bar").style.width = rp + "%";
  $("p3-text").textContent = t("p3_status", { p: rp });
  $("doc-meta").textContent = t("meta_proj", { n: lines.length, c: ch.length, d: fmt(P.duration) });
}
async function changeTarget() {
  if (!S.P) return;
  if (S.P.lines.some((l) => l.edited) && !confirm(t("confirm_target"))) { $("target").value = S.P.target; return; }
  say("translating_all");
  try { await api(`/api/project/${S.pid}/target`, { target: $("target").value }); say("translated_all"); }
  catch (e) { say(e.code === "busy" ? "err_wait_tr" : "err_generic", { m: e.message }, true); }
  await refresh(true);
}

// ---------------------------------------------------------------- review table
function chunkLines() { return S.P ? S.P.lines.filter((l) => l.chunk === S.chunk) : []; }
function renderChunks() {
  const P = S.P, box = $("chunks");
  if (!P || P.chunks.length <= 1) { box.innerHTML = ""; box.hidden = true; return; }
  box.hidden = false;
  box.innerHTML = P.chunks.map((c) => {
    const ls = P.lines.filter((l) => l.chunk === c.i);
    const fl = ls.filter((l) => l.flags.length).length;
    const ready = c.status === "ready";
    let sub = `${fmt(c.start)}–${fmt(c.end)}`;
    if (c.status === "transcribing") sub = `<span class="run">●</span> ${t("ch_running", { p: Math.round((c.progress || 0) * 100) })}`;
    else if (c.status === "translating" || c.status === "transcribed") sub = `<span class="run">●</span> ${t("ch_translating")}`;
    else if (c.status === "queued") sub = t("ch_queued");
    else sub += ` · ${t("ch_lines", { n: ls.length })}` + (fl ? ` · ⚠ ${fl}` : "");
    return `<button type="button" class="chunk ${c.i === S.chunk ? "on" : ""}" data-c="${c.i}" ${ready ? "" : "disabled"}>` +
      `${c.reviewed ? '<span class="okc">✓</span> ' : ""}${t("ch_name", { n: c.i + 1 })}<small>${sub}</small></button>`;
  }).join("");
  if (!P.chunks.some((c) => c.i === S.chunk && c.status === "ready")) {
    const first = P.chunks.find((c) => c.status === "ready");
    if (first && first.i !== S.chunk) { S.chunk = first.i; renderTable(); }
  }
}
function glossMarks(text, side) {
  // underline glossary terms: English terms in the English column, targets in the other
  let h = esc(text);
  const terms = [];
  for (const g of S.glossary) {
    if (side === "en") terms.push(g.src);
    else terms.push(g.dst || g.src);
  }
  const uniq = [...new Set(terms.filter((x) => x && x.length > 1))].sort((a, b) => b.length - a.length);
  if (!uniq.length) return h;
  const re = new RegExp(uniq.map((x) => esc(x).replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|"), "gi");
  return h.replace(re, (m) => `<mark class="g">${m}</mark>`);
}
function lineFit(l) {
  if (!S.done || !S.items.length) return `<span class="chip none">—</span>`;
  const it = S.items.find((x) => x.lid === l.id);
  if (!it) return `<span class="chip none">—</span>`;
  if (it.skip) return `<span class="chip skip">${t("st_skip")}</span>`;
  const map = { ok: ["ok", t("st_ok")], sped: ["sped", `${it.factor}×`], gap: ["gap", t("st_gap")], late: ["late", t("st_late", { s: it.delay })] };
  const [c, label] = map[it.status] || ["none", "—"];
  return `<span class="chip ${c}">${label}</span>`;
}
function lateSet() {
  return new Set(S.done ? S.items.filter((x) => x.status === "late").map((x) => x.lid) : []);
}
function filterCounts(ls, late = lateSet()) {
  return { all: ls.length, flag: ls.filter((l) => l.flags.length || late.has(l.id)).length, edited: ls.filter((l) => l.edited).length, notrev: ls.filter((l) => !l.reviewed).length };
}
function renderTable() {
  S.pendingRender = false;
  const box = $("rv");
  if (!S.P) { box.innerHTML = ""; return; }
  const tg = tgtLang(), sl = srcLang();
  const ls = chunkLines();
  const late = lateSet();
  const counts = filterCounts(ls, late);
  $("filter").innerHTML = ["all", "flag", "edited", "notrev"].map((f) =>
    `<button type="button" data-f="${f}" class="${S.filter === f ? "on" : ""}">${t("f_" + f)} ${counts[f]}</button>`).join("");
  const shown = ls.filter((l) => S.filter === "all" || (S.filter === "flag" && (l.flags.length || late.has(l.id))) ||
    (S.filter === "edited" && l.edited) || (S.filter === "notrev" && !l.reviewed));
  const two = tg !== "off";
  let h = `<colgroup><col style="width:44px"><col style="width:72px"><col>${two ? "<col>" : ""}<col style="width:66px"><col style="width:40px"><col style="width:${two ? 70 : 50}px"></colgroup>` +
    `<thead><tr><th>#</th><th>${t("th_time")}</th><th>${t("th_orig", { l: langName(sl) })}</th>` +
    (two ? `<th>${t("th_tr", { l: langName(tg) })}</th>` : "") +
    `<th>${t("th_fit")}</th><th title="${esc(t("th_rev_tip"))}">✓</th><th></th></tr></thead><tbody>`;
  if (!shown.length) h += `<tr class="empty-row"><td colspan="7">${t(ls.length ? "rv_none" : "rv_empty")}</td></tr>`;
  for (const l of shown) {
    const n = S.P.lines.indexOf(l) + 1;
    const fl = l.flags;
    const cls = [fl.length || late.has(l.id) ? "flag" : "", l.skip ? "skip" : ""].join(" ");
    const unsure = fl.includes("unsure") ? ` <span class="wf" title="${esc(t("w_unsure"))}">⚠ ${t("w_unsure_s")}</span>` : "";
    const cont = fl.includes("cont") ? ` <button type="button" class="wf join" data-id="${l.id}" title="${esc(t("w_cont"))}">⚠ ⤓ ${t("w_join")}</button>` : "";
    const long = fl.includes("long") ? ` <span class="wf" title="${esc(t("w_long"))}">⚠ ${t("w_long_s")}</span>` : "";
    const edited = l.edited ? ` <span class="tag" title="${esc(t("was", { t: l.tr_auto }))}">${t("edited")}</span>` : "";
    h += `<tr data-id="${l.id}" class="${cls}"><td>${n}</td><td class="t" data-play="${l.id}">${fmtCue(l.start)}</td>` +
      `<td class="o" data-ed="src">${glossMarks(l.src, sl)}${unsure}${two ? "" : cont + long}</td>` +
      (two ? `<td class="tr" data-ed="tr">${l.tr ? glossMarks(l.tr, tg) : `<span class="muted">${t("tr_pending")}</span>`}${edited}${cont}${long}</td>` : "") +
      `<td>${lineFit(l)}</td><td><input type="checkbox" class="rvck" ${l.reviewed ? "checked" : ""} aria-label="${esc(t("th_rev_tip"))}"></td>` +
      `<td class="acts"><button type="button" data-play="${l.id}" title="${esc(t("a_play"))}">${icon("play")}</button>` +
      `<button type="button" data-edit="${two ? "tr" : "src"}" title="${esc(t("edit"))}">${icon("edit")}</button></td></tr>`;
  }
  box.innerHTML = h + "</tbody>";
  const c = S.P.chunks.find((x) => x.i === S.chunk);
  $("mark-chunk").disabled = !c || c.status !== "ready";
  $("mark-chunk").lastElementChild.textContent = c && c.reviewed ? t("chunk_is_reviewed") : t("mark_chunk");
  $("rt-chunk").disabled = !c || c.status !== "ready" || !two;
}
async function saveLine(id, change) {
  try { await api(`/api/project/${S.pid}/lines`, { changes: [{ id, ...change }] }); } catch (e) { say("err_generic", { m: e.message }, true); }
  await refresh(true);
}
function editCell(td) {
  const tr = td.closest("tr"), id = +tr.dataset.id, side = td.dataset.ed;
  const l = S.P.lines.find((x) => x.id === id);
  if (!l || td.querySelector("textarea")) return;
  if (S.editing != null) closeEditor(true);
  S.editing = id;
  td.innerHTML = `<textarea rows="2">${esc(side === "tr" ? l.tr : l.src)}</textarea><div class="edbar">` +
    `<button type="button" class="btn sm primary" data-save>${t("save")}</button><button type="button" class="btn sm" data-cancel>${t("cancel")}</button>` +
    (side === "tr" ? `<button type="button" class="btn sm" data-rt>${icon("redo")}${t("retranslate")}</button>` +
      (l.edited ? `<button type="button" class="btn sm" data-undo>${icon("undo")}${t("undo")}</button>` : "") : "") +
    `<span class="muted">${t("ed_keys")}</span></div>`;
  const ta = td.querySelector("textarea");
  ta.focus();
  ta.setSelectionRange(ta.value.length, ta.value.length);
  const commit = async () => {
    const v = ta.value.trim();
    S.editing = null;
    if (v && v !== (side === "tr" ? l.tr : l.src)) await saveLine(id, { [side]: v });
    else renderTable();
  };
  ta.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); commit(); }
    if (e.key === "Escape") { e.preventDefault(); closeEditor(false); }
  });
  td.querySelector("[data-save]").onclick = commit;
  td.querySelector("[data-cancel]").onclick = () => closeEditor(false);
  const rt = td.querySelector("[data-rt]");
  if (rt) rt.onclick = async () => { S.editing = null; say("retranslating"); await api(`/api/project/${S.pid}/retranslate`, { ids: [id] }); say(""); await refresh(true); };
  const un = td.querySelector("[data-undo]");
  if (un) un.onclick = async () => { S.editing = null; await saveLine(id, { tr: l.tr_auto }); };
}
function closeEditor() {
  S.editing = null;
  renderTable();
}
function playLine(id) {
  const l = S.P.lines.find((x) => x.id === id);
  const v = $("rv-video");
  if (!l || v.hidden) return say("no_video_to_play", {}, true);
  v.currentTime = l.start;
  S.playEnd = l.end;
  v.play();
}

// add-to-glossary popup ---------------------------------------------------
let popLine = null;
function openPop(x, y, text, side, lineId) {
  const pop = $("pop");
  popLine = lineId;
  const enSide = side === "src" ? srcLang() === "en" : tgtLang() === "en";
  $("pop-src").value = enSide ? text : "";
  $("pop-dst").value = enSide ? "" : text;
  pop.hidden = false;
  pop.style.left = Math.min(x, innerWidth - pop.offsetWidth - 12) + "px";
  pop.style.top = Math.min(y + 8, innerHeight - pop.offsetHeight - 12) + "px";
  (enSide ? $("pop-dst") : $("pop-src")).focus();
}
async function popAdd(all) {
  const src = $("pop-src").value.trim(), dst = $("pop-dst").value.trim();
  if (!src) { $("pop-src").focus(); return; }
  const n = popLine != null ? S.P.lines.findIndex((l) => l.id === popLine) + 1 : "";
  S.glossary = await api("/api/glossary", { items: [...S.glossary, { src, dst, where: n ? t("g_line", { n }) : "" }] });
  $("pop").hidden = true;
  updateGlossCount();
  say("retranslating");
  if (all) await api(`/api/project/${S.pid}/retranslate`, { terms: [src, dst].filter(Boolean) });
  else if (popLine != null) await api(`/api/project/${S.pid}/retranslate`, { ids: [popLine] });
  say("gloss_added", { s: src });
  await refresh(true);
}

// ---------------------------------------------------------------- glossary dialog
async function loadGlossary() {
  try { S.glossary = await api("/api/glossary"); } catch (e) { S.glossary = []; }
  updateGlossCount();
}
function updateGlossCount() {
  document.querySelectorAll(".gcount").forEach((e) => (e.textContent = t("gloss_edit", { n: S.glossary.length })));
}
function usedCount(g) {
  if (!S.P) return "–";
  const a = g.src.toLowerCase(), b = (g.dst || "").toLowerCase();
  return S.P.lines.filter((l) => l.src.toLowerCase().includes(a) || (b && (l.src + l.tr).toLowerCase().includes(b))).length;
}
function renderGloss() {
  const q = $("gloss-find").value.trim().toLowerCase();
  $("gloss-title").textContent = t("gloss_title", { n: S.glossary.length });
  const rows = S.glossary.map((g, i) => ({ g, i })).filter(({ g }) => !q || (g.src + " " + g.dst).toLowerCase().includes(q));
  $("gloss-rows").innerHTML = rows.map(({ g, i }) =>
    `<tr data-i="${i}" class="${S.glossDirty.includes(g.src) ? "new" : ""}"><td><input value="${esc(g.src)}" data-k="src"></td>` +
    `<td><input value="${esc(g.dst)}" data-k="dst" placeholder="${esc(t("keep_as_is"))}"></td>` +
    `<td class="muted">${esc(g.added === "starter" ? t("g_starter") : g.added)}${g.where ? " · " + esc(g.where) : ""}</td>` +
    `<td>${usedCount(g)}</td><td class="acts"><button type="button" data-del="${i}" title="${esc(t("delete"))}">${icon("x")}</button></td></tr>`).join("") +
    `<tr class="add"><td><input id="g-new-src" placeholder="${esc(t("g_new"))}"></td><td><input id="g-new-dst" placeholder="${esc(t("keep_as_is"))}"></td>` +
    `<td colspan="3"><button type="button" class="btn sm" id="g-add">+ ${t("add")}</button></td></tr>`;
  const n = S.glossDirty.length;
  $("gloss-apply").textContent = t("gloss_apply", { n });
  $("gloss-apply").disabled = !n || !S.P;
}
async function saveGloss() {
  S.glossary = await api("/api/glossary", { items: S.glossary });
  updateGlossCount();
}
function openGloss() {
  S.glossDirty = [];
  renderGloss();
  $("gloss").showModal();
}

// ---------------------------------------------------------------- voice (step 4)
function prepareVoiceStep() {
  if (S.mode !== "project" || !S.P) return;
  const vs = $("vsrc").value;
  const l = vs === "src" ? srcLang() : (tgtLang() === "off" ? srcLang() : tgtLang());
  const opts = [...$("lang").options];
  opts.forEach((o) => (o.disabled = l === "zh" ? o.value !== "zh" : o.value === "zh"));
  if (l === "zh") setLang("zh");
  else if ($("lang").value === "zh") setLang("en-us");
  $("vsrc").disabled = tgtLang() === "off";
  if (tgtLang() === "off") $("vsrc").value = "src";
  const running = S.P.running;
  $("gen").disabled = !!running;
  if (running) say("err_wait_tr");
}
function resetVoice() {
  S.done = false; S.files = {}; S.media = ""; S.jobId = null;
  const m = $("media"); m.pause(); m.removeAttribute("src"); m.load(); m.hidden = true;
  $("downloads").innerHTML = "";
  ["m-load", "m-gen", "m-aud", "m-rt", "m-cps", "m-fit"].forEach((id) => ($(id).textContent = "–"));
  $("bar").style.width = "0"; $("prog-text").textContent = "";
}
async function generate() {
  let body;
  const base = { lang: $("lang").value, voice: $("voice").value, blend: $("blend").value, amount: +$("amount").value,
    speed: +$("speed").value, pause: +$("pause").value };
  if (S.mode === "plain") {
    if (!S.items.length) return say("err_nofile", {}, true);
    body = { ...base, mode: "plain", output: $("out-plain").value,
      items: S.items.map((it) => ({ text: it.text, display: it.display, para: it.para, skip: false, original: it.original, changed: it.changed })) };
  } else if (S.mode === "project" && S.P) {
    if (S.P.running) return say("err_wait_tr", {}, true);
    const vs = $("vsrc").value;
    const lines = S.P.lines;
    const notRev = lines.filter((l) => !l.reviewed && !l.skip).length;
    if (notRev && !confirm(t("confirm_unreviewed", { n: notRev }))) return;
    if ($("orig").value !== "mute" && S.P.video && !confirm(t("confirm_two_voices"))) return;
    body = { ...base, mode: "srt", fit: $("fit").value, max_speed: +$("max").value, orig: $("orig").value,
      output: "all", video_id: S.P.video ? S.P.video.id : null, clean_items: true,
      items: lines.map((l) => { const txt = vs === "tr" && l.tr ? l.tr : l.src;
        return { lid: l.id, text: txt, display: txt, start: l.start, end: l.end, skip: !!l.skip, original: txt, changed: false }; }) };
    S.jobSrc = vs;
  } else return say("err_nofile", {}, true);
  resetVoice();
  S.jobLang = base.lang;
  try {
    S.jobId = (await api("/api/generate", body)).id;
  } catch (e) { return say(e.code === "busy" ? "err_busy" : "err_generic", { m: e.message }, true); }
  $("gen").disabled = $("gen-top").disabled = true; $("cancel").hidden = false;
  say("");
  clearInterval(S.timer);
  S.timer = setInterval(poll, 500);
}
async function poll() {
  let j;
  try { j = await api(`/api/job/${S.jobId}`); } catch (e) { return; }
  meters(j);
  if (["done", "error", "cancelled"].includes(j.status)) {
    clearInterval(S.timer);
    $("gen").disabled = $("gen-top").disabled = false; $("cancel").hidden = true;
    if (j.status === "error") return say("err_generic", { m: j.message }, true);
    if (j.status === "cancelled") return say("st_cancelled");
    S.items = j.items; S.files = j.files; S.media = j.media; S.done = true;
    meters(j, true);
    setupMedia();
    renderAll();
    if (S.mode === "project") {
      store("kr-job-" + S.pid, JSON.stringify({ id: S.jobId, lang: S.jobLang, orig: $("orig").value }));
      say("voice_done"); showTab("play"); renderSteps();
    }
    else say("st_done");
  }
}
function meters(j, final = false) {
  const n = (x, d = 1) => (x == null ? "–" : (+x).toFixed(d));
  $("m-load").textContent = `${n(j.load_time)} s`;
  $("m-gen").textContent = j.gen_time >= 60 ? fmt(j.gen_time) : `${n(j.gen_time)} s`;
  $("m-aud").textContent = j.audio_time >= 60 ? fmt(j.audio_time) : `${n(j.audio_time)} s`;
  $("m-rt").textContent = j.gen_time > 0 ? `${n(j.audio_time / j.gen_time)}x` : "–";
  $("m-cps").textContent = j.gen_time > 0 ? n(j.chars / j.gen_time, 0) : "–";
  if (final && S.mode === "project") {
    const spoken = j.items.filter((x) => !x.skip);
    $("m-fit").textContent = `${spoken.filter((x) => x.status && x.status !== "late").length} / ${spoken.length}`;
  }
  const pct = j.n ? Math.round((j.i / j.n) * 100) : 0;
  $("bar").style.width = `${j.status === "done" ? 100 : pct}%`;
  const label = { queued: "st_loading", loading: "st_loading", running: "st_running", exporting: "st_exporting", done: "st_done", cancelled: "st_cancelled" }[j.status];
  let txt = label ? t(label, { i: j.i, n: j.n }) + (j.status === "running" ? ` · ${pct}%` : "") : "";
  if (final && S.mode === "project") {
    const sp = j.items.filter((x) => x.status === "sped").length, late = j.items.filter((x) => x.status === "late").length;
    txt = t("voice_summary", { s: sp, l: late, o: t("orig_" + $("orig").value) });
  }
  $("prog-text").textContent = txt;
}

// ---------------------------------------------------------------- export (step 5)
function outName(kind) {
  const base = stem(S.P?.video?.name || S.P?.name || S.fileName);
  const vtag = S.jobLang === "zh" ? "zh-TW" : "en";
  const stag = srcLang() === "zh" ? "zh-TW" : "en";
  const ttag = tgtLang() === "zh" ? "zh-TW" : tgtLang() === "en" ? "en" : stag;
  return { mp4: `${base}.${vtag}.mp4`, wav: `${base}.${vtag}.wav`, vsrt: `${base}.${vtag}.srt`,
    src: `${base}.${stag}.srt`, bi: `${base}.${stag}+${ttag}.srt` }[kind];
}
function exportRows() {
  const rows = [];
  const f = S.files, j = S.jobId;
  const fileUrl = (name, n) => `/files/${j}/${encodeURIComponent(name)}?dl=1&n=${encodeURIComponent(n)}`;
  if (f.mp4) rows.push({ k: "mp4", on: true, url: fileUrl(f.mp4, outName("mp4")), d: t("x_mp4_d", { o: t("orig_" + $("orig").value) }) });
  if (f.wav) rows.push({ k: "wav", on: true, url: fileUrl(f.wav, outName("wav")), d: t("x_wav_d") });
  if (f.srt) rows.push({ k: "vsrt", on: true, url: fileUrl(f.srt, outName("vsrt")), d: t("x_vsrt_d") });
  const pu = (w, n) => `/api/project/${S.pid}/srt/${w}?n=${encodeURIComponent(n)}`;
  rows.push({ k: "src", on: false, url: pu("src", outName("src")), d: t("x_src_d") });
  if (tgtLang() !== "off") rows.push({ k: "bi", on: false, url: pu("bi", outName("bi")), d: t("x_bi_d") });
  return rows;
}
function renderExport() {
  if (!S.P || !S.done) { $("out-rows").innerHTML = ""; return; }
  const rows = exportRows();
  const lname = (k) => k === "vsrt" ? t("x_vsrt", { l: langName(S.jobLang === "zh" ? "zh" : "en") }) : k === "src" ? t("x_src", { l: langName(srcLang()) }) : t("x_" + k);
  $("out-rows").innerHTML = rows.map((r) =>
    `<tr><td><input type="checkbox" data-k="${r.k}" ${r.on ? "checked" : ""}></td><td><b>${lname(r.k)}</b> <span class="muted">${esc(r.d)}</span><div class="fn">${esc(outName(r.k))}</div></td>` +
    `<td><a class="btn sm" href="${r.url}">${icon("dl")}${t("save")}</a></td></tr>`).join("");
  updateSaveSel();
}
function updateSaveSel() {
  const n = document.querySelectorAll("#out-rows input:checked").length;
  $("save-sel-t").textContent = t("save_sel", { n });
  $("save-sel").disabled = !n;
}
async function saveSelected() {
  const rows = exportRows();
  for (const box of document.querySelectorAll("#out-rows input:checked")) {
    const r = rows.find((x) => x.k === box.dataset.k);
    if (!r) continue;
    const a = document.createElement("a");
    a.href = r.url; a.download = ""; document.body.appendChild(a); a.click(); a.remove();
    await new Promise((res) => setTimeout(res, 700));
  }
}

// ---------------------------------------------------------------- play & highlight
function renderPlay() {
  const box = $("text");
  if (!S.items.length) {
    box.innerHTML = `<p class="empty">${t(S.mode === "project" ? "play_empty" : "empty_hint")}</p>`;
    return;
  }
  let h = "", para = null;
  S.items.forEach((it, i) => {
    if (it.skip) return;
    const p = it.para ?? 0;
    if (para === null || p !== para) { if (para !== null) h += "</p>"; h += "<p>"; para = p; }
    const fixed = it.changed ? `<span class="fixed" title="${esc(t("cleaned_tip", { t: it.original }))}">${t("cleaned")}</span>` : "";
    const inner = S.done && it.words
      ? it.words.map((w, k) => `<span class="w" data-i="${i}" data-k="${k}">${esc(w.t)}</span>${w.w ? " " : ""}`).join("")
      : esc(it.display || it.text);
    h += `<span class="sent" data-i="${i}">${inner}${fixed}</span>${isZh(it.text) ? "" : " "}`;
  });
  box.innerHTML = h + "</p>";
  S.cur = -1; S.curW = null;
  $("downloads").innerHTML = S.mode === "plain" ? Object.entries(S.files).map(([k, name]) =>
    `<a class="btn" href="/files/${S.jobId}/${encodeURIComponent(name)}?dl=1&n=${encodeURIComponent(stem(S.fileName) + "." + name.split(".").pop())}">${icon("dl")}${t("save_audio")} (${k.toUpperCase()})</a>`).join("") : "";
}
function setupMedia() {
  const m = $("media");
  m.src = `/files/${S.jobId}/${encodeURIComponent(S.media)}`;
  m.hidden = !/\.mp4$/i.test(S.media);
  m.load();
}
function curIndex(ct) {
  for (let i = 0; i < S.items.length; i++) {
    const it = S.items[i];
    if (!it.skip && it.start != null && ct >= it.start && ct < it.end) return i;
  }
  return -1;
}
function tick() {
  const m = $("media");
  if (S.done && m.getAttribute("src")) {
    const ct = m.currentTime;
    $("seek").max = m.duration || 0;
    if (document.activeElement !== $("seek")) $("seek").value = ct;
    $("time").textContent = `${fmt(ct)} / ${fmt(m.duration)}`;
    const want = m.paused ? "play" : "pause";
    if ($("play").dataset.st !== want) { $("play").innerHTML = icon(want); $("play").dataset.st = want; }
    const i = curIndex(ct);
    if (i !== S.cur) {
      document.querySelectorAll(".sent.cur").forEach((e) => e.classList.remove("cur"));
      if (i >= 0) {
        const el = document.querySelector(`.sent[data-i="${i}"]`);
        if (el) {
          el.classList.add("cur");
          if (!m.paused) {
            const box = $("text");
            const top = el.offsetTop - box.offsetTop;
            if (top < box.scrollTop || top > box.scrollTop + box.clientHeight - 40) box.scrollTop = top - 40;
            for (let k = 0; k < i; k++) document.querySelector(`.sent[data-i="${k}"]`)?.classList.add("done");
          }
        }
      }
      S.cur = i;
    }
    let wEl = null;
    if (i >= 0 && S.items[i].words) {
      const k = S.items[i].words.findIndex((w) => w.s != null && ct >= w.s && ct < w.e);
      if (k >= 0) wEl = document.querySelector(`.w[data-i="${i}"][data-k="${k}"]`);
    }
    if (wEl !== S.curW) { S.curW?.classList.remove("cur"); wEl?.classList.add("cur"); S.curW = wEl; }
  }
  const rv = $("rv-video");
  if (S.playEnd != null && !rv.paused && rv.currentTime >= S.playEnd) { rv.pause(); S.playEnd = null; }
  requestAnimationFrame(tick);
}
function jump(dir) {
  const m = $("media"), ct = m.currentTime;
  const starts = S.items.filter((x) => !x.skip && x.start != null).map((x) => x.start);
  const target = dir > 0 ? starts.find((s) => s > ct + 0.05) : [...starts].reverse().find((s) => s < ct - 0.5);
  if (target != null) m.currentTime = target;
  else if (dir < 0) m.currentTime = 0;
}

// ---------------------------------------------------------------- whole-page render
function renderMeta() {
  if (S.mode === "plain") {
    $("doc-title").textContent = S.fileName;
    $("doc-meta").textContent = S.items.length ? t("sentences", { n: S.items.length }) : "";
    $("src").innerHTML = `${icon("file")}<span>${esc(S.fileName)}</span>`;
  } else if (S.mode === "project") {
    const name = S.P?.from_srt ? S.P.name : (S.video?.name || S.P?.name || "");
    $("doc-title").textContent = S.P?.video?.name ? stem(S.P.video.name) : name;
    const v = S.P?.video || S.video;
    const parts = [];
    if (S.P?.from_srt) parts.push(`${icon("file")}<span>${esc(S.P.name)}</span>`);
    if (v) parts.push(`${icon("video")}<span>${esc(v.name)} · ${fmt(v.duration)}${S.P?.lang ? " · " + langName(S.P.lang) : ""}</span>`);
    else if (S.P?.from_srt) parts.push(`<span class="muted">· ${esc(t("srt_no_video"))}</span>`);
    $("src").innerHTML = parts.join(" ");
    $("rv-video").hidden = !v;
    if (v && $("rv-video").dataset.vid !== v.id) { $("rv-video").src = `/video/${v.id}`; $("rv-video").dataset.vid = v.id; }
    if (!S.P) $("doc-meta").textContent = "";
  }
}
function renderAll() {
  renderMeta();
  if (S.mode === "project") { renderProgress(); renderChunks(); renderTable(); renderSteps(); if (S.step === 5) renderExport(); }
  renderPlay();
  updateGlossCount();
  if ($("gloss").open) renderGloss();
  if ($("guide").open) renderGuide();
}

// ---------------------------------------------------------------- getting started
let guideLang = null;
function renderGuide() {
  const l = guideLang || S.ui;
  $("guide-body").innerHTML = GUIDE[l];
  $("guide-title").textContent = l === "zh" ? "使用說明" : "Getting started";
  document.querySelectorAll("[data-gl]").forEach((b) => b.classList.toggle("on", b.dataset.gl === l));
}
function openGuide() { guideLang = null; renderGuide(); $("guide").showModal(); }

// ---------------------------------------------------------------- wiring
document.querySelectorAll("[data-ui]").forEach((b) => b.addEventListener("click", () => applyUI(b.dataset.ui)));
$("file").addEventListener("change", (e) => { const f = e.target.files[0]; e.target.value = ""; f && openFile(f); });
$("video").addEventListener("change", (e) => { const f = e.target.files[0]; e.target.value = ""; f && openVideo(f); });
$("guide-btn").onclick = openGuide;
$("welcome-guide").onclick = openGuide;
$("guide-close").onclick = () => $("guide").close();
document.querySelectorAll("[data-gl]").forEach((b) => (b.onclick = () => { guideLang = b.dataset.gl; renderGuide(); }));
$("guide").addEventListener("click", (e) => { const a = e.target.closest("a[href^='#']"); if (a) { e.preventDefault(); $("guide").querySelector(a.getAttribute("href"))?.scrollIntoView({ behavior: "smooth" }); } });

$("steps").addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) go(+b.dataset.s); });
document.querySelectorAll("[data-go]").forEach((b) => b.addEventListener("click", () => go(+b.dataset.go)));
$("p1-start").onclick = startTranscribe;
$("p1-stop").onclick = async () => { await api(`/api/project/${S.pid}/stop`, {}); say("stopping"); };
$("p1-resume").onclick = async () => { await api(`/api/project/${S.pid}/resume`, {}); startPolling(); say(""); };
$("target").addEventListener("change", () => { if (S.P) changeTarget(); });
$("p2-again").onclick = changeTarget;
$("to-table").onclick = () => { showTab("rev"); $("work").scrollIntoView({ behavior: "smooth" }); };

document.querySelectorAll("#tabs button").forEach((b) => (b.onclick = () => showTab(b.dataset.tab)));
$("chunks").addEventListener("click", (e) => { const b = e.target.closest(".chunk"); if (b && !b.disabled) { S.chunk = +b.dataset.c; S.editing = null; renderChunks(); renderTable(); } });
$("filter").addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) { S.filter = b.dataset.f; renderTable(); } });
$("rv").addEventListener("click", async (e) => {
  const join = e.target.closest(".join");
  if (join) { say("joining"); await api(`/api/project/${S.pid}/join`, { id: +join.dataset.id }); say(""); return refresh(true); }
  const pl = e.target.closest("[data-play]");
  if (pl) return playLine(+pl.dataset.play);
  const ck = e.target.closest(".rvck");
  if (ck) return saveLine(+ck.closest("tr").dataset.id, { reviewed: ck.checked });
  const ed = e.target.closest("[data-edit]");
  if (ed) return editCell(ed.closest("tr").querySelector(`[data-ed="${ed.dataset.edit}"]`));
  const cell = e.target.closest("[data-ed]");
  if (cell && !e.target.closest("textarea,button,.edbar") && !getSelection().toString()) editCell(cell);
});
$("rv").addEventListener("contextmenu", (e) => {
  const sel = getSelection().toString().trim();
  const cell = e.target.closest("[data-ed]");
  if (!sel || !cell || sel.length > 80) return;
  e.preventDefault();
  openPop(e.clientX, e.clientY, sel, cell.dataset.ed, +cell.closest("tr").dataset.id);
});
$("pop-line").onclick = () => popAdd(false);
$("pop-all").onclick = () => popAdd(true);
$("pop-cancel").onclick = () => ($("pop").hidden = true);
document.addEventListener("keydown", (e) => { if (e.key === "Escape") $("pop").hidden = true; });
$("mark-chunk").onclick = async () => {
  const ls = chunkLines();
  const c = S.P.chunks.find((x) => x.i === S.chunk);
  const val = !(c && c.reviewed);
  await api(`/api/project/${S.pid}/lines`, { changes: ls.map((l) => ({ id: l.id, reviewed: val })) });
  await refresh(true);
  if (val) {
    const next = S.P.chunks.find((x) => x.status === "ready" && !x.reviewed);
    say(next ? "chunk_marked_next" : "chunk_marked_all", { n: next ? next.i + 1 : "" });
  }
};
$("rt-chunk").onclick = async () => { say("retranslating"); const r = await api(`/api/project/${S.pid}/retranslate`, { chunk: S.chunk }); say("retranslated", { n: r.n }); await refresh(true); };

document.querySelectorAll("[data-gloss]").forEach((b) => (b.onclick = openGloss));
$("gloss-close").onclick = $("gloss-done").onclick = () => $("gloss").close();
$("gloss-find").addEventListener("input", renderGloss);
$("gloss-rows").addEventListener("change", async (e) => {
  const inp = e.target.closest("input[data-k]");
  if (!inp) return;
  const i = +inp.closest("tr").dataset.i;
  S.glossary[i][inp.dataset.k] = inp.value.trim();
  S.glossDirty.push(S.glossary[i].src);
  await saveGloss();
  renderGloss();
});
$("gloss-rows").addEventListener("click", async (e) => {
  const del = e.target.closest("[data-del]");
  if (del) { const g = S.glossary.splice(+del.dataset.del, 1)[0]; S.glossDirty.push(g.src); await saveGloss(); return renderGloss(); }
  if (e.target.closest("#g-add")) {
    const src = $("g-new-src").value.trim(), dst = $("g-new-dst").value.trim();
    if (!src) return $("g-new-src").focus();
    S.glossary.unshift({ src, dst, where: "" });
    S.glossDirty.push(src);
    await saveGloss();
    renderGloss();
  }
});
$("gloss-import").addEventListener("change", async (e) => {
  const f = e.target.files[0]; e.target.value = "";
  if (!f) return;
  const r = await fetch("/api/glossary.txt", { method: "POST", body: await readText(f) });
  S.glossary = await r.json();
  updateGlossCount(); renderGloss();
});
$("gloss-apply").onclick = async () => {
  const terms = [];
  for (const s of S.glossDirty) { terms.push(s); const g = S.glossary.find((x) => x.src === s); if (g?.dst) terms.push(g.dst); }
  $("gloss").close();
  say("retranslating");
  const r = await api(`/api/project/${S.pid}/retranslate`, { terms });
  say("retranslated", { n: r.n });
  S.glossDirty = [];
  await refresh(true);
};

$("voice").addEventListener("change", () => store("kr-voice-" + $("lang").value, $("voice").value));
$("lang").addEventListener("change", async () => { fillVoices(false); if (S.mode === "plain") { await parsePlain(); say("reparsed"); } });
$("vsrc").addEventListener("change", prepareVoiceStep);
$("clean").addEventListener("change", parsePlain);
$("tone").addEventListener("change", applyTone);
["speed", "pause"].forEach((id) => $(id).addEventListener("change", () => ($("tone").value = "custom")));
$("gen").addEventListener("click", generate);
$("gen-top").addEventListener("click", generate);
$("cancel").addEventListener("click", () => S.jobId && api(`/api/job/${S.jobId}/cancel`, {}));
$("out-rows").addEventListener("change", updateSaveSel);
$("save-sel").onclick = saveSelected;

$("text").addEventListener("click", (e) => {
  const m = $("media");
  if (!S.done) return;
  const w = e.target.closest(".w");
  if (w) { const word = S.items[+w.dataset.i].words[+w.dataset.k]; if (word.s != null) { m.currentTime = word.s; m.play(); } return; }
  const s = e.target.closest(".sent");
  if (s) { const it = S.items[+s.dataset.i]; if (it.start != null) { m.currentTime = it.start; m.play(); } }
});
$("play").addEventListener("click", () => { const m = $("media"); if (!m.getAttribute("src")) return; m.paused ? m.play() : m.pause(); });
$("stop").addEventListener("click", () => { const m = $("media"); m.pause(); m.currentTime = 0; document.querySelectorAll(".sent.done").forEach((e) => e.classList.remove("done")); });
$("prev").addEventListener("click", () => jump(-1));
$("next").addEventListener("click", () => jump(1));
$("seek").addEventListener("input", (e) => ($("media").currentTime = +e.target.value));

let quitArmed = false;
$("quit").addEventListener("click", async () => {
  const busy = !$("cancel").hidden || (S.P && S.P.running);
  if (busy && !quitArmed) { quitArmed = true; return say("quit_busy", {}, true); }
  try { await fetch("/api/quit", { method: "POST" }); } catch (e) {}
  document.body.innerHTML = `<p class="closed">${t("closed")}</p>`;
});
const heartbeat = () => fetch("/api/ping").catch(() => {});
setInterval(heartbeat, 20000);
window.addEventListener("beforeunload", (e) => { if (S.P && S.P.running) { e.preventDefault(); e.returnValue = ""; } });

(async function init() {
  heartbeat();
  S.voices = await (await fetch("/api/voices")).json();
  await loadGlossary();
  setMode(null);
  applyUI(recall("kr-ui") || (navigator.language.startsWith("zh") ? "zh" : "en"));
  requestAnimationFrame(tick);
  offerLastProject();
})();

async function offerLastProject() {
  const pid = recall("kr-pid");
  if (!pid) return;
  let P;
  try { P = await api(`/api/project/${pid}`); } catch (e) { return; }
  const b = document.createElement("button");
  b.type = "button"; b.className = "btn sm primary";
  b.textContent = t("continue_last", { n: stem(P.video?.name || P.name) });
  $("welcome").appendChild(b);
  b.onclick = async () => {
    S.video = P.video ? { id: P.video.id, name: P.video.name, duration: P.video.duration } : null;
    S.fileName = P.video?.name || P.name;
    resetVoice();
    setMode("project");
    await loadProject(pid);
    let st = P.chunks.some((c) => c.status === "ready") ? 3 : P.from_srt ? 2 : 1;
    try {  // bring back the last voice made for this video, if the app has not been restarted since
      const saved = JSON.parse(recall("kr-job-" + pid) || "null");
      const j = saved && await api(`/api/job/${saved.id}`);
      if (j && j.status === "done") {
        S.jobId = saved.id; S.jobLang = saved.lang; $("orig").value = saved.orig || "mute";
        S.items = j.items; S.files = j.files; S.media = j.media; S.done = true;
        meters(j, true); setupMedia(); renderAll(); st = 5;
      }
    } catch (e) {}
    S.step = st; go(st, true);
    if (P.running || (!P.done && !P.from_srt)) startPolling();
  };
}
