"""Kokoro Reader launcher for the installed app (run with pythonw.exe, no console window).

- Uses the bundled models only (offline).
- Keeps generated files in %LOCALAPPDATA%\\KokoroReader\\work (macOS: ~/Library/Application Support/
  KokoroReader/work) and a log beside it.
- If Kokoro Reader is already running, just opens the browser to it.
- Stops on "Quit app", or about 5 minutes after the last browser tab closes.
"""
import json
import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if sys.platform == "darwin":  # macOS: ~/Library/Application Support/KokoroReader
    DATA = Path.home() / "Library" / "Application Support" / "KokoroReader"
else:
    DATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "KokoroReader"
DATA.mkdir(parents=True, exist_ok=True)

log = open(DATA / "kokoro-reader.log", "a", encoding="utf-8", buffering=1)
sys.stdout = sys.stderr = log
print(f"\n=== start {time.strftime('%Y-%m-%d %H:%M:%S')} ===")

os.environ["HF_HOME"] = str(ROOT / "models")
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["KOKORO_READER_WORK"] = str(DATA / "work")
os.environ["KOKORO_READER_NO_BROWSER"] = "1"
os.environ["KOKORO_READER_AUTOQUIT"] = "1"


def is_ours(port):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ping", timeout=1.5) as r:
            return json.loads(r.read()).get("app") == "kokoro-reader"
    except Exception:
        return False


def free(port):
    with socket.socket() as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


for port in range(7860, 7880):
    if is_ours(port):
        webbrowser.open(f"http://127.0.0.1:{port}")
        sys.exit(0)
    if free(port):
        break
else:
    sys.exit("No free port between 7860 and 7879")

os.environ["KOKORO_READER_PORT"] = str(port)


def open_when_ready():
    for _ in range(360):  # up to 3 min: the first start on a Mac also compiles Python files
        if is_ours(port):
            webbrowser.open(f"http://127.0.0.1:{port}")
            return
        time.sleep(0.5)


threading.Thread(target=open_when_ready, daemon=True).start()
sys.path.insert(0, str(ROOT / "app"))
import server  # noqa: E402

server.main()
