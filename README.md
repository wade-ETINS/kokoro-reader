# Kokoro Reader

**English** · [繁體中文](README.zh-TW.md)

Local text-to-speech, transcription, translation and video dubbing for ETINSTW. Everything runs on
your own Windows laptop: no internet connection is needed and no file is uploaded anywhere.

| You have | Kokoro Reader gives you |
|---|---|
| A text file (.txt / .md) | The text read aloud, with each word highlighted, saved as WAV or MP3 |
| A video (English or Chinese) | Subtitles of what is said, a translation you can review, and the video with a new voice in the other language |
| A subtitle file (.srt) + its video | The same, starting from your subtitles instead of transcribing |

---

## 1. Install

1. Run **KokoroReader-Setup-1.1.1.exe**. No administrator rights are needed; it installs for your
   Windows account only.
2. If Windows shows **"Windows protected your PC"**, click **More info → Run anyway**. The installer is
   not signed with a company certificate. Do this only for an installer you received from ETINSTW.
3. Pick English or 繁體中文 for the installer, optionally tick **Create a desktop shortcut**, and click
   **Install**. Installing takes a few minutes.

**Requirements:** Windows 10 or 11 (64-bit), about 5 GB free disk space, 16 GB RAM recommended
(8 GB works for text and short videos).

## 2. Start and stop

- Open **Kokoro Reader** from the Start menu. It opens in your web browser at `127.0.0.1`
  (your own computer).
- The full **Getting Started User Manual** (PDF with pictures, English and 繁體中文) is in the Start
  menu: *Kokoro Reader – Getting Started* and *Kokoro Reader – 使用入門*.
- **EN / 繁中** at the top right switches the interface language. **Getting started** opens the
  step-by-step manual inside the app.
- Click **Quit** when you finish. If you only close the tab, the app stops by itself about
  5 minutes later (never while it is still working).

## 3. Read a text file aloud

1. **Open file** → choose a `.txt` or `.md` file.
2. Choose the **Language**, **Voice** and, if you like, tone, speed and pauses.
   Hover over any dashed label for an explanation.
3. **Generate**. The first time after starting takes 30–40 seconds longer while the voice loads.
4. Press ▶ to listen; click any word to jump there. **Save audio** saves the WAV or MP3.

## 4. Translate and dub a video: steps 1 to 5

Click **Open video**. A step bar guides you: **1 Transcribe → 2 Translate → 3 Review → 4 Voice → 5 Export**.
Finished steps turn green ✓; locked steps 🔒 open as soon as the step before is ready.

| Step | What you do | Good to know |
|---|---|---|
| **1 Transcribe** | Keep *Spoken language* = Auto, *Chunk length* = About 5 min, *Accuracy* = Best. Click **Start transcribing**. | Takes about half the video's length (1-hour video ≈ 30 min). Keep the laptop plugged in. **Stop** / **Resume** continue where you left off, even after closing the app. |
| **2 Translate** | *Translate to* = Automatic (English → 繁體中文, Chinese → English), or Off to re-voice in the same language. | Each chunk is translated as soon as it is transcribed, so you can move on while the rest runs. |
| **3 Review** | In the **Review** table, check the translation chunk by chunk. Click a line to edit it, tick ✓ when it is right, or **Mark chunk reviewed**. | Start with the ⚠ lines. See *Review tips* below. |
| **4 Voice** | Pick the voice (defaults: `zm_009` Chinese, `af_bella` English) and click **Generate voice**. Watch the result in **Play & highlight**. | *Original audio* = **Replace**: the video's old sound is removed and only the new voice remains, so you never hear two voices. |
| **5 Export** | Tick what you need and click **Save selected**. | MP4 with the new voice, voice only (WAV), new subtitles re-timed to the voice, original subtitles, bilingual subtitles. Files are named after the video and go to Downloads. |

### Review tips

- **Edit:** click a line; **Enter** saves, **Esc** cancels. **Re-translate** asks the translator
  again; **Undo edit** restores the machine translation.
- **▶** plays that line in the video, so you can hear what was really said.
- **⚠ marks are hints, not errors:**
  - **⤓ join**: the sentence continues on the next line. Click to merge the two lines.
  - **long**: probably too long for its time slot; shorten the wording.
  - **unsure**: the transcriber was not sure of some words; listen and fix the original.
- Filters **⚠ Flagged** and **Not reviewed** show what is left; chunk buttons jump through the video.

### Glossary: teach it your words once

- Select a wrong word in the table, **right-click → Add to glossary**, type the right term, then
  **Add + fix this line** or **Add + re-translate all**.
- Leave the Chinese empty to keep a term in English (for example *FLIR Thermal Studio*).
  Glossary terms are underlined in green.
- The **Glossary** button lists all terms with where they came from and how often they are used.
  **Export .txt** / **Import .txt** share the list with colleagues.

### A video that already has subtitles

**Open file** → the `.srt` (step 1 is skipped), then **Open video** → the matching video, and
continue with steps 2–5.

## 5. Where things are kept

| What | Where |
|---|---|
| Work in progress, the glossary, a log file | `%LOCALAPPDATA%\KokoroReader` |
| Files you save | Your browser's Downloads folder |
| The program | `%LOCALAPPDATA%\Programs\Kokoro Reader` |

Uninstalling (Windows Settings → Apps) removes the program and the work folder. Export the glossary
first if you want to keep it.

## 6. Troubleshooting

| Problem | What to do |
|---|---|
| Nothing seems to happen after Start transcribing or Generate | The first load can take up to a minute. Watch the progress text. |
| The page says the app has stopped | Open Kokoro Reader from the Start menu again. **Continue: <video>** on the start screen brings back your last video. |
| The voice runs late on some lines | Shorten those translations in step 3, or raise *Max speed-up* in step 4. |
| Product names are translated wrongly | Add them to the glossary once; every later video uses them. |
| Chinese pronunciation of a word is odd | Known limit of the Chinese voice model; rephrase the line, or write the word in English if it is a brand name. |

## 7. What is inside (open-source, all running locally)

| Part | Used for | Licence |
|---|---|---|
| Kokoro-82M and Kokoro-82M-v1.1-zh | English and Chinese voices | Apache-2.0 |
| faster-whisper with Whisper large-v3-turbo / small | Transcription | MIT |
| Opus-MT (Helsinki-NLP) en↔zh via CTranslate2 | Translation | CC-BY-4.0 / MIT |
| OpenCC | Traditional characters with Taiwan wording | Apache-2.0 |
| FFmpeg (LGPL build) | Reading video, MP4 and MP3 output | LGPL |
| Python, PyTorch, Flask and other packages | Running the app | see `licenses` folder |

---

## For maintainers

**Run from source:** `Kokoro Reader.bat` (opens http://127.0.0.1:7860). Command-line tools:
`Video to SRT.bat` (drag videos onto it), `transcribe.py`, `translate_srt.py`.

| Path | Contents |
|---|---|
| `app/server.py` | Local web server (Flask, 127.0.0.1 only) and the API |
| `app/engine.py` | Kokoro voices, SRT timing fit, WAV / MP3 / MP4 export |
| `app/pipeline.py` | Chunked transcription, translation, glossary, review flags, resume |
| `app/static/` | The page: `index.html`, `style.css`, `app.js`, `i18n.js` (EN / 繁中), `guide.js` (manual), `icons.js` |
| `app/glossary-starter.txt` | Terms every new installation starts with |
| `models/opus-mt-*` | Translation models (CTranslate2 int8), made by `get_mt_models.py` |
| `tools/ffmpeg/` | FFmpeg 9.0 LGPL |
| `build/` | Installer build (below) |

**Build the installer:**

1. `.venv\Scripts\python.exe build\build_dist.py` assembles `build\dist\KokoroReader` (embedded
   Python, packages, app, ffmpeg, Kokoro voices, Whisper and Opus-MT models, licences).
2. `build\tools\innosetup\ISCC.exe build\KokoroReader.iss` writes
   `build\output\KokoroReader-Setup-<version>.exe`. Raise `AppVersion` in the `.iss` first.

The installed app runs `python\pythonw.exe app\launcher.pyw` with `HF_HUB_OFFLINE=1`, keeps work
files in `%LOCALAPPDATA%\KokoroReader`, and stops on **Quit** or about 5 minutes after the last tab
closes.

## Credits

Kokoro Reader uses open models and software from Kokoro (hexgrad), Whisper (OpenAI), Opus-MT
(Helsinki-NLP), FFmpeg, eSpeak NG and others. See [CREDITS.md](CREDITS.md) for the full list and licences.
