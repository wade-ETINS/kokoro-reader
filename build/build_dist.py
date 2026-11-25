"""Assemble a self-contained Kokoro Reader folder in build/dist/KokoroReader.

Run with the project's venv:  .venv\\Scripts\\python.exe build\\build_dist.py
Steps: embedded Python 3.12 + copied packages, the app, ffmpeg, both Kokoro models
(every voice), licence files. The result runs offline with python\\pythonw.exe app\\launcher.pyw.
"""
import os
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

import truststore

truststore.inject_into_ssl()

PROJ = Path(__file__).resolve().parent.parent
DIST = PROJ / "build" / "dist" / "KokoroReader"
CACHE = PROJ / "build" / "cache"
PYVER = "3.12.10"
EMBED = f"https://www.python.org/ftp/python/{PYVER}/python-{PYVER}-embed-amd64.zip"
SITE = PROJ / ".venv" / "Lib" / "site-packages"
REPOS = ["hexgrad/Kokoro-82M", "hexgrad/Kokoro-82M-v1.1-zh"]
WHISPER_REPOS = ["mobiuslabsgmbh/faster-whisper-large-v3-turbo", "Systran/faster-whisper-small"]

assert sys.version.startswith(PYVER), f"build with Python {PYVER} (the venv's version)"


def step(msg):
    print(f"\n== {msg}", flush=True)


def skip_site(dirpath, names):
    drop = {"__pycache__", "pip"}
    if Path(dirpath).name == "torch":
        drop |= {"include"}  # C++ headers; torch.testing is imported at startup, keep it
    out = [n for n in names if n in drop or n.startswith("pip-")]
    if Path(dirpath).name == "lib" and Path(dirpath).parent.name == "torch":
        out += [n for n in names if n.endswith(".lib")]
    return out


if DIST.exists():
    step("remove previous build")
    shutil.rmtree(DIST)
DIST.mkdir(parents=True)
CACHE.mkdir(parents=True, exist_ok=True)

step(f"embedded Python {PYVER}")
zpath = CACHE / Path(EMBED).name
if not zpath.exists():
    urllib.request.urlretrieve(EMBED, zpath)
with zipfile.ZipFile(zpath) as z:
    z.extractall(DIST / "python")
pth = next((DIST / "python").glob("python*._pth"))
pth.write_text(f"{pth.stem.replace('python', 'python')}.zip\n.\nLib\\site-packages\n..\\app\nimport site\n",
               encoding="ascii")

step("Python packages (from the tested venv)")
shutil.copytree(SITE, DIST / "python" / "Lib" / "site-packages", ignore=skip_site)

step("app, ffmpeg, docs")
shutil.copytree(PROJ / "app", DIST / "app", ignore=shutil.ignore_patterns("__pycache__"))
shutil.copytree(PROJ / "tools" / "ffmpeg", DIST / "tools" / "ffmpeg")
shutil.copy(PROJ / "build" / "README-colleagues.txt", DIST / "README.txt")
shutil.copy(PROJ / "README.md", DIST / "README.md")
shutil.copy(PROJ / "README.zh-TW.md", DIST / "README.zh-TW.md")
for pdf in (PROJ / "docs" / "manual").glob("Kokoro Reader - *.pdf"):  # Getting Started manuals (EN + 繁中)
    if "Mac" in pdf.name:  # the Mac install guides ship in the macOS zip only
        continue
    shutil.copy(pdf, DIST / pdf.name)

step("voice models (all voices)")
os.environ["HF_HOME"] = str(DIST / "models")
from huggingface_hub import snapshot_download  # noqa: E402

for repo in REPOS:
    path = snapshot_download(repo, allow_patterns=["*.json", "*.pth", "voices/*.pt"])
    print(repo, "->", path, sum(1 for _ in Path(path).rglob("*.pt")), "voices")

step("speech-to-text models (faster-whisper: Best = large-v3-turbo, Fast = small)")
for repo in WHISPER_REPOS:
    path = snapshot_download(repo)
    print(repo, "->", sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file()) // 2**20, "MB")

step("translation models (Opus-MT en<->zh, CTranslate2 int8)")
for pair in ("en-zh", "zh-en"):
    src = PROJ / "models" / f"opus-mt-{pair}"
    assert (src / "model.bin").exists(), f"run get_mt_models.py first ({src} missing)"
    shutil.copytree(src, DIST / "models" / f"opus-mt-{pair}")

step("licences")
lic = DIST / "licenses"
lic.mkdir()
shutil.copy(PROJ / "tools" / "ffmpeg" / "LICENSE.txt", lic / "ffmpeg-LGPL.txt")
for py_lic in (DIST / "python").glob("LICENSE*"):
    shutil.copy(py_lic, lic / f"python-{py_lic.name}")
for info in sorted((DIST / "python" / "Lib" / "site-packages").glob("*.dist-info")):
    files = [p for p in info.rglob("*") if p.is_file() and p.name.upper().startswith(("LICENSE", "LICENCE", "COPYING", "NOTICE"))]
    for f in files:
        shutil.copy(f, lic / f"{info.name.split('-')[0]}-{f.name}")
(lic / "THIRD-PARTY.txt").write_text(
    "Kokoro Reader bundles these third-party components:\n\n"
    "- Kokoro-82M and Kokoro-82M-v1.1-zh voice models (hexgrad), Apache-2.0: https://huggingface.co/hexgrad\n"
    "- FFmpeg 9.0 (LGPL build from https://github.com/FFmpeg-Builds/FFmpeg-Builds). Source: https://ffmpeg.org\n"
    "- eSpeak NG, inside the espeakng_loader package, GPL-3.0. Source: https://github.com/espeak-ng/espeak-ng\n"
    "- Whisper large-v3-turbo and small (OpenAI, MIT) in faster-whisper / CTranslate2 format (MIT)\n"
    "- Opus-MT en-zh and zh-en (Helsinki-NLP, CC-BY-4.0): https://huggingface.co/Helsinki-NLP\n"
    "- OpenCC (opencc-python-reimplemented), Apache-2.0\n"
    "- Python 3.12 (PSF licence), PyTorch (BSD), Flask (BSD), spaCy (MIT), misaki and kokoro (Apache-2.0),\n"
    "  and the other Python packages whose licence files are in this folder.\n",
    encoding="utf-8")

step("size")
total = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file())
for part in sorted(DIST.iterdir()):
    size = sum(f.stat().st_size for f in part.rglob("*") if f.is_file()) if part.is_dir() else part.stat().st_size
    print(f"  {part.name:12s} {size / 2**20:8.0f} MB")
print(f"  {'TOTAL':12s} {total / 2**20:8.0f} MB")
