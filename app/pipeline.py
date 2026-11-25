"""Video -> subtitles -> translation pipeline for Kokoro Reader.

A Project is one video (or one opened .srt). Transcription runs chunk by chunk (about N minutes,
cut at the quietest moment near each mark), each chunk is translated as soon as it is transcribed,
and everything is saved to project.json so a stopped job resumes where it left off.
Fully local: faster-whisper for speech, Opus-MT (ctranslate2) for translation, OpenCC for Taiwan
Traditional characters.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
import uuid
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "models"
EXE = ".exe" if os.name == "nt" else ""  # Windows ffmpeg.exe, macOS ffmpeg
FFMPEG = ROOT / "tools" / "ffmpeg" / f"ffmpeg{EXE}"
WHISPER = {"best": "large-v3-turbo", "fast": "small"}
SR16 = 16000
ENDS = (".", "?", "!", "。", "？", "！", "…")
CJK = r"[㐀-鿿＀-￯]"
NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def is_cjk(text):
    return bool(re.search(r"[一-鿿]", text or ""))


# ---------------------------------------------------------------- audio

def load_audio(media: Path) -> np.ndarray:
    raw = subprocess.run([str(FFMPEG), "-nostdin", "-v", "error", "-i", str(media), "-vn", "-ac", "1",
                          "-ar", str(SR16), "-f", "f32le", "-"], capture_output=True, check=True,
                         creationflags=NOWIN).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def chunk_bounds(audio: np.ndarray, minutes: float) -> list[tuple[float, float]]:
    """Cut near every `minutes` mark at the quietest half second within +-30 s."""
    dur = len(audio) / SR16
    if minutes <= 0 or dur <= minutes * 60 * 1.3:
        return [(0.0, dur)]
    hop = SR16 // 10
    n = len(audio) // hop
    rms = np.sqrt(np.mean(audio[: n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    smooth = np.convolve(rms, np.ones(5) / 5, mode="same")
    cuts, t = [0.0], minutes * 60
    while t < dur - 60:
        lo, hi = int((t - 30) * 10), min(int((t + 30) * 10), n - 1)
        k = lo + int(np.argmin(smooth[lo:hi]))
        cuts.append(k / 10)
        t = k / 10 + minutes * 60
    cuts.append(dur)
    return list(zip(cuts[:-1], cuts[1:]))


# ---------------------------------------------------------------- subtitle lines from words

MAX_SEC, MAX_CHARS, MAX_CJK, PAUSE = 7.0, 84, 40, 0.6


def group_words(words: list[dict]) -> list[dict]:
    """words [{start,end,word,prob}] -> cues [{start,end,text,prob}]."""
    cues, cur = [], []

    def text_of(ws):
        return "".join(w["word"] for w in ws).strip()

    def flush():
        if cur:
            cues.append({"start": cur[0]["start"], "end": cur[-1]["end"], "text": text_of(cur),
                         "probs": [w["prob"] for w in cur]})
            cur.clear()

    for i, w in enumerate(words):
        if cur:
            gap = w["start"] - cur[-1]["end"]
            t = text_of(cur + [w])
            limit = MAX_CJK if is_cjk(t) else MAX_CHARS
            if gap > PAUSE:
                flush()
            elif w["end"] - cur[0]["start"] > MAX_SEC or len(t) > limit:
                cut = max((k for k, x in enumerate(cur[:-1])
                           if x["word"].strip().endswith((",", "，", "、", ";"))), default=None)
                if cut is not None and cut >= 2:
                    rest = cur[cut + 1:]
                    del cur[cut + 1:]
                    flush()
                    cur.extend(rest)
                else:
                    flush()
        cur.append(w)
        t = text_of(cur)
        nxt = words[i + 1] if i + 1 < len(words) else None
        if t.endswith(ENDS) and (nxt is None or len(t) > 25 or nxt["start"] - w["end"] > 0.3):
            flush()
    flush()
    out = []
    for c in cues:  # merge short tails into the line before
        if out:
            p = out[-1]
            short = (c["end"] - c["start"] < 1.2 or len(c["text"]) < 12) and not p["text"].endswith(ENDS)
            if short and c["start"] - p["end"] < 0.4 and c["end"] - p["start"] <= MAX_SEC + 2 \
                    and len(p["text"]) + len(c["text"]) <= MAX_CHARS + 30:
                sep = "" if is_cjk(c["text"]) else " "
                p.update(end=c["end"], text=(p["text"] + sep + c["text"]).strip(), probs=p["probs"] + c["probs"])
                continue
        out.append(c)
    return out


# ---------------------------------------------------------------- glossary

class Glossary:
    """English term <-> Chinese term. dst '' means keep the term as it is."""

    def __init__(self, path: Path, seed: Path | None):
        self.path, self.lock = path, threading.Lock()
        if not path.exists():
            items = []
            if seed and seed.exists():
                for line in seed.read_text(encoding="utf-8-sig").splitlines():
                    line = line.split("#", 1)[0].strip()
                    if line:
                        src, _, dst = line.partition("=")
                        items.append({"src": src.strip(), "dst": dst.strip(), "added": "starter", "where": ""})
            self.save(items)

    def load(self) -> list[dict]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def save(self, items):
        clean, seen = [], set()
        for it in items:
            src = (it.get("src") or "").strip()
            if src and src.lower() not in seen:
                seen.add(src.lower())
                clean.append({"src": src, "dst": (it.get("dst") or "").strip(),
                              "added": it.get("added") or date.today().isoformat(), "where": it.get("where", "")})
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(clean, ensure_ascii=False, indent=1), encoding="utf-8")
        return clean

    def pairs(self, to: str) -> dict[str, str]:
        """Terms to protect when translating into `to`: source text -> exact output."""
        out = {}
        for g in self.load():
            src, dst = g["src"], g["dst"]
            if to == "zh":
                out[src] = dst or src
            else:
                out[src] = src  # English or brand terms inside Chinese text stay as they are
                if dst:
                    out[dst] = src
        return out


# ---------------------------------------------------------------- translation

def tidy_zh(s):
    s = re.sub(r"\s+([，。、！？：；])", r"\1", s)
    s = s.replace(",", "，").replace("?", "？").replace("!", "！").replace(":", "：").replace(";", "；")
    s = re.sub(rf"(?<={CJK})\s+(?={CJK})", "，", s)
    s = re.sub(rf"(?<={CJK})\s+(?=[A-Za-z0-9])|(?<=[A-Za-z0-9])\s+(?={CJK})", " ", s)
    s = re.sub(r"，{2,}", "，", s)
    s = re.sub(r"，([。！？])", r"\1", s)
    s = re.sub(r"([，。、！？：；])\s+", r"\1", s)
    return s.strip(" ，")


class Translator:
    def __init__(self, to: str):
        import ctranslate2
        import opencc
        from transformers import MarianTokenizer
        d = MODELS / f"opus-mt-{'en-zh' if to == 'zh' else 'zh-en'}"
        self.to = to
        self.tok = MarianTokenizer.from_pretrained(str(d))
        self.tr = ctranslate2.Translator(str(d), device="cpu", compute_type="int8")
        self.prefix = ">>cmn_Hant<< " if to == "zh" else ""
        self.cc = opencc.OpenCC("s2twp") if to == "zh" else None

    def __call__(self, texts: list[str], glossary: dict[str, str]) -> list[str]:
        if not texts:
            return []
        terms = sorted(glossary.items(), key=lambda kv: -len(kv[0]))
        prepared, slots = [], []
        for t in texts:
            found = {}
            for k, (term, target) in enumerate(terms):
                pat = re.compile(re.escape(term), re.I) if not is_cjk(term) else re.compile(re.escape(term))
                if pat.search(t):
                    tag = f"X{k}Q"
                    t = pat.sub(f" {tag} " if is_cjk(term) else tag, t)
                    found[tag] = target
            prepared.append(re.sub(r"\s{2,}", " ", t).strip())
            slots.append(found)
        src = [self.tok.convert_ids_to_tokens(self.tok.encode(self.prefix + t)) for t in prepared]
        res = self.tr.translate_batch(src, max_batch_size=16, beam_size=4)
        out = []
        for r, found in zip(res, slots):
            o = self.tok.decode(self.tok.convert_tokens_to_ids(r.hypotheses[0]), skip_special_tokens=True)
            if self.cc:
                o = self.cc.convert(o)
            for tag, target in found.items():
                pat = (r"\s*" + re.escape(tag) + r"\s*") if is_cjk(target) else re.escape(tag)
                o = re.sub(pat, lambda _m, s=target: s, o, flags=re.I)
            o = tidy_zh(o) if self.to == "zh" else re.sub(r"\s+([,.!?;:])", r"\1", o).strip()
            out.append(o)
        return out


SENT_END = ENDS + ('"', "”", "」")
SPLIT_AT = "，、。；：！？,;:!?"


def sentence_groups(lines: list[dict]) -> list[list[dict]]:
    """Consecutive lines that form one sentence (same chunk, close together, max 4 lines / 25 s)."""
    groups, cur = [], []
    for ln in lines:
        if cur and (ln["chunk"] != cur[-1]["chunk"] or ln["start"] - cur[-1]["end"] > 1.5
                    or len(cur) >= 4 or ln["end"] - cur[0]["start"] > 25):
            groups.append(cur)
            cur = []
        cur.append(ln)
        if ln["src"].rstrip().endswith(SENT_END):
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    return groups


def split_translation(text: str, weights: list[int], zh: bool) -> list[str]:
    """Divide one translated sentence over n lines, cutting at punctuation near the proportional spots."""
    n = len(weights)
    if n == 1:
        return [text]
    total = sum(weights) or 1
    L = len(text)
    marks = [i + 1 for i, ch in enumerate(text) if ch in SPLIT_AT and 0 < i + 1 < L]
    if not zh:
        spaces = [i + 1 for i, ch in enumerate(text) if ch == " "]
    else:  # word boundaries, so a cut never splits a Chinese word such as 指南
        import jieba
        spaces, pos = [], 0
        for w in jieba.cut(text):
            pos += len(w)
            if 0 < pos < L:
                spaces.append(pos)
    cuts, acc, prev = [], 0, 0
    for k in range(n - 1):
        acc += weights[k]
        want = round(L * acc / total)
        window = max(3, L // (n * 3))
        near = [m for m in marks if prev < m < L and abs(m - want) <= window]
        if near:
            c = min(near, key=lambda m: abs(m - want))
        else:
            sp = [m for m in spaces if prev < m < L]
            c = min(sp, key=lambda m: abs(m - want)) if sp else want
        c = max(prev + 1, min(c, L - (n - 1 - k)))
        cuts.append(c)
        prev = c
    parts = [text[a:b].strip() for a, b in zip([0] + cuts, cuts + [L])]
    return [p.strip(" ，,") if i < n - 1 else p.strip() for i, p in enumerate(parts)]


def translate_lines(tr: "Translator", lines: list[dict], glossary: dict[str, str]) -> dict[int, str]:
    """Translate whole sentences, then divide each over its lines. Returns {line id: text}."""
    groups = sentence_groups(lines)
    joined = [(" " if not is_cjk(g[0]["src"]) else "").join(x["src"].strip() for x in g) for g in groups]
    out = tr(joined, glossary)
    zh = tr.to == "zh"
    res = {}
    for g, t in zip(groups, out):
        parts = split_translation(t, [max(1, len(x["src"])) for x in g], zh)
        for x, p in zip(g, parts):
            res[x["id"]] = p
    return res


# ---------------------------------------------------------------- flags

def speak_seconds(text: str) -> float:
    """Rough speaking time for Kokoro at speed 1.0."""
    cjk = len(re.findall(r"[一-鿿]", text))
    latin = len(re.findall(r"[A-Za-z0-9]+", text))
    return cjk * 0.27 + latin * 0.36 + 0.2  # 0.27 s per character: measured median for zm_009


def flag_lines(lines: list[dict]):
    for k, ln in enumerate(lines):
        flags = []
        nxt = lines[k + 1] if k + 1 < len(lines) else None
        # cut mid-clause (no punctuation at all): the translation of each half is usually broken
        if nxt and not ln["src"].rstrip().endswith(ENDS + ('"', "”", "」", ",", "，", "、", ";", "；", ":", "：", "-", "—")) \
                and nxt["chunk"] == ln["chunk"] and nxt["start"] - ln["end"] < 1.0:
            flags.append("cont")
        voice_text = ln.get("tr") or ln["src"]
        room = (nxt["start"] if nxt else ln["end"] + 1.0) - ln["start"]
        if speak_seconds(voice_text) / 1.25 > room:
            flags.append("long")
        if ln.get("unsure"):
            flags.append("unsure")
        ln["flags"] = flags


# ---------------------------------------------------------------- projects

class Project:
    def __init__(self, folder: Path, data: dict):
        self.folder, self.d = folder, data
        self.lock = threading.RLock()
        self.cancel = False
        self.thread: threading.Thread | None = None
        self.message = ""

    # persistence ----------------------------------------------------------
    @property
    def id(self):
        return self.d["id"]

    def save(self):
        with self.lock:
            tmp = self.folder / "project.json.tmp"
            tmp.write_text(json.dumps(self.d, ensure_ascii=False), encoding="utf-8")
            tmp.replace(self.folder / "project.json")

    @classmethod
    def load(cls, folder: Path):
        return cls(folder, json.loads((folder / "project.json").read_text(encoding="utf-8")))

    def snapshot(self, since_rev: int | None = None):
        with self.lock:
            d = dict(self.d)
            d["running"] = bool(self.thread and self.thread.is_alive())
            d["message"] = self.message
            if since_rev is not None and since_rev == d.get("rev"):
                d.pop("lines")
            return d

    def touch(self):
        self.d["rev"] = self.d.get("rev", 0) + 1

    # lines ----------------------------------------------------------------
    def lines_of(self, chunk=None):
        return [ln for ln in self.d["lines"] if chunk is None or ln["chunk"] == chunk]

    def reflag(self):
        flag_lines(self.d["lines"])
        for c in self.d["chunks"]:
            ls = self.lines_of(c["i"])
            c["reviewed"] = bool(ls) and all(ln["reviewed"] for ln in ls)
        self.touch()


class Pipeline:
    """Owns the projects, the speech model and the translators."""

    def __init__(self, work: Path, glossary: Glossary):
        self.root = work / "projects"
        self.root.mkdir(parents=True, exist_ok=True)
        self.glossary = glossary
        self.projects: dict[str, Project] = {}
        self._whisper: dict[str, object] = {}
        self._tr: dict[str, Translator] = {}
        self.model_lock = threading.Lock()   # one transcription at a time
        self.tr_lock = threading.Lock()      # translation runs beside it
        for f in self.root.glob("*/project.json"):
            try:
                p = Project.load(f.parent)
                if not p.d.get("done") and p.d.get("status") not in ("error",):
                    p.d["status"] = "stopped"  # the app was closed while it was working
                    for c in p.d["chunks"]:
                        if c["status"] == "transcribing":
                            c["status"] = "queued"
                p.reflag()
                self.projects[p.id] = p
            except Exception:
                pass

    # models ---------------------------------------------------------------
    def whisper(self, accuracy: str):
        name = WHISPER.get(accuracy, WHISPER["best"])
        if name not in self._whisper:
            from faster_whisper import WhisperModel
            import os
            self._whisper[name] = WhisperModel(name, device="cpu", compute_type="int8",
                                               cpu_threads=os.cpu_count() or 4)
        return self._whisper[name]

    def translator(self, to: str) -> Translator:
        if to not in self._tr:
            self._tr[to] = Translator(to)
        return self._tr[to]

    # create ---------------------------------------------------------------
    def _new(self, name, video, duration, spoken, target, chunk_min, accuracy, from_srt=False):
        pid = uuid.uuid4().hex[:12]
        folder = self.root / pid
        folder.mkdir(parents=True)
        p = Project(folder, {
            "id": pid, "name": name, "video": video, "duration": duration, "spoken": spoken,
            "lang": None if spoken == "auto" else spoken, "target": target, "chunk_min": chunk_min,
            "accuracy": accuracy, "from_srt": from_srt, "chunks": [], "lines": [], "status": "queued",
            "done": False, "t_audio": 0.0, "t_work": 0.0, "t_translate": 0.0, "rev": 0,
            "created": time.time(),
        })
        self.projects[pid] = p
        return p

    def from_video(self, video: dict, spoken, target, chunk_min, accuracy):
        p = self._new(video["name"], video, video["duration"], spoken, target, chunk_min, accuracy)
        p.save()
        self.start(p)
        return p

    def from_srt(self, name, cues: list[dict], target, video: dict | None):
        text = " ".join(c["text"] for c in cues)
        lang = "zh" if len(re.findall(r"[一-鿿]", text)) > 0.2 * max(1, len(text.replace(" ", ""))) else "en"
        dur = video["duration"] if video else (cues[-1]["end"] if cues else 0)
        p = self._new(name, video, dur, lang, target, 0, "best", from_srt=True)
        p.d["chunks"] = [{"i": 0, "start": 0.0, "end": dur, "status": "transcribed", "reviewed": False}]
        p.d["lines"] = [{"id": k, "chunk": 0, "start": c["start"], "end": c["end"], "src": c["text"],
                         "tr": "", "tr_auto": "", "edited": False, "reviewed": False, "skip": False,
                         "unsure": False, "flags": []} for k, c in enumerate(cues)]
        p.d["status"] = "translating"
        p.save()
        self.start(p)
        return p

    # run ------------------------------------------------------------------
    def start(self, p: Project):
        if p.thread and p.thread.is_alive():
            return
        p.cancel = False
        p.thread = threading.Thread(target=self._run, args=(p,), daemon=True)
        p.thread.start()

    def stop(self, p: Project):
        p.cancel = True

    def _run(self, p: Project):
        try:
            with self.model_lock:
                self._work(p)
        except Exception as e:  # report on the page, keep the server alive
            with p.lock:
                p.d["status"] = "error"
                p.message = f"{type(e).__name__}: {e}"
                p.touch()
                p.save()

    def _work(self, p: Project):
        d = p.d
        audio = None
        if not d["from_srt"] and not d["chunks"]:
            with p.lock:
                d["status"] = "preparing"
                p.touch()
            audio = load_audio(Path(d["video"]["path"]))
            d["chunks"] = [{"i": k, "start": round(a, 2), "end": round(b, 2), "status": "queued", "reviewed": False}
                           for k, (a, b) in enumerate(chunk_bounds(audio, d["chunk_min"]))]
            p.save()
        for c in d["chunks"]:
            if p.cancel:
                break
            if c["status"] in ("queued", "transcribing"):
                if audio is None:
                    audio = load_audio(Path(d["video"]["path"]))
                self._transcribe_chunk(p, audio, c)
                if p.cancel:
                    break
            if c["status"] == "transcribed" or (c["status"] == "ready" and d["target"] != "off"
                                                 and any(not ln["tr"] for ln in p.lines_of(c["i"]))):
                self._translate_chunk(p, c)
        with p.lock:
            if p.cancel:
                d["status"] = "stopped"
            else:
                d["status"], d["done"] = "done", True
            p.touch()
            p.save()

    def _transcribe_chunk(self, p: Project, audio, c):
        d = p.d
        with p.lock:
            c["status"], d["status"] = "transcribing", "transcribing"
            p.message = ""
            p.touch()
        model = self.whisper(d["accuracy"])
        a0, a1 = int(c["start"] * SR16), int(c["end"] * SR16)
        t0 = time.perf_counter()
        segs, info = model.transcribe(audio[a0:a1], language=d["lang"], vad_filter=True, word_timestamps=True,
                                      beam_size=5, condition_on_previous_text=False)
        if not d["lang"]:
            d["lang"] = "zh" if info.language in ("zh", "yue") else info.language
        words = []
        for s in segs:
            if p.cancel:
                with p.lock:
                    c["status"] = "queued"
                    p.touch()
                return
            for w in s.words or []:
                words.append({"start": round(w.start + c["start"], 3), "end": round(w.end + c["start"], 3),
                              "word": w.word, "prob": w.probability})
            with p.lock:
                c["progress"] = round(min(1.0, s.end / max(c["end"] - c["start"], 1)), 3)
                p.touch()
        cues = group_words(words)
        if any(is_cjk(x["text"]) for x in cues):
            import opencc
            cc = opencc.OpenCC("s2tw")
            for x in cues:
                x["text"] = cc.convert(x["text"])
        with p.lock:
            base = max((ln["id"] for ln in d["lines"]), default=-1) + 1
            for k, x in enumerate(cues):
                probs = x["probs"] or [1.0]
                unsure = sum(1 for q in probs if q < 0.5) / len(probs) > 0.3
                d["lines"].append({"id": base + k, "chunk": c["i"], "start": round(x["start"], 3),
                                   "end": round(x["end"], 3), "src": x["text"], "tr": "", "tr_auto": "",
                                   "edited": False, "reviewed": False, "skip": False, "unsure": unsure, "flags": []})
            d["lines"].sort(key=lambda ln: ln["start"])
            c["status"], c["progress"] = "transcribed", 1.0
            d["t_audio"] += c["end"] - c["start"]
            d["t_work"] += time.perf_counter() - t0
            p.reflag()
            p.save()

    def target_lang(self, p: Project):
        t = p.d["target"]
        if t == "auto":
            return "zh" if (p.d["lang"] or "en") != "zh" else "en"
        return t

    def _translate_chunk(self, p: Project, c):
        d = p.d
        to = self.target_lang(p)
        with p.lock:
            c["status"] = "translating" if c["status"] != "ready" else c["status"]
            d["status"] = "translating"
            p.touch()
        if to != "off" and to != (d["lang"] or "en"):
            groups = [g for g in sentence_groups(p.lines_of(c["i"])) if any(not x["tr"] for x in g)]
            sel = [x for g in groups for x in g]
            t0 = time.perf_counter()
            with self.tr_lock:
                res = translate_lines(self.translator(to), sel, self.glossary.pairs(to))
            with p.lock:
                for ln in sel:
                    if not ln["edited"]:
                        ln["tr"] = ln["tr_auto"] = res.get(ln["id"], "")
                d["t_translate"] += time.perf_counter() - t0
        with p.lock:
            c["status"] = "ready"
            p.reflag()
            p.save()

    # edits ----------------------------------------------------------------
    def retranslate(self, p: Project, ids: list[int] | None = None, chunk: int | None = None,
                    terms: list[str] | None = None, all_lines=False, keep_edits=True):
        """Translate again: given lines, a chunk, lines containing given terms, or everything."""
        with self.tr_lock:
            to = self.target_lang(p)
            if to == "off" or to == (p.d["lang"] or "en"):
                return []
            lines = p.d["lines"]
            if ids is not None:
                todo = [ln for ln in lines if ln["id"] in set(ids)]
            elif chunk is not None:
                todo = [ln for ln in lines if ln["chunk"] == chunk and not (keep_edits and ln["edited"])]
            elif terms:
                low = [t.lower() for t in terms if t]
                todo = [ln for ln in lines if not (keep_edits and ln["edited"])
                        and any(t in ln["src"].lower() for t in low)]
            else:
                todo = [ln for ln in lines if not (keep_edits and ln["edited"])] if all_lines else []
            # translate whole sentences: take every sentence that contains a requested line
            want = {ln["id"] for ln in todo}
            groups = [g for g in sentence_groups(lines) if any(x["id"] in want for x in g)]
            sel = [x for g in groups for x in g]
            res = translate_lines(self.translator(to), sel, self.glossary.pairs(to))
            changed = []
            with p.lock:
                for ln in sel:
                    if ln["id"] in want or not ln["edited"]:
                        ln["tr"] = ln["tr_auto"] = res.get(ln["id"], ln["tr"])
                        ln["edited"] = False
                        changed.append(ln["id"])
                p.reflag()
                p.save()
            return changed

    def update_lines(self, p: Project, changes: list[dict]):
        with p.lock:
            by_id = {ln["id"]: ln for ln in p.d["lines"]}
            for ch in changes:
                ln = by_id.get(ch.get("id"))
                if not ln:
                    continue
                if "tr" in ch:
                    ln["tr"] = ch["tr"].strip()
                    ln["edited"] = ln["tr"] != ln["tr_auto"]
                if "src" in ch:
                    ln["src"] = ch["src"].strip()
                    ln["unsure"] = False
                for k in ("reviewed", "skip"):
                    if k in ch:
                        ln[k] = bool(ch[k])
            p.reflag()
            p.save()

    def join(self, p: Project, lid: int):
        with p.lock:
            ls = p.d["lines"]
            k = next((i for i, ln in enumerate(ls) if ln["id"] == lid), None)
            if k is None or k + 1 >= len(ls):
                return
            a, b = ls[k], ls[k + 1]
            zh = is_cjk(a["src"])
            a["src"] = (a["src"] + ("" if zh else " ") + b["src"]).strip()
            tsep = "" if is_cjk(a["tr"]) else " "
            a["tr"] = (a["tr"] + tsep + b["tr"]).strip()
            a["tr_auto"] = (a["tr_auto"] + tsep + b["tr_auto"]).strip()
            a["end"], a["unsure"] = b["end"], a["unsure"] or b["unsure"]
            a["edited"] = a["edited"] or b["edited"]
            del ls[k + 1]
            p.reflag()
            p.save()
        if not a["edited"] and a["tr"]:
            self.retranslate(p, ids=[a["id"]])

    def set_target(self, p: Project, target: str):
        with p.lock:
            p.d["target"] = target
            for ln in p.d["lines"]:
                ln["tr"] = ln["tr_auto"] = ""
                ln["edited"] = False
            p.touch()
        self.retranslate(p, all_lines=True, keep_edits=False)


# ---------------------------------------------------------------- SRT writing

def fmt_t(t):
    ms = int(round(max(t, 0) * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def srt_text(lines: list[dict], which: str) -> str:
    out, n = [], 0
    for ln in lines:
        text = {"src": ln["src"], "tr": ln["tr"] or ln["src"],
                "bi": ln["src"] + ("\n" + ln["tr"] if ln["tr"] else "")}[which]
        n += 1
        out += [str(n), f"{fmt_t(ln['start'])} --> {fmt_t(ln['end'])}", text, ""]
    return "\n".join(out)
