"""Transcribe a video/audio file to SRT with faster-whisper (local, offline after the first model download).

Usage:  .venv\\Scripts\\python.exe transcribe.py <media> [--model large-v3-turbo] [--lang en|zh|auto] [--out file.srt]
Lines are rebuilt from word timestamps: split at sentence ends and pauses, at most ~2 subtitle
lines (84 chars, or 40 CJK chars) and 7 seconds each, which suits Kokoro Reader's SRT fitting.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import truststore

truststore.inject_into_ssl()
from faster_whisper import WhisperModel  # noqa: E402

MAX_SEC = 7.0
MAX_CHARS = 84
MAX_CJK = 40
PAUSE = 0.6
ENDS = (".", "?", "!", "。", "？", "！", "…")


def ts(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


FFMPEG = Path(__file__).resolve().parent / "tools" / "ffmpeg" / "ffmpeg.exe"


def load_audio(media):
    """Decode any audio/video to 16 kHz mono float32 with the bundled ffmpeg (avoids PyAV)."""
    import subprocess
    import numpy as np
    raw = subprocess.run([str(FFMPEG), "-nostdin", "-v", "error", "-i", str(media), "-vn", "-ac", "1",
                          "-ar", "16000", "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def is_cjk(text):
    return any("一" <= c <= "鿿" for c in text)


def group(words):
    """Words -> subtitle cues [(start, end, text)]."""
    cues, cur = [], []

    def text_of(ws):
        t = "".join(w.word for w in ws).strip()
        return t

    def flush():
        if cur:
            cues.append((cur[0].start, cur[-1].end, text_of(cur)))
            cur.clear()

    for i, w in enumerate(words):
        if cur:
            gap = w.start - cur[-1].end
            t = text_of(cur + [w])
            limit = MAX_CJK if is_cjk(t) else MAX_CHARS
            if gap > PAUSE:
                flush()
            elif w.end - cur[0].start > MAX_SEC or len(t) > limit:
                # split at the last comma in the line if there is one, else here
                cut = max((k for k, x in enumerate(cur[:-1]) if x.word.strip().endswith((",", "，", "、", ";"))),
                          default=None)
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
        if t.endswith(ENDS) and (nxt is None or len(t) > 25 or nxt.start - w.end > 0.3):
            flush()
    flush()
    # merge short tails (< 1.2 s or < 12 chars) into the cue before when they belong to it
    out = []
    for s, e, t in cues:
        if out:
            ps, pe, pt = out[-1]
            short = (e - s < 1.2 or len(t) < 12) and not pt.endswith(ENDS)
            if short and s - pe < 0.4 and e - ps <= MAX_SEC + 2 and len(pt) + len(t) <= MAX_CHARS + 30:
                out[-1] = (ps, e, (pt + ("" if is_cjk(t) else " ") + t).strip())
                continue
        out.append((s, e, t))
    return out


def write_srt(out, cues):
    if any(is_cjk(t) for _, _, t in cues):          # Whisper writes Simplified; use Traditional (Taiwan)
        import opencc
        cc = opencc.OpenCC("s2tw")
        cues = [(s, e, cc.convert(t)) for s, e, t in cues]
    with open(out, "w", encoding="utf-8") as f:
        for n, (s, e, t) in enumerate(cues, 1):
            f.write(f"{n}\n{ts(s)} --> {ts(e)}\n{t}\n\n")
    print(f"{len(cues)} cues -> {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("media")
    ap.add_argument("--model", default="large-v3-turbo")
    ap.add_argument("--lang", default="auto")
    ap.add_argument("--out")
    ap.add_argument("--regroup", action="store_true", help="re-split saved words (<media>.words.json) only")
    a = ap.parse_args()
    media = Path(a.media)
    out = Path(a.out) if a.out else media.with_suffix(".srt")
    wjson = out.with_suffix(".words.json")
    if a.regroup:
        from types import SimpleNamespace
        words = [SimpleNamespace(**w) for w in json.loads(wjson.read_text(encoding="utf-8"))]
        write_srt(out, group(words))
        return

    t0 = time.time()
    model = WhisperModel(a.model, device="cpu", compute_type="int8", cpu_threads=os.cpu_count())
    load = time.time() - t0
    print(f"model {a.model} loaded in {load:.0f}s", flush=True)

    t1 = time.time()
    audio = load_audio(media)
    segs, info = model.transcribe(audio, language=None if a.lang == "auto" else a.lang,
                                  vad_filter=True, word_timestamps=True, beam_size=5,
                                  condition_on_previous_text=False)
    print(f"language {info.language} ({info.language_probability:.2f}), duration {info.duration:.0f}s", flush=True)
    words = []
    for s in segs:
        words.extend(s.words or [])
        pct = 100 * s.end / info.duration
        print(f"  {pct:5.1f}%  {ts(s.end)}  {time.time() - t1:6.0f}s elapsed", flush=True)
    wjson.write_text(json.dumps([{"start": w.start, "end": w.end, "word": w.word} for w in words]),
                     encoding="utf-8")
    write_srt(out, group(words))
    took = time.time() - t1
    print(f"transcribe {took:.0f}s for {info.duration:.0f}s audio = {info.duration / took:.2f}x real time")


if __name__ == "__main__":
    sys.exit(main())
