"""Kokoro Reader: local web app. Run with .venv\\Scripts\\python.exe app\\server.py

Binds to 127.0.0.1 only; nothing is reachable from other computers.
"""
from __future__ import annotations

import os
import sys
import threading
import time
import uuid
import webbrowser
from pathlib import Path
from urllib.parse import quote

try:  # use the Windows certificate store for model downloads
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

from flask import Flask, abort, jsonify, request, send_from_directory

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine as E  # noqa: E402
import pipeline as P  # noqa: E402

HERE = Path(__file__).resolve().parent
WORK = Path(os.environ.get("KOKORO_READER_WORK", HERE.parent / "work"))
UPLOADS, JOBS = WORK / "uploads", WORK / "jobs"
for d in (UPLOADS, JOBS):
    d.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder=str(HERE / "static"), static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 ** 3  # videos up to 4 GB

ENGINE = E.Engine()
GLOSSARY = P.Glossary(WORK / "glossary.json", HERE / "glossary-starter.txt")
PIPE = P.Pipeline(WORK, GLOSSARY)
VIDEOS: dict[str, dict] = {}
for _p in PIPE.projects.values():  # videos of saved projects stay playable after a restart
    _v = _p.d.get("video")
    if _v and _v.get("id") and Path(_v["path"]).exists():
        VIDEOS[_v["id"]] = {k: _v[k] for k in ("path", "name", "duration", "has_audio") if k in _v}
JOB_TABLE: dict[str, E.Job] = {}


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


LAST_SEEN = [time.time()]


@app.get("/api/ping")
def ping():
    LAST_SEEN[0] = time.time()
    return jsonify(app="kokoro-reader")


@app.post("/api/quit")
def quit_app():
    threading.Timer(0.3, lambda: os._exit(0)).start()
    return jsonify(ok=True)


def _busy():
    return any(j.status in ("queued", "loading", "running", "exporting") for j in JOB_TABLE.values())


def _pipe_busy():
    return any(p.thread and p.thread.is_alive() for p in PIPE.projects.values())


def watchdog(idle_seconds=300):
    """Stop the app when no page has checked in for a while and nothing is generating."""
    while True:
        time.sleep(30)
        if time.time() - LAST_SEEN[0] > idle_seconds and not _busy() and not _pipe_busy():
            os._exit(0)


@app.get("/api/voices")
def voices():
    return jsonify(E.VOICES)


@app.post("/api/parse")
def parse():
    d = request.get_json(force=True)
    raw, kind, lang = d.get("text", ""), d.get("kind", "plain"), d.get("lang", "en-us")
    clean = d.get("clean", True)
    if kind == "srt":
        items = E.parse_srt(raw)
        if not items:
            return jsonify(error="no_cues"), 400
    else:
        items = E.split_sentences(raw)
        if not items:
            return jsonify(error="empty"), 400
    for it in items:
        it["original"] = it["text"]
        it["display"] = it["text"]
        if clean:
            it["text"] = E.clean_text(it["text"], lang)
            it["display"] = E.clean_text(it["original"], lang, speak=False)
        it["changed"] = it["text"] != it["original"]
        it["skip"] = kind == "srt" and E.auto_skip(it["original"])
    return jsonify(items=items)


@app.post("/api/video")
def upload_video():
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify(error="no_file"), 400
    vid = uuid.uuid4().hex[:12]
    ext = Path(f.filename).suffix.lower()[:6] or ".mp4"
    path = UPLOADS / f"{vid}{ext}"
    f.save(path)
    try:
        info = E.probe(path)
    except Exception:
        path.unlink(missing_ok=True)
        return jsonify(error="bad_video"), 400
    VIDEOS[vid] = {"path": str(path), "name": f.filename, **info}
    return jsonify(id=vid, name=f.filename, duration=info["duration"], has_audio=info["has_audio"])


@app.post("/api/generate")
def generate():
    req = request.get_json(force=True)
    if req.get("lang") not in E.VOICES or req.get("voice") not in E.VOICES[req["lang"]]:
        return jsonify(error="bad_voice"), 400
    if req.get("blend") and req["blend"] not in E.VOICES[req["lang"]]:
        return jsonify(error="bad_voice"), 400
    if not req.get("items"):
        return jsonify(error="empty"), 400
    if _busy():
        return jsonify(error="busy"), 409
    if req.get("clean_items"):
        for it in req["items"]:
            it["text"] = E.clean_text(it["text"], req["lang"])
    jid = uuid.uuid4().hex[:12]
    folder = JOBS / jid
    folder.mkdir()
    job = E.Job(id=jid, folder=folder)
    v = VIDEOS.get(req.get("video_id") or "")
    if req.get("mode") == "srt" and v:
        req["video_path"] = v["path"]
        job.duration = v["duration"]
    JOB_TABLE[jid] = job
    threading.Thread(target=ENGINE.run, args=(job, req), daemon=True).start()
    return jsonify(id=jid)


@app.get("/api/job/<jid>")
def job_state(jid):
    job = JOB_TABLE.get(jid)
    if not job:
        abort(404)
    return jsonify(job.snapshot())


@app.post("/api/job/<jid>/cancel")
def cancel(jid):
    job = JOB_TABLE.get(jid)
    if job:
        job.cancel = True
    return jsonify(ok=True)


@app.get("/files/<jid>/<name>")
def files(jid, name):
    job = JOB_TABLE.get(jid)
    allowed = set(job.files.values()) | {job.media} if job else set()
    if name not in allowed:
        abort(404)
    as_dl = request.args.get("dl") == "1"
    return send_from_directory(job.folder, name, as_attachment=as_dl,
                               download_name=_safe_name(request.args.get("n")) or name)


# ---------------------------------------------------------------- video -> subtitles projects

def _safe_name(n):
    if not n:
        return None
    n = "".join(c for c in n if c not in '<>:"/\\|?*').strip(" .")
    return n[:150] or None


def _project(pid):
    p = PIPE.projects.get(pid)
    if not p:
        abort(404)
    return p


@app.get("/video/<vid>")
def video_file(vid):
    v = VIDEOS.get(vid)
    if not v:
        abort(404)
    return send_from_directory(Path(v["path"]).parent, Path(v["path"]).name, conditional=True)


@app.post("/api/project")
def project_new():
    d = request.get_json(force=True)
    target = d.get("target", "auto")
    if d.get("srt"):
        cues = E.parse_srt(d["srt"])
        if not cues:
            return jsonify(error="no_cues"), 400
        v = VIDEOS.get(d.get("video_id") or "")
        p = PIPE.from_srt(d.get("name") or "subtitles.srt", cues, target,
                          dict(v, id=d["video_id"]) if v else None)
    else:
        v = VIDEOS.get(d.get("video_id") or "")
        if not v:
            return jsonify(error="no_video"), 400
        p = PIPE.from_video(dict(v, id=d["video_id"]), d.get("spoken", "auto"), target,
                            float(d.get("chunk_min", 5)), d.get("accuracy", "best"))
    return jsonify(id=p.id)


@app.get("/api/project/<pid>")
def project_get(pid):
    return jsonify(_project(pid).snapshot(request.args.get("rev", type=int)))


@app.post("/api/project/<pid>/stop")
def project_stop(pid):
    PIPE.stop(_project(pid))
    return jsonify(ok=True)


@app.post("/api/project/<pid>/resume")
def project_resume(pid):
    p = _project(pid)
    if not p.d.get("done"):
        PIPE.start(p)
    return jsonify(ok=True)


@app.post("/api/project/<pid>/video")
def project_video(pid):
    p = _project(pid)
    vid = request.get_json(force=True).get("video_id") or ""
    v = VIDEOS.get(vid)
    if not v:
        return jsonify(error="no_video"), 400
    with p.lock:
        p.d["video"] = dict(v, id=vid)
        p.d["duration"] = v["duration"]
        p.touch()
        p.save()
    return jsonify(ok=True)


@app.post("/api/project/<pid>/lines")
def project_lines(pid):
    PIPE.update_lines(_project(pid), request.get_json(force=True).get("changes", []))
    return jsonify(ok=True)


@app.post("/api/project/<pid>/join")
def project_join(pid):
    PIPE.join(_project(pid), int(request.get_json(force=True)["id"]))
    return jsonify(ok=True)


@app.post("/api/project/<pid>/retranslate")
def project_retranslate(pid):
    d = request.get_json(force=True)
    ids = PIPE.retranslate(_project(pid), ids=d.get("ids"), chunk=d.get("chunk"), terms=d.get("terms"),
                           all_lines=bool(d.get("all")), keep_edits=d.get("keep_edits", True))
    return jsonify(ok=True, n=len(ids))


@app.post("/api/project/<pid>/target")
def project_target(pid):
    p = _project(pid)
    if p.thread and p.thread.is_alive():
        return jsonify(error="busy"), 409
    PIPE.set_target(p, request.get_json(force=True).get("target", "auto"))
    return jsonify(ok=True)


@app.get("/api/project/<pid>/srt/<which>")
def project_srt(pid, which):
    p = _project(pid)
    if which not in ("src", "tr", "bi"):
        abort(404)
    body = P.srt_text([ln for ln in p.d["lines"] if not ln.get("skip")], which)
    name = _safe_name(request.args.get("n")) or f"subtitles.{which}.srt"
    return app.response_class(body.encode("utf-8-sig"), mimetype="application/x-subrip",
                              headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(name)}"})


@app.get("/api/glossary")
def glossary_get():
    return jsonify(GLOSSARY.load())


@app.post("/api/glossary")
def glossary_set():
    return jsonify(GLOSSARY.save(request.get_json(force=True).get("items", [])))


@app.get("/api/glossary.txt")
def glossary_export():
    body = "# Kokoro Reader glossary: 'English = 中文', or a term alone to keep it as is\n" + "\n".join(
        f"{g['src']} = {g['dst']}" if g["dst"] else g["src"] for g in GLOSSARY.load()) + "\n"
    return app.response_class(body.encode("utf-8-sig"), mimetype="text/plain",
                              headers={"Content-Disposition": "attachment; filename=glossary.txt"})


@app.post("/api/glossary.txt")
def glossary_import():
    items = GLOSSARY.load()
    for line in request.get_data(as_text=True).splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            src, _, dst = line.partition("=")
            items.append({"src": src.strip(), "dst": dst.strip(), "where": "import"})
    return jsonify(GLOSSARY.save(items))


def main():
    port = int(os.environ.get("KOKORO_READER_PORT", "7860"))
    url = f"http://127.0.0.1:{port}"
    if "--no-browser" not in sys.argv and os.environ.get("KOKORO_READER_NO_BROWSER") != "1":
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    if os.environ.get("KOKORO_READER_AUTOQUIT") == "1":
        threading.Thread(target=watchdog, daemon=True).start()
    print(f"Kokoro Reader running at {url}")
    app.run(host="127.0.0.1", port=port, threaded=True)


if __name__ == "__main__":
    main()
