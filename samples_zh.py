"""Kokoro-82M v1.1-zh samples: Traditional Chinese (Taiwan wording) with English terms.

Usage: .venv\\Scripts\\python.exe samples_zh.py
Writes out_zh\\<voice>.wav and prints generation speed per voice.
"""
import os
import re
import time
from pathlib import Path

import truststore

truststore.inject_into_ssl()  # use the Windows certificate store for downloads

ESPEAK = r"C:\Program Files\eSpeak NG"
os.environ.setdefault("PHONEMIZER_ESPEAK_LIBRARY", os.path.join(ESPEAK, "libespeak-ng.dll"))
os.environ.setdefault("PHONEMIZER_ESPEAK_PATH", os.path.join(ESPEAK, "espeak-ng.exe"))

import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
from kokoro import KModel, KPipeline  # noqa: E402

REPO = "hexgrad/Kokoro-82M-v1.1-zh"
SR = 24000
GAP = np.zeros(int(0.25 * SR), dtype=np.float32)  # pause between sentences

TEXT = (
    "歡迎使用 FLIR Thermal Studio。"
    "這套軟體可以幫你一次管理上千張熱影像和影片。"
    "請先用傳輸線把相機連接到電腦，再點選右上角的「從相機匯入」。"
    "完成報告之後，記得按下儲存，也可以匯出成 PDF 檔案。"
)
VOICES = ["zf_001", "zf_002", "zf_017", "zm_009", "zm_010", "zm_011"]

en_pipe = KPipeline(lang_code="a", repo_id=REPO, model=False)


def en_callable(word):
    return next(en_pipe(word)).phonemes


def speed_callable(n_phonemes):
    # From the model's own sample script: slow long sentences so they don't rush.
    speed = 0.8
    if n_phonemes <= 83:
        speed = 1
    elif n_phonemes < 183:
        speed = 1 - (n_phonemes - 83) / 500
    return speed * 1.1


t0 = time.perf_counter()
model = KModel(repo_id=REPO).eval()
zh = KPipeline(lang_code="z", repo_id=REPO, model=model, en_callable=en_callable)
print(f"model load: {time.perf_counter() - t0:.1f}s  ({len(TEXT)} characters)")

sentences = [s for s in re.split(r"(?<=[。！？])", TEXT) if s.strip()]
out = Path(__file__).parent / "out_zh"
out.mkdir(exist_ok=True)

for v in VOICES:
    t = time.perf_counter()
    parts = []
    for s in sentences:
        for r in zh(s, voice=v, speed=speed_callable):
            parts += [r.audio.numpy(), GAP]
    gen = time.perf_counter() - t
    wav = np.concatenate(parts)
    dur = len(wav) / SR
    sf.write(out / f"{v}.wav", wav, SR)
    print(f"{v}  audio {dur:5.1f}s  generated in {gen:4.1f}s  -> {dur / gen:4.1f}x real time")
