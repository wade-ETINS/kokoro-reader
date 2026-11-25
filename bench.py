"""Kokoro-82M benchmark: one ~30 s Instagram voiceover, three voices, CPU only.

Usage: .venv\\Scripts\\python.exe bench.py
Writes out\\<voice>.wav and prints load time, generation time and real-time factor.
"""
import os
import time
from pathlib import Path

import truststore

truststore.inject_into_ssl()  # use the Windows certificate store for downloads

import numpy as np  # noqa: E402
import soundfile as sf

# espeak-ng handles English words outside Kokoro's dictionary.
ESPEAK = r"C:\Program Files\eSpeak NG"
os.environ.setdefault("PHONEMIZER_ESPEAK_LIBRARY", os.path.join(ESPEAK, "libespeak-ng.dll"))
os.environ.setdefault("PHONEMIZER_ESPEAK_PATH", os.path.join(ESPEAK, "espeak-ng.exe"))

from kokoro import KPipeline  # noqa: E402

SCRIPT = (
    "Your city only fixes what someone reports. "
    "The pothole on your street, the mould in the hallway, the smell from the storm drain. "
    "Nobody at city hall is walking past your building every morning. "
    "That is what three one one is for. "
    "It takes two minutes, it is free, and it creates a record that someone has to answer. "
    "Public health is not decided at the hospital. "
    "It is decided on your street, by the people who bother to call. "
    "So next time you walk past it, report it."
)
VOICES = ["af_heart", "af_bella", "am_michael"]
SR = 24000

out = Path(__file__).parent / "out"
out.mkdir(exist_ok=True)

t0 = time.perf_counter()
pipe = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")  # American English
print(f"model load: {time.perf_counter() - t0:.1f}s  ({len(SCRIPT.split())} words)")

for v in VOICES:
    t = time.perf_counter()
    chunks = [audio for _, _, audio in pipe(SCRIPT, voice=v, speed=1.0)]
    gen = time.perf_counter() - t
    wav = np.concatenate([c.numpy() if hasattr(c, "numpy") else c for c in chunks])
    dur = len(wav) / SR
    sf.write(out / f"{v}.wav", wav, SR)
    print(f"{v:11s} audio {dur:5.1f}s  generated in {gen:5.1f}s  -> {dur / gen:4.1f}x real time")
