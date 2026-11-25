"""Speech engine for Kokoro Reader: models, text clean-up, SRT fitting and export."""
from __future__ import annotations

import os
import re
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 24000
EN_REPO = "hexgrad/Kokoro-82M"
ZH_REPO = "hexgrad/Kokoro-82M-v1.1-zh"
LANG_CODES = {"en-us": "a", "en-gb": "b", "zh": "z"}

ROOT = Path(__file__).resolve().parent.parent
EXE = ".exe" if os.name == "nt" else ""  # Windows ffmpeg.exe, macOS ffmpeg
FFMPEG = ROOT / "tools" / "ffmpeg" / f"ffmpeg{EXE}"
FFPROBE = ROOT / "tools" / "ffmpeg" / f"ffprobe{EXE}"
# eSpeak NG comes with the espeakng_loader package, which misaki points phonemizer at.

# Best-rated first, from the Kokoro voice cards.
VOICES = {
    "en-us": ["af_heart", "af_bella", "af_nicole", "af_aoede", "af_kore", "af_sarah", "af_nova",
              "af_sky", "af_alloy", "af_jessica", "af_river", "am_michael", "am_fenrir", "am_puck",
              "am_echo", "am_eric", "am_liam", "am_onyx", "am_adam", "am_santa"],
    "en-gb": ["bf_emma", "bf_isabella", "bf_alice", "bf_lily", "bm_george", "bm_fable", "bm_lewis",
              "bm_daniel"],
    "zh": [f"zf_{n:03d}" for n in (1, 2, 3, 4, 5, 6, 7, 8, 17, 18, 19, 21, 22, 23, 24, 26, 27, 28, 32,
                                   36, 38, 39, 40, 42, 43, 44, 46, 47, 48, 49, 51, 59, 60, 67, 70, 71,
                                   72, 73, 74, 75, 76, 77, 78, 79, 83, 84, 85, 86, 87, 88, 90, 92, 93,
                                   94, 99)]
          + [f"zm_{n:03d}" for n in (9, 10, 11, 12, 13, 14, 15, 16, 20, 25, 29, 30, 31, 33, 34, 35, 37,
                                     41, 45, 50, 52, 53, 54, 55, 56, 57, 58, 61, 62, 63, 64, 65, 66, 68,
                                     69, 80, 81, 82, 89, 91, 95, 96, 97, 98, 100)],
}


# ---------------------------------------------------------------- text helpers

def parse_srt_time(s: str) -> float:
    h, m, rest = s.strip().replace(".", ",").split(":")
    sec, ms = (rest.split(",") + ["0"])[:2]
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms.ljust(3, "0")[:3]) / 1000


def fmt_srt_time(t: float) -> str:
    ms = int(round(max(t, 0) * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def parse_srt(raw: str) -> list[dict]:
    cues = []
    for block in re.split(r"\n\s*\n", raw.replace("\r\n", "\n").strip()):
        lines = [x for x in block.strip().split("\n") if x.strip()]
        k = next((i for i, x in enumerate(lines) if "-->" in x), None)
        if k is None:
            continue
        a, b = lines[k].split("-->")
        text = " ".join(lines[k + 1:]).strip()
        if text:
            cues.append({"start": parse_srt_time(a), "end": parse_srt_time(b.split()[0]), "text": text})
    return cues


def split_sentences(raw: str) -> list[dict]:
    out = []
    for p, para in enumerate(re.split(r"\n\s*\n", raw.replace("\r\n", "\n"))):
        para = re.sub(r"\s*\n\s*", " ", para).strip()
        for s in re.split(r"(?<=[.!?])\s+|(?<=[。！？])", para):
            if s.strip():
                out.append({"text": s.strip(), "para": p})
    return out


DOMAIN = r"(?:com|net|org|io|tw|ai|co|gov|edu)"


def clean_text(text: str, lang: str, speak: bool = True) -> str:
    """Fix subtitle typos. speak=True also rewrites URLs the way they should be said."""
    t = re.sub(r"\s+", " ", text).strip()
    # "flir. com /thermal-studio-suite" -> "flir.com/thermal-studio-suite"
    t = re.sub(rf"\b([A-Za-z0-9-]+)\.\s+({DOMAIN})\b", r"\1.\2", t)
    t = re.sub(rf"(\.{DOMAIN})\s+/(?=[\w-])", r"\1/", t)
    # click'Import from Camera'on -> click "Import from Camera" on
    t = re.sub(r"(\w)?'([A-Z][^'\n]{0,60}?)'(\w)?",
               lambda m: f'{(m.group(1) or "")} "{m.group(2)}" {(m.group(3) or "")}', t)
    t = re.sub(r"\s+([,.;:!?])", r"\1", re.sub(r"\s{2,}", " ", t)).strip()
    if speak and lang != "zh":
        def say_url(m):
            spoken = f"{m.group(1)} dot {m.group(2)}"
            if m.group(3):
                spoken += " slash " + m.group(3).strip("/").replace("/", " slash ").replace("-", " ")
            return spoken
        t = re.sub(rf"\b([A-Za-z0-9-]+)\.({DOMAIN})(/[\w\-/]*)?", say_url, t)
    return t


def auto_skip(text: str) -> bool:
    return "©" in text or bool(re.search(r"all\s*rights\s*re", text, re.I))


# ---------------------------------------------------------------- engine

@dataclass
class Job:
    id: str
    folder: Path
    status: str = "queued"
    message: str = ""
    n: int = 0
    i: int = 0
    load_time: float = 0.0
    gen_time: float = 0.0
    audio_time: float = 0.0
    chars: int = 0
    started: float = field(default_factory=time.perf_counter)
    items: list = field(default_factory=list)
    files: dict = field(default_factory=dict)
    media: str = ""
    duration: float = 0.0
    cancel: bool = False

    def snapshot(self):
        busy = self.status in ("loading", "running", "exporting")
        return {
            "status": self.status, "message": self.message, "n": self.n, "i": self.i,
            "load_time": round(self.load_time, 2), "gen_time": round(self.gen_time, 2),
            "audio_time": round(self.audio_time, 2), "chars": self.chars,
            "elapsed": round(time.perf_counter() - self.started, 1) if busy else None,
            "items": self.items if self.status == "done" else [],
            "files": self.files, "media": self.media, "duration": round(self.duration, 2),
        }


class Engine:
    def __init__(self):
        self._pipes: dict[str, object] = {}
        self._cache: dict[tuple, tuple] = {}
        self.lock = threading.Lock()

    # models ---------------------------------------------------------------
    def pipeline(self, lang: str):
        """Return (pipeline, seconds spent loading now)."""
        if lang in self._pipes:
            return self._pipes[lang], 0.0
        t0 = time.perf_counter()
        from kokoro import KModel, KPipeline
        if lang == "zh":
            model = KModel(repo_id=ZH_REPO).eval()
            en = KPipeline(lang_code="a", repo_id=ZH_REPO, model=False)
            self._pipes["zh"] = KPipeline(lang_code="z", repo_id=ZH_REPO, model=model,
                                          en_callable=lambda w: next(en(w)).phonemes)
        else:
            shared = next((p.model for k, p in self._pipes.items() if k != "zh"), None)
            model = shared or KModel(repo_id=EN_REPO).eval()
            self._pipes[lang] = KPipeline(lang_code=LANG_CODES[lang], repo_id=EN_REPO, model=model)
        return self._pipes[lang], time.perf_counter() - t0

    def synth(self, text, lang, voice, blend, amount, speed):
        """Return (audio float32, words or None, seconds of compute, from_cache)."""
        key = (text, lang, voice, blend, amount, round(speed, 3))
        if key in self._cache:
            a, w = self._cache[key]
            return a, w, 0.0, True
        pipe, _ = self.pipeline(lang)
        pack = voice
        if blend and amount > 0:
            pack = pipe.load_voice(voice) * (1 - amount) + pipe.load_voice(blend) * amount
        if lang == "zh":
            def sp(n, s=speed):  # slow long Chinese sentences, as the model card does
                base = 1.0 if n <= 83 else (1 - (n - 83) / 500 if n < 183 else 0.8)
                return base * 1.1 * s
        else:
            sp = speed
        t0 = time.perf_counter()
        chunks, words, off = [], [], 0.0
        for r in pipe(text, voice=pack, speed=sp):
            if r.audio is None:
                continue
            a = r.audio.numpy().astype(np.float32)
            if r.tokens:
                for tk in r.tokens:
                    s = None if tk.start_ts is None else off + tk.start_ts
                    e = None if tk.end_ts is None else off + tk.end_ts
                    words.append({"t": tk.text, "w": tk.whitespace, "s": s, "e": e})
            chunks.append(a)
            off += len(a) / SR
        audio = np.concatenate(chunks) if chunks else np.zeros(1, np.float32)
        result = (audio, words or None)
        self._cache[key] = result
        return audio, result[1], time.perf_counter() - t0, False

    # jobs -----------------------------------------------------------------
    def run(self, job: Job, req: dict):
        with self.lock:
            try:
                self._run(job, req)
            except Exception as e:  # report, never crash the server
                job.status, job.message = "error", f"{type(e).__name__}: {e}"

    def _run(self, job: Job, req: dict):
        lang, mode = req["lang"], req["mode"]
        voice, blend = req["voice"], req.get("blend") or None
        amount, speed = float(req.get("amount", 0)), float(req.get("speed", 1.0))
        pause = float(req.get("pause", 0.35))
        items = [dict(x) for x in req["items"]]
        job.n = sum(1 for x in items if not x.get("skip"))

        job.status = "loading"
        _, job.load_time = self.pipeline(lang)
        job.status = "running"

        def gen(text, spd):
            a, w, secs, _ = self.synth(text, lang, voice, blend, amount, spd)
            job.gen_time += secs
            return a, w

        placed = []  # (start, audio)
        if mode == "srt":
            self._fit_srt(job, items, gen, speed, req)
            if job.status == "cancelled":
                return
        else:
            t, last_para = 0.0, None
            for it in items:
                if job.cancel:
                    job.status = "cancelled"
                    return
                if last_para is not None and it.get("para") != last_para:
                    t += pause
                a, w = gen(it["text"], speed)
                it.update(start=t, end=t + len(a) / SR, status="ok")
                it["words"] = [dict(x, s=None if x["s"] is None else x["s"] + t,
                                    e=None if x["e"] is None else x["e"] + t) for x in w] if w else None
                it["_audio"] = a
                t = it["end"] + pause
                last_para = it.get("para")
                job.i += 1
                job.audio_time += len(a) / SR
                job.chars += len(it["text"])

        job.status = "exporting"
        spoken = [x for x in items if x.get("_audio") is not None]
        total = max([x["end"] for x in spoken] + [job.duration]) + 0.3
        track = np.zeros(int(total * SR) + 1, np.float32)
        for x in spoken:
            s = int(x["start"] * SR)
            a = x.pop("_audio")
            track[s:s + len(a)] += a[: len(track) - s]
        peak = float(np.abs(track).max() or 1)
        if peak > 0.99:
            track *= 0.99 / peak
        for x in items:
            x.pop("_audio", None)
        self._export(job, track, items, req)
        job.items = items
        job.status = "done"

    def _fit_srt(self, job, items, gen, speed, req):
        fit, max_up = req.get("fit", "both"), float(req.get("max_speed", 1.25))
        use_speed, use_gaps = fit in ("both", "speed"), fit in ("both", "gaps")
        spoken = [x for x in items if not x.get("skip")]
        prev_end = 0.0
        for k, it in enumerate(spoken):
            if job.cancel:
                job.status = "cancelled"
                return
            nxt = spoken[k + 1]["start"] if k + 1 < len(spoken) else float("inf")
            start = max(it["start"], prev_end + 0.05)
            a, w = gen(it["text"], speed)
            dur, factor = len(a) / SR, 1.0
            room = max(it["end"] - start, 0.3)
            if use_speed and dur > room * 1.02:
                factor = min(dur / room, max_up)
                a, w = gen(it["text"], speed * factor)
                dur = len(a) / SR
            end = start + dur
            limit = nxt if use_gaps else it["end"]
            late = start - it["start"]
            over = end - limit
            if late >= 0.3 or over > 0.05:
                status = "late"
            elif end > it["end"] + 0.05:
                status = "gap"
            elif factor > 1.0:
                status = "sped"
            else:
                status = "ok"
            it.update(new_start=round(start, 3), new_end=round(end, 3), status=status,
                      factor=round(factor, 2), delay=round(max(late, over, 0), 2),
                      words=[dict(x, s=None if x["s"] is None else x["s"] + start,
                                  e=None if x["e"] is None else x["e"] + start) for x in w] if w else None)
            it["_audio"] = a
            prev_end = end
            job.i += 1
            job.audio_time += dur
            job.chars += len(it["text"])
        for it in spoken:  # timeline positions used by the player
            it["orig_start"], it["orig_end"] = it["start"], it["end"]
            it["start"], it["end"] = it["new_start"], it["new_end"]

    # export ---------------------------------------------------------------
    def _export(self, job, track, items, req):
        folder, out = job.folder, req.get("output", "all")
        wav = folder / "voice.wav"
        sf.write(wav, track, SR)
        job.files["wav"] = wav.name
        if req["mode"] == "plain" and out == "mp3":
            mp3 = folder / "voice.mp3"
            ffmpeg(["-i", str(wav), "-codec:a", "libmp3lame", "-q:a", "2", str(mp3)])
            job.files["mp3"] = mp3.name
        if req["mode"] == "srt":
            lines = []
            for n, x in enumerate(items, 1):
                s, e = (x["start"], x["end"])
                lines += [str(n), f"{fmt_srt_time(s)} --> {fmt_srt_time(e)}", x.get("display") or x["text"], ""]
            srt = folder / "voice-retimed.srt"
            srt.write_text("\n".join(lines), encoding="utf-8")
            if out in ("all", "srt"):
                job.files["srt"] = srt.name
            video = req.get("video_path")
            if video:
                mp4 = folder / "video-dubbed.mp4"
                mix_video(Path(video), wav, mp4, req.get("orig", "lower"))
                job.media = mp4.name
                if out in ("all", "mp4"):
                    job.files["mp4"] = mp4.name
        if not job.media:
            job.media = wav.name


# ---------------------------------------------------------------- ffmpeg

def ffmpeg(args):
    subprocess.run([str(FFMPEG), "-hide_banner", "-loglevel", "error", "-y", *args], check=True,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def probe(path: Path) -> dict:
    r = subprocess.run([str(FFPROBE), "-v", "error", "-show_entries", "format=duration:stream=codec_type",
                        "-of", "json", str(path)], capture_output=True, text=True, check=True,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    import json
    d = json.loads(r.stdout)
    return {"duration": float(d.get("format", {}).get("duration", 0) or 0),
            "has_audio": any(s.get("codec_type") == "audio" for s in d.get("streams", []))}


def mix_video(video: Path, voice: Path, out: Path, orig: str):
    info = probe(video)
    if orig == "mute" or not info["has_audio"]:
        args = ["-i", str(video), "-i", str(voice), "-map", "0:v:0", "-map", "1:a:0"]
    else:
        vol = 0.2 if orig == "lower" else 1.0
        args = ["-i", str(video), "-i", str(voice), "-filter_complex",
                f"[0:a]volume={vol}[o];[o][1:a]amix=inputs=2:duration=first:normalize=0[a]",
                "-map", "0:v:0", "-map", "[a]"]
    ffmpeg(args + ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)])
