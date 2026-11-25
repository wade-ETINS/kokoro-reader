"""Capture manual screenshots of Kokoro Reader with headless Edge over CDP (stdlib only)."""
import base64, json, os, socket, struct, subprocess, sys, time, urllib.request
from pathlib import Path

OUT = Path(r"C:\ClaudeCode\kokoro-tts\docs\manual\img")
OUT.mkdir(parents=True, exist_ok=True)
APP = "http://127.0.0.1:7860/"
FLIR, CLIP = "1ec616b2d8ae", "102360a195c5"
TXT = r"C:\ClaudeCode\kokoro-tts\docs\manual\sample.txt"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PORT = 9333
SCR = Path(__file__).parent
W, H = 1360, 900


class CDP:
    def __init__(self, ws_url):
        host, path = ws_url[len("ws://"):].split("/", 1)
        h, p = host.split(":")
        self.s = socket.create_connection((h, int(p)))
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET /{path} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.s.recv(4096)
        self.rest = buf.split(b"\r\n\r\n", 1)[1]
        self.n = 0

    def _read(self, k):
        while len(self.rest) < k:
            self.rest += self.s.recv(1 << 20)
        d, self.rest = self.rest[:k], self.rest[k:]
        return d

    def _frame(self):
        b1, b2 = self._read(2)
        ln = b2 & 0x7F
        if ln == 126: ln = struct.unpack(">H", self._read(2))[0]
        elif ln == 127: ln = struct.unpack(">Q", self._read(8))[0]
        return b1 & 0x0F, self._read(ln)

    def call(self, method, **params):
        self.n += 1
        msg = json.dumps({"id": self.n, "method": method, "params": params}).encode()
        mask = os.urandom(4)
        hdr = bytes([0x81])
        L = len(msg)
        hdr += bytes([0x80 | L]) if L < 126 else (bytes([0x80 | 126]) + struct.pack(">H", L) if L < 65536 else bytes([0x80 | 127]) + struct.pack(">Q", L))
        self.s.sendall(hdr + mask + bytes(c ^ mask[i % 4] for i, c in enumerate(msg)))
        data = b""
        while True:
            op, part = self._frame()
            data += part
            if op == 0 and not part: continue
            try:
                m = json.loads(data)
            except ValueError:
                continue
            data = b""
            if m.get("id") == self.n:
                if "error" in m: raise RuntimeError(f"{method}: {m['error']}")
                return m.get("result", {})


def js(c, expr):
    r = c.call("Runtime.evaluate", expression=f"(async()=>{{{expr}}})()", awaitPromise=True, returnByValue=True)
    if r.get("exceptionDetails"):
        raise RuntimeError(r["exceptionDetails"].get("exception", {}).get("description", r["exceptionDetails"]))
    return r.get("result", {}).get("value")


def shot(c, name, sel=None, pad=0, scroll_top=True, clipH=None):
    time.sleep(0.6)
    if sel:
        box = js(c, f"""const e=document.querySelector({json.dumps(sel)}); {'e.scrollIntoView({block:"start"});' if scroll_top else ''}
            await new Promise(r=>setTimeout(r,250)); const b=e.getBoundingClientRect();
            return {{x:b.left+scrollX,y:b.top+scrollY,w:b.width,h:b.height}};""")
        clip = dict(x=max(0, box["x"] - pad), y=max(0, box["y"] - pad), width=box["w"] + 2 * pad,
                    height=min(box["h"] + 2 * pad, clipH or 99999), scale=1)
        r = c.call("Page.captureScreenshot", format="png", clip=clip, captureBeyondViewport=True)
    else:
        r = c.call("Page.captureScreenshot", format="png")
    (OUT / f"{name}.png").write_bytes(base64.b64decode(r["data"]))
    print("  saved", name)


def wait(c, cond, t=120):
    t0 = time.time()
    while time.time() - t0 < t:
        if js(c, f"return !!({cond})"): return True
        time.sleep(0.5)
    print("STATE", js(c, "return {mode:S.mode,step:S.step,P:!!S.P,rows:document.querySelectorAll('#rv tr').length,msg:document.getElementById('msg').textContent}"))
    raise TimeoutError(cond)


def open_project(c, pid, lang):
    c.call("Page.navigate", url=APP)
    time.sleep(1)
    js(c, f"localStorage.setItem('kr-pid','{pid}'); localStorage.setItem('kr-ui','{lang}'); localStorage.removeItem('kr-job-{pid}');")
    c.call("Page.reload")
    wait(c, "document.querySelector('#welcome .btn.primary')")
    js(c, "window.confirm=()=>true; window.alert=()=>{};")


def main():
    prof = SCR / "edge-prof"
    edge = subprocess.Popen([EDGE, "--headless=new", f"--remote-debugging-port={PORT}", f"--user-data-dir={prof}",
                             f"--window-size={W},{H}", "--hide-scrollbars", "--mute-audio", "--no-first-run", "about:blank"])
    try:
        for _ in range(40):
            try:
                tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json").read())
                ws = next(t["webSocketDebuggerUrl"] for t in tabs if t["type"] == "page")
                break
            except Exception:
                time.sleep(0.5)
        c = CDP(ws)
        c.call("Page.enable"); c.call("DOM.enable")
        c.call("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": "light"}])
        c.call("Emulation.setDeviceMetricsOverride", width=W, height=H, deviceScaleFactor=1, mobile=False)
        langs = sys.argv[1:] or ["en", "zh"]
        for lang in langs:
            print("==", lang)
            # welcome
            open_project(c, FLIR, lang)
            shot(c, f"{lang}-01-welcome", "#config", 70)
            # guide dialog
            js(c, "document.getElementById('welcome-guide').click();")
            shot(c, f"{lang}-02-guide")
            js(c, "document.getElementById('guide').close();")
            # project: FLIR
            js(c, "document.querySelector('#welcome .btn.primary').click();")
            wait(c, "document.querySelectorAll('#rv tr').length > 5")
            js(c, "go(1, true);")
            shot(c, f"{lang}-03-step1", "#config", 8)
            js(c, "go(2, true);")
            shot(c, f"{lang}-04-step2", "#config", 8)
            js(c, "go(3, true); window.scrollTo(0,0);")
            shot(c, f"{lang}-05-step3", "#config", 8)
            js(c, "document.getElementById('work').scrollIntoView();")
            shot(c, f"{lang}-06-review", "#work", 8, clipH=760)
            # right-click glossary popup on a translated cell
            js(c, """const cell=[...document.querySelectorAll('#rv [data-ed="tr"]')].find(e=>e.textContent.length>8);
                cell.scrollIntoView({block:'center'}); const tn=[...cell.childNodes].find(n=>n.nodeType===3&&n.textContent.length>4)||cell.firstChild;
                const r=document.createRange(); r.setStart(tn,0); r.setEnd(tn,Math.min(4,tn.textContent.length));
                getSelection().removeAllRanges(); getSelection().addRange(r);
                const b=r.getBoundingClientRect();
                cell.dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,clientX:b.left+10,clientY:b.bottom}));""")
            shot(c, f"{lang}-07-popup")
            js(c, "document.getElementById('pop').hidden=true; getSelection().removeAllRanges();")
            js(c, "openGloss();")
            shot(c, f"{lang}-08-glossary")
            js(c, "document.getElementById('gloss').close();")
            # voice on the short clip
            open_project(c, CLIP, lang)
            js(c, "document.querySelector('#welcome .btn.primary').click();")
            wait(c, "document.querySelectorAll('#rv tr').length > 3")
            js(c, "go(4); window.scrollTo(0,0);")
            shot(c, f"{lang}-09-step4", "#config", 8)
            js(c, "document.getElementById('gen').click();")
            wait(c, "S.done && S.jobId", 400)
            time.sleep(1)
            js(c, "go(4, true); window.scrollTo(0,0);")
            shot(c, f"{lang}-10-step4-done", "#config", 8)
            js(c, "go(5, true); window.scrollTo(0,0);")
            shot(c, f"{lang}-11-step5", "#config", 8)
            js(c, "showTab('play'); document.getElementById('work').scrollIntoView();")
            shot(c, f"{lang}-12-play", "#work", 8, clipH=760)
            # plain text mode
            c.call("Page.navigate", url=APP); time.sleep(1)
            js(c, f"localStorage.removeItem('kr-pid'); localStorage.setItem('kr-ui','{lang}');")
            c.call("Page.reload"); time.sleep(2)
            doc = c.call("DOM.getDocument")
            nid = c.call("DOM.querySelector", nodeId=doc["root"]["nodeId"], selector="#file")["nodeId"]
            c.call("DOM.setFileInputFiles", nodeId=nid, files=[TXT])
            wait(c, "S.mode==='plain'")
            time.sleep(1)
            shot(c, f"{lang}-13-text")
    finally:
        edge.terminate()


main()

