"""Build the macOS (Apple silicon) package of Kokoro Reader on Windows.

Run with the project's venv:  .venv\\Scripts\\python.exe build\\build_mac.py
Needs build\\dist\\KokoroReader (from build_dist.py, for the models) and the downloads in
build\\cache\\mac-dl + build\\cache\\mac-wheels (see MAC_WHEELS / DOWNLOADS below).

Output: build\\output\\KokoroReader-Setup-<ver>-macOS.zip, which holds a folder with
"Kokoro Reader.app", the manuals and README. Nothing is staged on disk: files go straight into
the zip with Unix permissions, so the app runs once unzipped on a Mac (Archive Utility keeps them).

Checks before writing: every Mach-O file is arm64 and carries a code signature (Apple silicon
refuses unsigned code), and every package's requirements are met under macOS markers.
"""
import io
import plistlib
import struct
import sys
import tarfile
import time
import zipfile
from pathlib import Path

from packaging.markers import default_environment
from packaging.metadata import Metadata
from packaging.utils import canonicalize_name

VERSION = "1.1.1"
PROJ = Path(__file__).resolve().parent.parent
CACHE = PROJ / "build" / "cache"
WIN_DIST = PROJ / "build" / "dist" / "KokoroReader"
WIN_SITE = PROJ / ".venv" / "Lib" / "site-packages"
OUT = PROJ / "build" / "output" / f"KokoroReader-Setup-{VERSION}-macOS.zip"
TOP = f"Kokoro Reader {VERSION}"
APP = f"{TOP}/Kokoro Reader.app/Contents"
RES = f"{APP}/Resources"
SITE = f"{RES}/python/lib/python3.12/site-packages"
PY_TGZ = CACHE / "mac-dl" / "cpython-3.12.16-mac-arm64.tar.gz"   # python-build-standalone 20261110
FFMPEG_ZIPS = [CACHE / "mac-dl" / "ffmpeg-mac-arm64.zip", CACHE / "mac-dl" / "ffprobe-mac-arm64.zip"]  # martin-riedl.de 9.1
WHEELS = CACHE / "mac-wheels"   # pip download --platform macosx_14_0_arm64 of the packages with native code
SKIP_WIN = {"win32_setctime", "pip"}  # Windows-only / not needed

entries = {}  # arcname -> (data bytes | Path, mode)


def add(arc, src, mode=None):
    assert arc not in entries, f"duplicate {arc}"
    entries[arc] = (src, mode)


def step(msg):
    print(f"\n== {msg}", flush=True)


# ------------------------------------------------------------------ Python
step("Python 3.12 for Apple silicon")
drop_dirs = ("python/include/", "python/share/", "python/lib/pkgconfig/", "python/lib/python3.12/test/",
             "python/lib/python3.12/idlelib/", "python/lib/python3.12/site-packages/",
             "python/lib/python3.12/config-3.12-darwin/")
with tarfile.open(PY_TGZ) as t:
    for m in t.getmembers():
        if not m.isfile() or m.name.startswith(drop_dirs) or "/__pycache__/" in m.name:
            continue
        if m.name.startswith("python/bin/") and m.name != "python/bin/python3.12":
            continue
        add(f"{RES}/{m.name}", t.extractfile(m).read(), m.mode)

# ------------------------------------------------------------------ packages
step("packages with native code (macOS arm64 wheels)")
native = set()
for whl in sorted(WHEELS.glob("*.whl")):
    native.add(canonicalize_name(whl.name.split("-")[0]))
    with zipfile.ZipFile(whl) as z:
        for i in z.infolist():
            name = i.filename
            if i.is_dir() or "__pycache__/" in name:
                continue
            parts = name.split("/")
            if parts[0].endswith(".data"):  # <dist>.data/purelib|platlib/... go to site-packages
                if parts[1] not in ("purelib", "platlib"):
                    continue
                name = "/".join(parts[2:])
            if name.startswith("torch/include/"):
                continue
            add(f"{SITE}/{name}", z.read(i), (i.external_attr >> 16) or None)
print(len(native), "wheels")

step("pure-Python packages (copied from the tested Windows venv)")
pure = 0
for info in sorted(WIN_SITE.glob("*.dist-info")):
    meta = Metadata.from_email((info / "METADATA").read_text(encoding="utf-8"), validate=False)
    key = canonicalize_name(meta.name)
    if key in native or key in SKIP_WIN:
        continue
    files = [line.rsplit(",", 2)[0] for line in (info / "RECORD").read_text(encoding="utf-8").splitlines() if line]
    for rel in files:
        if rel.startswith("..") or rel.endswith((".pyc", ".exe")) or "__pycache__" in rel:
            continue
        src = WIN_SITE / rel
        if src.is_file():
            assert not rel.endswith((".pyd", ".dll")), f"native file in 'pure' package {rel}"
            add(f"{SITE}/{rel}", src)
    pure += 1
print(pure, "packages")

# ------------------------------------------------------------------ app, tools, models
step("app, ffmpeg, models")
for f in sorted((PROJ / "app").rglob("*")):
    if f.is_file() and "__pycache__" not in f.parts:
        add(f"{RES}/app/{f.relative_to(PROJ / 'app').as_posix()}", f)
for zp in FFMPEG_ZIPS:
    with zipfile.ZipFile(zp) as z:
        for i in z.infolist():
            add(f"{RES}/tools/ffmpeg/{i.filename}", z.read(i), 0o755)
for f in sorted((WIN_DIST / "models").rglob("*")):
    if f.is_file():
        add(f"{RES}/models/{f.relative_to(WIN_DIST / 'models').as_posix()}", f)

# ------------------------------------------------------------------ bundle files
step("app bundle: Info.plist, launcher, icon")
add(f"{APP}/Info.plist", plistlib.dumps({
    "CFBundleName": "Kokoro Reader", "CFBundleDisplayName": "Kokoro Reader",
    "CFBundleIdentifier": "local.kokororeader.app", "CFBundleExecutable": "Kokoro Reader",
    "CFBundleIconFile": "KokoroReader", "CFBundlePackageType": "APPL",
    "CFBundleShortVersionString": VERSION, "CFBundleVersion": VERSION,
    "LSMinimumSystemVersion": "14.0", "LSUIElement": True,  # no Dock icon: the app lives in the browser
    "NSHighResolutionCapable": True,
}))
add(f"{APP}/MacOS/Kokoro Reader", (PROJ / "build" / "mac" / "launch.sh").read_bytes().replace(b"\r\n", b"\n"), 0o755)

src = (PROJ / "build" / "make_icon.py").read_text(encoding="utf-8")
ns = {"__file__": str(PROJ / "build" / "make_icon.py")}
exec(src.split("\nsizes = [")[0], ns)  # pixel() + render() only
icns = b""
for tag, size, ss in ((b"ic07", 128, 4), (b"ic08", 256, 4), (b"ic09", 512, 2)):
    png = ns["render"](size, ss)
    icns += tag + struct.pack(">I", 8 + len(png)) + png
add(f"{RES}/KokoroReader.icns", b"icns" + struct.pack(">I", 8 + len(icns)) + icns)

# ------------------------------------------------------------------ docs + licences
step("manuals, README, licences")
for pdf in sorted((PROJ / "docs" / "manual").glob("Kokoro Reader - *.pdf")):
    add(f"{TOP}/{pdf.name}", pdf)
add(f"{TOP}/README.txt", (PROJ / "build" / "mac" / "README-mac.txt").read_bytes().replace(b"\r\n", b"\n"))
lic = f"{RES}/licenses"
add(f"{lic}/python-LICENSE.txt", entries[f"{RES}/python/lib/python3.12/LICENSE.txt"][0])
for arc in [a for a in entries if a.startswith(SITE) and ".dist-info/" in a]:
    base = arc.rsplit("/", 1)[1]
    if base.upper().startswith(("LICENSE", "LICENCE", "COPYING", "NOTICE")):
        dist = arc[len(SITE) + 1:].split(".dist-info")[0].split("-")[0]
        name = f"{lic}/{dist}-{base}"
        if name not in entries:
            add(name, entries[arc][0])
add(f"{lic}/THIRD-PARTY.txt", (
    "Kokoro Reader for macOS bundles these third-party components:\n\n"
    "- Kokoro-82M and Kokoro-82M-v1.1-zh voice models (hexgrad), Apache-2.0: https://huggingface.co/hexgrad\n"
    "- FFmpeg 9.1 for macOS arm64, GPL build by Martin Riedl (https://ffmpeg.martin-riedl.de). Source: https://ffmpeg.org\n"
    "- eSpeak NG, inside the espeakng_loader package, GPL-3.0. Source: https://github.com/espeak-ng/espeak-ng\n"
    "- Whisper large-v3-turbo and small (OpenAI, MIT) in faster-whisper / CTranslate2 format (MIT)\n"
    "- Opus-MT en-zh and zh-en (Helsinki-NLP, CC-BY-4.0): https://huggingface.co/Helsinki-NLP\n"
    "- OpenCC (opencc-python-reimplemented), Apache-2.0\n"
    "- Python 3.12 (PSF licence; python-build-standalone build, https://github.com/astral-sh/python-build-standalone),\n"
    "  PyTorch (BSD), Flask (BSD), spaCy (MIT), misaki and kokoro (Apache-2.0),\n"
    "  and the other Python packages whose licence files are in this folder.\n").encode())


# ------------------------------------------------------------------ checks
def read(src):
    return src if isinstance(src, bytes) else src.read_bytes()


def macho_ok(data):
    """(is_macho, arm64, signed, is_executable) for a Mach-O file."""
    magic = data[:4]
    if magic == b"\xca\xfe\xba\xbe":  # fat: check the arm64 slice
        n = struct.unpack(">I", data[4:8])[0]
        for k in range(n):
            cpu, _, off, size, _ = struct.unpack(">iiIII", data[8 + 20 * k: 28 + 20 * k])
            if cpu == 0x0100000C:
                return (True,) + macho_ok(data[off: off + size])[1:]
        return True, False, False, False
    if magic != b"\xcf\xfa\xed\xfe":
        return False, False, False, False
    cpu, _, ftype, ncmds = struct.unpack("<iiII", data[4:20])
    off, signed = 32, False
    for _ in range(ncmds):
        cmd, size = struct.unpack("<II", data[off: off + 8])
        signed |= cmd == 0x1D  # LC_CODE_SIGNATURE
        off += size
    return True, cpu == 0x0100000C, signed, ftype == 2


step("checks")
bad, machos = [], 0
for arc, (src, mode) in entries.items():
    if arc.endswith((".so", ".dylib")) or "/bin/" in arc or "/tools/ffmpeg/" in arc or "/torch/lib/" in arc or mode and mode & 0o111:
        data = read(src)
        is_m, arm, signed, exe = macho_ok(data)
        if is_m:
            machos += 1
            if not (arm and signed):
                bad.append(f"{arc}: arm64={arm} signed={signed}")
            if exe:
                entries[arc] = (src, 0o755)
        elif data[:2] == b"#!":
            entries[arc] = (src, 0o755)
    elif arc.endswith(".exe") or arc.endswith((".pyd", ".dll")):
        bad.append(f"{arc}: Windows binary")
print(machos, "Mach-O files checked")

dists = {}
for arc in entries:
    if arc.startswith(SITE) and arc.endswith(".dist-info/METADATA"):
        m = Metadata.from_email(read(entries[arc][0]).decode("utf-8"), validate=False)
        dists[canonicalize_name(m.name)] = m
env = default_environment()
env.update(sys_platform="darwin", platform_system="Darwin", os_name="posix", platform_machine="arm64",
           python_version="3.12", python_full_version="3.12.16", implementation_name="cpython")
for name, m in dists.items():
    for req in m.requires_dist or []:
        if req.marker and not req.marker.evaluate({**env, "extra": ""}):
            continue
        dep = dists.get(canonicalize_name(req.name))
        if dep is None:
            bad.append(f"{name} needs {req} - missing")
        elif req.specifier and not req.specifier.contains(str(dep.version), prereleases=True):
            bad.append(f"{name} needs {req} - have {dep.version}")
print(len(dists), "packages, requirements checked for macOS")
for b in bad:
    print("  PROBLEM:", b)
if bad:
    sys.exit(f"{len(bad)} problems - not writing the zip")

# ------------------------------------------------------------------ write
step(f"write {OUT.name} ({len(entries)} files)")
OUT.parent.mkdir(parents=True, exist_ok=True)
t0 = time.time()
tmp = OUT.with_suffix(".part")
with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as z:
    dirs = set()
    for arc in sorted(entries):
        parts = arc.split("/")
        for k in range(1, len(parts)):
            d = "/".join(parts[:k]) + "/"
            if d not in dirs:
                dirs.add(d)
                zi = zipfile.ZipInfo(d, (2026, 11, 24, 0, 0, 0))
                zi.create_system, zi.external_attr = 3, (0o40755 << 16) | 0x10
                z.writestr(zi, b"")
        src, mode = entries[arc]
        zi = zipfile.ZipInfo(arc, (2026, 11, 24, 0, 0, 0))
        zi.create_system = 3  # Unix, so macOS honours the permission bits
        zi.external_attr = (0o100000 | (0o755 if mode and mode & 0o111 else 0o644)) << 16
        zi.compress_type = zipfile.ZIP_DEFLATED
        size = len(src) if isinstance(src, bytes) else src.stat().st_size
        with z.open(zi, "w", force_zip64=size > 2**31) as w:
            if isinstance(src, bytes):
                w.write(src)
            else:
                with open(src, "rb") as r:
                    while chunk := r.read(1 << 22):
                        w.write(chunk)
tmp.replace(OUT)
total = sum(len(s) if isinstance(s, bytes) else s.stat().st_size for s, _ in entries.values())
print(f"{OUT}  {OUT.stat().st_size / 2**20:.0f} MB (unzipped {total / 2**20:.0f} MB) in {(time.time() - t0) / 60:.1f} min")
