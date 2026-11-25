"""Build the Kokoro Reader Getting Started manual (EN + 繁中) as HTML and PDF.

Run:  .venv\\Scripts\\python.exe docs\\manual\\make_manual.py
Screenshots come from docs\\manual\\img (en-*.png / zh-*.png). PDFs are printed with Microsoft Edge.
"""
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
VERSION = "1.1"
INSTALLER = "KokoroReader-Setup-1.1.1.exe"

CSS = """
@page { size: A4; margin: 16mm 15mm 16mm 15mm; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", "Microsoft JhengHei UI", "Microsoft JhengHei", sans-serif; color: #1d1d1b;
       font-size: 10.5pt; line-height: 1.55; margin: 0; background: #fff; }
.wrap { max-width: 180mm; margin: 0 auto; }
h1 { font-size: 26pt; margin: 0 0 4mm; letter-spacing: -0.5px; }
h2 { font-size: 16pt; margin: 0 0 3mm; padding-top: 1mm; break-before: page; color: #14365f; }
h2 .n { display: inline-block; min-width: 9mm; color: #2a7de1; }
h3 { font-size: 12pt; margin: 6mm 0 2mm; color: #14365f; break-after: avoid; }
p { margin: 0 0 2.5mm; }
ol, ul { margin: 0 0 3mm; padding-left: 6mm; }
li { margin: 0 0 1.2mm; }
b, strong { font-weight: 600; }
code { font-family: Consolas, monospace; font-size: 9.5pt; background: #f1efe9; padding: 0 1mm; border-radius: 2px; }
.ui { font-weight: 600; background: #eef4fc; border: 1px solid #cfe0f6; border-radius: 3px; padding: 0 1.2mm; white-space: nowrap; }
figure { margin: 3mm 0 4mm; break-inside: avoid; }
figure img { width: 100%; border: 1px solid #d9d6cc; border-radius: 6px; display: block; }
figcaption { font-size: 9pt; color: #6b6a63; margin-top: 1.2mm; }
table { border-collapse: collapse; width: 100%; margin: 2mm 0 4mm; font-size: 9.8pt; break-inside: avoid; }
th, td { border: 1px solid #d9d6cc; padding: 1.6mm 2.2mm; text-align: left; vertical-align: top; }
th { background: #f1efe9; font-weight: 600; }
.note { border-left: 3px solid #2a7de1; background: #eef4fc; padding: 2.2mm 3mm; margin: 3mm 0; break-inside: avoid; }
.warn { border-left: 3px solid #d08a00; background: #fdf5e4; padding: 2.2mm 3mm; margin: 3mm 0; break-inside: avoid; }
.cover { height: 250mm; display: flex; flex-direction: column; justify-content: center; }
.cover .logo { width: 22mm; height: 22mm; border-radius: 5mm; background: #0f7b80; display: flex; align-items: center;
               justify-content: center; gap: 1.6mm; margin-bottom: 8mm; }
.cover .logo i { display: block; width: 1.6mm; background: #fff; border-radius: 1mm; }
.cover .sub { font-size: 14pt; color: #4b4a45; margin-bottom: 10mm; }
.cover .meta { color: #6b6a63; font-size: 10pt; margin-top: 10mm; }
.flow { display: flex; gap: 2mm; margin: 4mm 0; }
.flow div { flex: 1; border: 1px solid #cfe0f6; background: #eef4fc; border-radius: 4px; padding: 2mm; text-align: center; font-size: 9.5pt; }
.flow b { display: block; color: #2a7de1; font-size: 13pt; }
.toc { columns: 2; column-gap: 10mm; padding-left: 0; list-style: none; }
.toc li { margin-bottom: 1.5mm; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 4mm; }
.check li { list-style: "☐  "; }
"""

LOGO = '<div class="logo">' + "".join(f'<i style="height:{h}mm"></i>' for h in (5, 9, 13, 9, 5)) + "</div>"


def fig(lang, name, cap):
    return f'<figure><img src="img/{lang}-{name}.png" alt=""><figcaption>{cap}</figcaption></figure>'


def ui(s):
    return f'<span class="ui">{s}</span>'


# --------------------------------------------------------------------------- English
def en():
    L = "en"
    return f"""
<section class="cover">{LOGO}
<h1>Kokoro Reader</h1>
<div class="sub">Getting Started User Manual</div>
<p>Read text aloud, turn a video's speech into subtitles, translate English ↔ 繁體中文,
and give the video a new voice. Everything runs on your own Windows laptop: no internet,
no uploads, no account.</p>
<div class="flow"><div><b>1</b>Transcribe</div><div><b>2</b>Translate</div><div><b>3</b>Review</div><div><b>4</b>Voice</div><div><b>5</b>Export</div></div>
<div class="meta">Version {VERSION} · ETINSTW · 繁體中文版：《Kokoro Reader 使用入門》</div>
</section>

<h2><span class="n">0</span>Contents</h2>
<ol class="toc">
<li>1 · Install</li><li>2 · Start and stop</li><li>3 · Read a text file aloud</li>
<li>4 · Dub a video: overview</li><li>5 · Step 1 Transcribe</li><li>6 · Step 2 Translate</li>
<li>7 · Step 3 Review</li><li>8 · The glossary</li><li>9 · Step 4 Voice</li>
<li>10 · Step 5 Export</li><li>11 · A video that already has subtitles</li><li>12 · How long things take</li>
<li>13 · Where files are kept</li><li>14 · Troubleshooting</li><li>15 · One-page checklist</li>
</ol>
<h3>What you can do</h3>
<table><tr><th>You have</th><th>Kokoro Reader gives you</th><th>Go to</th></tr>
<tr><td>A text file (.txt / .md)</td><td>The text read aloud with each word highlighted, saved as WAV or MP3</td><td>Section 3</td></tr>
<tr><td>A video, English or Chinese</td><td>Subtitles, a translation you review line by line, and the video with a new voice in the other language</td><td>Sections 4–10</td></tr>
<tr><td>A subtitle file (.srt) and its video</td><td>The same, starting from your subtitles</td><td>Section 11</td></tr></table>
<div class="note"><b>Privacy:</b> all speech recognition, translation and voices are built into the program.
Your videos and texts never leave your laptop.</div>

<h2><span class="n">1</span>Install</h2>
<p><b>You need:</b> Windows 10 or 11 (64-bit), about 5 GB free disk space, 16 GB RAM recommended
(8 GB is fine for text and short videos). No administrator rights and no internet are needed.</p>
<ol>
<li>Copy <code>{INSTALLER}</code> (about 2.8 GB) to your laptop and double-click it.</li>
<li>If Windows shows <b>“Windows protected your PC”</b>, click {ui("More info")} → {ui("Run anyway")}.
The installer is not signed with a company certificate; do this only for the installer you received from ETINSTW.</li>
<li>Choose English or 繁體中文 for the installer, read the welcome page and click {ui("Next")}.</li>
<li>Optionally tick {ui("Create a desktop shortcut")}, then click {ui("Install")}. Installing takes about 5–6 minutes.</li>
<li>Leave {ui("Start Kokoro Reader now")} ticked and click {ui("Finish")}.</li>
</ol>
<p>Everything is included in the one installer: the program, Python, the English and Chinese voices,
the speech-recognition models, the translation models and FFmpeg for video. Nothing is downloaded later.</p>
<p>The Start menu gets three entries: <b>Kokoro Reader</b>, <b>Kokoro Reader – Getting Started</b> (this manual) and <b>Kokoro Reader – 使用入門</b> (the 繁體中文 manual).</p>

<h2><span class="n">2</span>Start and stop</h2>
<ol>
<li>Open <b>Kokoro Reader</b> from the Start menu. It opens in your web browser at <code>127.0.0.1</code>,
which is your own laptop, not a website.</li>
<li>{ui("EN")} / {ui("繁中")} at the top right switches the language of the screens.</li>
<li>{ui("Getting started")} opens a short version of this manual inside the app.</li>
<li>When you finish, click {ui("Quit")}. If you only close the browser tab, the app stops by itself
about 5 minutes later, but never while it is still working.</li>
</ol>
{fig(L, "01-welcome", "The start screen. “Continue: …” brings back the last video you worked on.")}
<div class="note">Your work is saved as you go. After closing the app, open it again and click
{ui("Continue: &lt;video name&gt;")} to carry on where you stopped.</div>
{fig(L, "02-guide", "Getting started inside the app: the same steps in short form, in English or 繁體中文.")}

<h2><span class="n">3</span>Read a text file aloud</h2>
<ol>
<li>Click {ui("Open file")} and choose a <code>.txt</code> or <code>.md</code> file.</li>
<li>Choose the <b>Language</b> and <b>Voice</b>. Defaults: <code>af_bella</code> for English, <code>zm_009</code> for Chinese.
Optionally set the tone, speed and pause between sentences.
Hover over any label with a dashed underline for an explanation.</li>
<li>Click {ui("Generate")}. The first time after starting the app it takes 30–40 seconds longer while the voice loads.</li>
<li>Press ▶ to listen. Click any word to jump there. Save the audio as WAV or MP3 from the list of files under the player.</li>
</ol>
{fig(L, "13-text", "Text mode: settings at the top, the text below, highlighted while it is read.")}

<h2><span class="n">4</span>Dub a video: overview</h2>
<p>Click {ui("Open video")} and choose the video (MP4, MOV, MKV and most other formats).
A bar of five steps appears and guides you from left to right:</p>
<div class="flow"><div><b>1</b>Transcribe<br>speech → subtitles</div><div><b>2</b>Translate<br>EN ↔ 繁中</div><div><b>3</b>Review<br>check &amp; fix</div><div><b>4</b>Voice<br>new voice track</div><div><b>5</b>Export<br>save files</div></div>
<ul>
<li>The step you are on is <b style="color:#2a7de1">blue</b>. Finished steps turn <b style="color:#3d6b1f">green ✓</b>.
Locked steps 🔒 open by themselves as soon as the step before is ready.</li>
<li>Each step shows a blue instruction line explaining what to do, and {ui("Back")} / {ui("Next")} buttons at the bottom.</li>
<li>Long videos are cut into chunks of about 5 minutes at natural pauses. You can review chunk 1
while the later chunks are still being transcribed.</li>
<li>The lower card has two tabs: {ui("Review")} (the table of lines) and {ui("Play &amp; highlight")} (watch the result).</li>
</ul>
<div class="warn">Keep the laptop plugged in and awake while it works. Long videos take a while (see section 12).
{ui("Stop")} and {ui("Resume")} continue exactly where they left off, even after closing the app.</div>

<h2><span class="n">5</span>Step 1 · Transcribe</h2>
<p>Turns the speech in the video into time-coded subtitle lines.</p>
<table><tr><th>Setting</th><th>Recommended</th><th>Why</th></tr>
<tr><td>Spoken language</td><td>Auto</td><td>Detects English or Chinese by itself. Choose it yourself only if Auto guesses wrong.</td></tr>
<tr><td>Chunk length</td><td>About 5 min</td><td>Lets you start reviewing early. “Whole video” is fine for clips under 10 minutes.</td></tr>
<tr><td>Accuracy</td><td>Best</td><td>“Fast” is about twice as quick but makes more mistakes; use it for rough drafts.</td></tr></table>
<ol><li>Check the settings and click {ui("Start transcribing")}.</li>
<li>Watch the progress bar. As soon as the first chunk is done, step 2 opens; you don't have to wait for the rest.</li></ol>
{fig(L, "03-step1", "Step 1 when finished: 202 lines from a 14-minute video, 2.6× faster than real time.")}

<h2><span class="n">6</span>Step 2 · Translate</h2>
<p>Each chunk is translated as soon as it is transcribed.</p>
<ul>
<li><b>Translate to</b> = <b>Automatic</b>: English videos become 繁體中文 (Taiwan wording); Chinese videos become English.</li>
<li>Choose <b>Off — same language</b> if you only want to re-voice the video in its own language, for example to replace a poor recording.</li>
<li>{ui("Translate again")} redoes the translation, for example after you add many glossary terms.
Lines you already edited by hand are kept.</li>
</ul>
<p>The translation works sentence by sentence, then spreads each sentence back over its subtitle lines,
so the meaning stays whole even when a sentence is split over several lines.</p>
{fig(L, "04-step2", "Step 2: choose the direction; the progress shows how many chunks are translated.")}

<h2><span class="n">7</span>Step 3 · Review</h2>
<p>This is where you make the translation right. The machine translation is literal; plan to fix some lines.</p>
{fig(L, "05-step3", "Step 3: the counters show how much is reviewed, flagged and edited.")}
<h3>The review table</h3>
{fig(L, "06-review", "The Review tab: video, chunk buttons, filters, and the original and translation side by side.")}
<ol>
<li>Pick a chunk with the chunk buttons (for example <b>Chunk 1 · 0:00–5:07</b>).</li>
<li>Click {ui("⚠ Flagged")} to see the lines most likely to need work first.</li>
<li>Click a translation to edit it. <b>Enter</b> saves, <b>Esc</b> cancels.
While editing you can also click {ui("Re-translate")} or {ui("Undo edit")} (back to the machine translation).</li>
<li>▶ plays that line in the video so you can hear what was really said. ✎ edits the original text.</li>
<li>Tick ✓ for each line that is right, or click {ui("Mark chunk reviewed")} when the whole chunk is done.</li>
<li>Repeat for each chunk. {ui("Not reviewed")} shows what is left.</li>
</ol>
<h3>What the ⚠ marks mean</h3>
<p>They are hints, not errors.</p>
<table><tr><th>Mark</th><th>Meaning</th><th>What to do</th></tr>
<tr><td>⤓ join</td><td>The sentence continues on the next line.</td><td>Click it to merge the two lines into one.</td></tr>
<tr><td>long</td><td>The translation is probably too long to speak in the time available.</td><td>Shorten the wording.</td></tr>
<tr><td>unsure</td><td>The transcriber was not sure about some words.</td><td>Press ▶, listen, and fix the original text (✎).</td></tr>
<tr><td>late</td><td>After step 4: the new voice ran past the next line.</td><td>Shorten that line and generate the voice again.</td></tr></table>

<h2><span class="n">8</span>The glossary: teach it your words once</h2>
<p>Product names and technical terms are often translated wrongly. Fix them once in the glossary and every
later video uses your terms. Glossary terms are underlined in green in the table.</p>
<ol>
<li>In the table, select the wrong word with the mouse.</li>
<li>Right-click → the <b>Add to glossary</b> box opens with the word filled in.</li>
<li>Type the correct term on the other side. Leave the Chinese side empty to keep a term in English
(for example <i>FLIR Thermal Studio</i>).</li>
<li>Click {ui("Add + fix this line")}, or {ui("Add + re-translate all")} to apply it to every line.</li>
</ol>
{fig(L, "07-popup", "Right-click a selected word to add it to the glossary.")}
<p>The {ui("Glossary")} button lists all terms, where each came from and how often it is used.
You can search, edit and delete terms. {ui("Export .txt")} and {ui("Import .txt")} let colleagues share one list.</p>
{fig(L, "08-glossary", "The glossary window.")}

<h2><span class="n">9</span>Step 4 · Voice</h2>
<p>Makes the new voice track and puts it into the video.</p>
<ol>
<li>Check the <b>Voice</b>: <code>zm_009</code> (Chinese, male) or <code>af_bella</code> (English, female) by default; other voices are in the list.</li>
<li>Leave <b>Voice reads</b> = Translation, <b>Fit to timing</b> = Speed up + use gaps, <b>Max speed-up</b> = 1.25×.</li>
<li><b>Original audio</b> = <b>Replace — new voice only</b> (default). The video's old sound is removed and only the
new voice remains, so you never hear two voices at once. Background music is removed too.</li>
<li>Click {ui("Generate voice")}. The time meter shows progress; <b>Lines fit</b> shows how many lines fit their time slot.</li>
<li>Open the {ui("Play &amp; highlight")} tab and watch the result.</li>
</ol>
{fig(L, "10-step4-done", "Step 4 when finished: 8 of 10 lines fit; the 2 late lines are marked in the review table.")}
{fig(L, "12-play", "Play &amp; highlight: the video with its new voice, and the text highlighted as it is spoken.")}
<div class="note">If some lines run late, go back to step 3, filter ⚠ Flagged, shorten the lines marked <b>late</b>,
and generate the voice again. Raising <b>Max speed-up</b> to 1.4× is a quicker fix but sounds hurried.</div>

<h2><span class="n">10</span>Step 5 · Export</h2>
<p>Tick the files you need and click {ui("Save selected")}, or {ui("Save")} on one row.
Files are named after the video and go to your Downloads folder.</p>
<table><tr><th>File</th><th>Example name</th><th>Use it for</th></tr>
<tr><td>Video with new voice (MP4)</td><td><code>video.zh-TW.mp4</code></td><td>The finished dubbed video</td></tr>
<tr><td>Voice only (WAV)</td><td><code>video.zh-TW.wav</code></td><td>Editing in another video program</td></tr>
<tr><td>New subtitles, re-timed to the voice</td><td><code>video.zh-TW.srt</code></td><td>Subtitles for the dubbed video</td></tr>
<tr><td>Original subtitles</td><td><code>video.en.srt</code></td><td>Subtitles for the original video</td></tr>
<tr><td>Bilingual subtitles</td><td><code>video.en+zh-TW.srt</code></td><td>Both languages on each line, for checking or training</td></tr></table>
{fig(L, "11-step5", "Step 5: the three most-used files are ticked for you.")}

<h2><span class="n">11</span>A video that already has subtitles</h2>
<p>If you already have a good <code>.srt</code> for the video, skip transcription:</p>
<ol>
<li>Click {ui("Open file")} and choose the <code>.srt</code>. The app starts at step 2.</li>
<li>Click {ui("Open video")} and choose the matching video (needed for steps 3–5).</li>
<li>Continue with steps 2 to 5 as usual.</li>
</ol>

<h2><span class="n">12</span>How long things take</h2>
<p>Measured on an ETINSTW laptop (Intel Core Ultra 7, no graphics card needed):</p>
<table><tr><th>Work</th><th>14-minute video</th><th>1-hour video (estimate)</th></tr>
<tr><td>Step 1 Transcribe (Best)</td><td>about 6 min</td><td>about 25–30 min</td></tr>
<tr><td>Step 2 Translate</td><td>under 10 s</td><td>under 1 min</td></tr>
<tr><td>Step 4 Chinese voice</td><td>about 11 min</td><td>about 1 hour</td></tr>
<tr><td>Step 4 English voice</td><td>about 8 min</td><td>about 40 min</td></tr></table>
<p>The first voice after starting the app adds 30–80 seconds while the voice model loads.
Review time depends on you: plan roughly 10–20 minutes per 5-minute chunk the first time; less as your glossary grows.</p>
<div class="note"><b>Tip for long videos:</b> start transcription, then review each chunk as it becomes ready.
Generate the voice at the end of the day or over lunch.</div>

<h2><span class="n">13</span>Where files are kept</h2>
<table><tr><th>What</th><th>Where</th></tr>
<tr><td>Files you save in step 5 or text mode</td><td>Your Downloads folder</td></tr>
<tr><td>Work in progress, the glossary, a log file</td><td><code>%LOCALAPPDATA%\\KokoroReader</code></td></tr>
<tr><td>The program and this manual</td><td><code>%LOCALAPPDATA%\\Programs\\Kokoro Reader</code></td></tr></table>
<div class="warn"><b>Uninstalling</b> (Windows Settings → Apps → Kokoro Reader → Uninstall) removes the program
<b>and</b> the work folder, including your glossary. Click {ui("Glossary")} → {ui("Export .txt")} first if you want to keep it.
Installing a newer version over the old one keeps your work and glossary.</div>

<h2><span class="n">14</span>Troubleshooting</h2>
<table><tr><th>Problem</th><th>What to do</th></tr>
<tr><td>Windows blocks the installer</td><td>{ui("More info")} → {ui("Run anyway")} (section 1).</td></tr>
<tr><td>Nothing seems to happen after Start transcribing or Generate</td><td>The first load can take up to a minute. Watch the progress text.</td></tr>
<tr><td>The page says the app has stopped</td><td>Open Kokoro Reader from the Start menu again and click {ui("Continue: …")}.</td></tr>
<tr><td>Step 5 is empty after reopening the app</td><td>The voice is not kept after quitting. Go to step 4 and click {ui("Generate voice")} again; your edits are kept.</td></tr>
<tr><td>The voice runs late on some lines</td><td>Shorten those lines in step 3, or raise Max speed-up in step 4.</td></tr>
<tr><td>Product names are translated wrongly</td><td>Add them to the glossary once (section 8).</td></tr>
<tr><td>A Chinese word is pronounced oddly</td><td>A known limit of the Chinese voice. Rephrase the line, or write a brand name in English.</td></tr>
<tr><td>The wrong language was detected</td><td>Open the video again and set Spoken language yourself in step 1.</td></tr>
<tr><td>Anything else</td><td>Send the file <code>%LOCALAPPDATA%\\KokoroReader\\kokoro-reader.log</code> to the person who gave you the installer.</td></tr></table>

<h2><span class="n">15</span>One-page checklist</h2>
<div class="two"><div>
<h3>Dub a video</h3>
<ul class="check">
<li>{ui("Open video")}</li>
<li>Step 1: Auto · About 5 min · Best → {ui("Start transcribing")}</li>
<li>Step 2: Automatic</li>
<li>Step 3: per chunk → ⚠ Flagged first → edit → ✓ → {ui("Mark chunk reviewed")}</li>
<li>Wrong term? Select → right-click → Add to glossary</li>
<li>Step 4: check voice · Original audio = Replace → {ui("Generate voice")}</li>
<li>Watch in {ui("Play &amp; highlight")}; fix late lines, generate again</li>
<li>Step 5: tick files → {ui("Save selected")}</li>
<li>{ui("Quit")}</li>
</ul></div><div>
<h3>Read a text aloud</h3>
<ul class="check">
<li>{ui("Open file")} → .txt / .md</li>
<li>Language and voice</li>
<li>{ui("Generate")}</li>
<li>▶ listen · click a word to jump</li>
<li>Save WAV / MP3</li>
<li>{ui("Quit")}</li>
</ul>
<h3>Keyboard in the review table</h3>
<ul><li><b>Enter</b>: save the edit</li><li><b>Esc</b>: cancel the edit or close the glossary box</li></ul>
</div></div>
"""


# --------------------------------------------------------------------------- 繁體中文
def zh():
    L = "zh"
    return f"""
<section class="cover">{LOGO}
<h1>Kokoro Reader</h1>
<div class="sub">使用入門手冊</div>
<p>朗讀文字、將影片語音轉成字幕、英文 ↔ 繁體中文翻譯，並為影片配上新的語音。
所有處理都在您自己的 Windows 筆電上完成：不需網路、不上傳檔案、不需帳號。</p>
<div class="flow"><div><b>1</b>轉錄</div><div><b>2</b>翻譯</div><div><b>3</b>校對</div><div><b>4</b>配音</div><div><b>5</b>匯出</div></div>
<div class="meta">版本 {VERSION} · ETINSTW · English edition: “Kokoro Reader – Getting Started”</div>
</section>

<h2><span class="n">0</span>目錄</h2>
<ol class="toc">
<li>1 · 安裝</li><li>2 · 啟動與結束</li><li>3 · 朗讀文字檔</li>
<li>4 · 影片配音：總覽</li><li>5 · 步驟 1 轉錄</li><li>6 · 步驟 2 翻譯</li>
<li>7 · 步驟 3 校對</li><li>8 · 詞彙表</li><li>9 · 步驟 4 配音</li>
<li>10 · 步驟 5 匯出</li><li>11 · 已有字幕的影片</li><li>12 · 所需時間</li>
<li>13 · 檔案存放位置</li><li>14 · 疑難排解</li><li>15 · 一頁檢查表</li>
</ol>
<h3>可以做什麼</h3>
<table><tr><th>您有</th><th>Kokoro Reader 提供</th><th>請看</th></tr>
<tr><td>文字檔（.txt / .md）</td><td>朗讀並逐字標示，可存成 WAV 或 MP3</td><td>第 3 節</td></tr>
<tr><td>英文或中文影片</td><td>字幕、可逐句校對的翻譯，以及配上另一種語言新語音的影片</td><td>第 4–10 節</td></tr>
<tr><td>字幕檔（.srt）與其影片</td><td>同上，但從您的字幕開始</td><td>第 11 節</td></tr></table>
<div class="note"><b>隱私：</b>語音辨識、翻譯和語音都內建在程式中。您的影片與文字不會離開您的筆電。</div>

<h2><span class="n">1</span>安裝</h2>
<p><b>需求：</b>Windows 10 或 11（64 位元）、約 5 GB 可用磁碟空間，建議 16 GB 記憶體
（文字與短片 8 GB 即可）。不需系統管理員權限，也不需網路。</p>
<ol>
<li>將 <code>{INSTALLER}</code>（約 2.8 GB）複製到筆電，按兩下執行。</li>
<li>若 Windows 顯示<b>「Windows 已保護您的電腦」</b>，請按 {ui("其他資訊")} → {ui("仍要執行")}。
安裝程式沒有公司憑證簽章；請只對 ETINSTW 提供的安裝程式這樣做。</li>
<li>選擇安裝程式語言（English 或 繁體中文），閱讀歡迎頁面後按 {ui("下一步")}。</li>
<li>可勾選 {ui("建立桌面捷徑")}，再按 {ui("安裝")}。安裝約需 5–6 分鐘。</li>
<li>保留勾選 {ui("立即啟動 Kokoro Reader")}，按 {ui("完成")}。</li>
</ol>
<p>單一安裝程式已包含所有元件：程式本身、Python、英文與中文語音、語音辨識模型、翻譯模型，以及處理影片的 FFmpeg。之後不會再下載任何東西。</p>
<p>開始功能表會出現三個項目：<b>Kokoro Reader</b>、<b>Kokoro Reader – 使用入門</b>（本手冊）與 <b>Kokoro Reader – Getting Started</b>（英文版手冊）。</p>

<h2><span class="n">2</span>啟動與結束</h2>
<ol>
<li>從開始功能表開啟 <b>Kokoro Reader</b>。它會在您的網頁瀏覽器中以 <code>127.0.0.1</code> 開啟，
也就是您自己的筆電，而不是網站。</li>
<li>右上角的 {ui("EN")} / {ui("繁中")} 可切換畫面語言。</li>
<li>{ui("使用說明")} 會在程式內開啟本手冊的精簡版。</li>
<li>使用完畢請按 {ui("結束")}。若只關閉瀏覽器分頁，程式約 5 分鐘後會自動結束，但工作進行中絕不會結束。</li>
</ol>
{fig(L, "01-welcome", "開始畫面。「繼續上次的工作：…」可回到上次處理的影片。")}
<div class="note">工作會隨時自動儲存。關閉程式後再開啟，按 {ui("繼續上次的工作：&lt;影片名稱&gt;")} 即可從中斷處繼續。</div>
{fig(L, "02-guide", "程式內的「使用入門」：以英文或繁體中文簡要說明相同步驟。")}

<h2><span class="n">3</span>朗讀文字檔</h2>
<ol>
<li>按 {ui("開啟檔案")}，選擇 <code>.txt</code> 或 <code>.md</code> 檔案。</li>
<li>選擇<b>語言</b>與<b>語音</b>。預設：英文 <code>af_bella</code>、中文 <code>zm_009</code>。
也可設定語氣、速度與句間停頓。將滑鼠移到有虛線底線的標籤上可看到說明。</li>
<li>按 {ui("產生")}。程式啟動後第一次產生會多花 30–40 秒載入語音。</li>
<li>按 ▶ 播放，點任何字可跳到該處。在播放器下方的檔案清單中儲存 WAV 或 MP3。</li>
</ol>
{fig(L, "13-text", "文字模式：上方是設定，下方是文字，朗讀時會同步標示。")}

<h2><span class="n">4</span>影片配音：總覽</h2>
<p>按 {ui("開啟影片")} 並選擇影片（MP4、MOV、MKV 等大部分格式皆可）。畫面會出現五個步驟的列，由左至右引導您：</p>
<div class="flow"><div><b>1</b>轉錄<br>語音 → 字幕</div><div><b>2</b>翻譯<br>英 ↔ 中</div><div><b>3</b>校對<br>檢查與修正</div><div><b>4</b>配音<br>新語音音軌</div><div><b>5</b>匯出<br>儲存檔案</div></div>
<ul>
<li>目前的步驟是<b style="color:#2a7de1">藍色</b>；完成的步驟變成<b style="color:#3d6b1f">綠色 ✓</b>。
鎖定的步驟 🔒 會在前一步準備好時自動開啟。</li>
<li>每個步驟都有藍色的說明列告訴您該做什麼，底部有 {ui("上一步")} / {ui("下一步")} 按鈕。</li>
<li>長影片會在自然停頓處切成約 5 分鐘的段落。後面段落還在轉錄時，您就可以先校對第 1 段。</li>
<li>下方卡片有兩個分頁：{ui("校對")}（逐句表格）與 {ui("播放與標示")}（觀看結果）。</li>
</ul>
<div class="warn">處理期間請接上電源並保持筆電不休眠。長影片需要一段時間（見第 12 節）。
{ui("停止")} 與 {ui("繼續")} 會從中斷處接續，即使關閉程式後也可以。</div>

<h2><span class="n">5</span>步驟 1 · 轉錄</h2>
<p>將影片中的語音轉成有時間碼的字幕句子。</p>
<table><tr><th>設定</th><th>建議</th><th>原因</th></tr>
<tr><td>影片語言</td><td>自動偵測</td><td>會自行判斷英文或中文。只有自動判斷錯誤時才自己選擇。</td></tr>
<tr><td>分段長度</td><td>約 5 分鐘</td><td>可以提早開始校對。10 分鐘以下的短片選「整部影片」也可以。</td></tr>
<tr><td>準確度</td><td>最佳</td><td>「快速」約快一倍，但錯誤較多；適合粗略草稿。</td></tr></table>
<ol><li>確認設定後按 {ui("開始轉錄")}。</li>
<li>觀察進度列。第一段完成後步驟 2 就會開啟，不必等全部完成。</li></ol>
{fig(L, "03-step1", "步驟 1 完成：14 分鐘影片轉出 202 句，速度為實際時間的 2.6 倍。")}

<h2><span class="n">6</span>步驟 2 · 翻譯</h2>
<p>每段轉錄完成後會立即翻譯。</p>
<ul>
<li><b>翻譯成</b> = <b>自動</b>：英文影片翻成繁體中文（台灣用語），中文影片翻成英文。</li>
<li>若只想用原語言重新配音（例如替換錄音品質不佳的旁白），請選<b>關閉 — 同一語言</b>。</li>
<li>{ui("重新翻譯")} 會重做翻譯，例如在加入許多詞彙後。您手動修改過的句子會保留。</li>
</ul>
<p>翻譯以整句為單位，再分配回各字幕行，因此即使一句話被拆成好幾行，意思仍然完整。</p>
{fig(L, "04-step2", "步驟 2：選擇翻譯方向；進度顯示已翻譯的段落數。")}

<h2><span class="n">7</span>步驟 3 · 校對</h2>
<p>在這裡把翻譯修正好。機器翻譯偏向直譯，請預期需要修改部分句子。</p>
{fig(L, "05-step3", "步驟 3：計數顯示已校對、已標示與已修改的數量。")}
<h3>校對表格</h3>
{fig(L, "06-review", "校對分頁：影片、段落按鈕、篩選，以及原文與譯文並排。")}
<ol>
<li>用段落按鈕選擇段落（例如<b>第 1 段 · 0:00–5:07</b>）。</li>
<li>按 {ui("⚠ 標記")}，先看最可能需要修改的句子。</li>
<li>點一下譯文即可編輯。<b>Enter</b> 儲存，<b>Esc</b> 取消。
編輯時也可以按 {ui("重新翻譯")} 或 {ui("復原修改")}（回到機器翻譯）。</li>
<li>▶ 播放影片中的該句，讓您聽到實際說了什麼。✎ 可修改原文。</li>
<li>每句正確就勾選 ✓；整段完成後按 {ui("標記本段已校對")}。</li>
<li>對每一段重複以上步驟。{ui("未校對")} 會顯示剩下的句子。</li>
</ol>
<h3>⚠ 標示的意思</h3>
<p>這些是提示，不是錯誤。</p>
<table><tr><th>標示</th><th>意思</th><th>處理方式</th></tr>
<tr><td>⤓ 合併</td><td>句子延續到下一行。</td><td>點一下即可把兩行合成一行。</td></tr>
<tr><td>太長</td><td>譯文可能太長，無法在可用時間內說完。</td><td>縮短用字。</td></tr>
<tr><td>不確定</td><td>轉錄時對某些字沒有把握。</td><td>按 ▶ 聆聽，修正原文（✎）。</td></tr>
<tr><td>延遲</td><td>步驟 4 之後：新語音超過了下一句的開始時間。</td><td>縮短該句，再產生一次語音。</td></tr></table>

<h2><span class="n">8</span>詞彙表：教一次就記住</h2>
<p>產品名稱與專業術語常被翻錯。在詞彙表修正一次，之後每部影片都會使用您的用詞。詞彙表中的詞在表格中以綠色底線標示。</p>
<ol>
<li>在表格中用滑鼠選取翻錯的字詞。</li>
<li>按右鍵 → 開啟<b>加入詞彙表</b>，已自動填入該字詞。</li>
<li>在另一邊輸入正確用詞。中文欄留空表示保留英文（例如 <i>FLIR Thermal Studio</i>）。</li>
<li>按 {ui("加入並修正這一行")}，或 {ui("加入並重新翻譯全部")} 套用到所有句子。</li>
</ol>
{fig(L, "07-popup", "選取字詞後按右鍵，即可加入詞彙表。")}
<p>{ui("詞彙表")} 按鈕會列出所有詞彙、來源與使用次數，可搜尋、修改與刪除。
{ui("匯出 .txt")} 與 {ui("匯入 .txt")} 可讓同事共用同一份清單。</p>
{fig(L, "08-glossary", "詞彙表視窗。")}

<h2><span class="n">9</span>步驟 4 · 配音</h2>
<p>產生新的語音音軌並放進影片中。</p>
<ol>
<li>確認<b>語音</b>：預設中文 <code>zm_009</code>（男聲）、英文 <code>af_bella</code>（女聲）；清單中還有其他語音。</li>
<li>保留<b>配音內容</b> = 譯文、<b>對齊時間</b> = 加速 + 使用空檔、<b>最高加速</b> = 1.25×。</li>
<li><b>原始音訊</b> = <b>取代 — 只有新配音</b>（預設）。影片原本的聲音會移除，只留下新語音，
因此絕不會同時聽到兩個聲音。背景音樂也會一併移除。</li>
<li>按 {ui("產生配音")}。時間表顯示進度；<b>符合時間的行數</b>顯示有多少句能在時間內說完。</li>
<li>開啟 {ui("播放與標示")} 分頁觀看結果。</li>
</ol>
{fig(L, "10-step4-done", "步驟 4 完成：10 句中有 8 句吻合；2 句延遲的句子會在校對表格中標示。")}
{fig(L, "12-play", "播放與標示：配上新語音的影片，文字隨語音同步標示。")}
<div class="note">若有句子延遲，請回到步驟 3，篩選 ⚠ 標記，縮短標示為<b>延遲</b>的句子，再產生一次語音。
把<b>最高加速</b>調到 1.4× 是較快的辦法，但聽起來會比較趕。</div>

<h2><span class="n">10</span>步驟 5 · 匯出</h2>
<p>勾選需要的檔案後按 {ui("儲存已勾選")}，或按單一列的 {ui("儲存")}。檔案以影片名稱命名，存到您的「下載」資料夾。</p>
<table><tr><th>檔案</th><th>名稱範例</th><th>用途</th></tr>
<tr><td>配上新語音的影片（MP4）</td><td><code>video.zh-TW.mp4</code></td><td>完成的配音影片</td></tr>
<tr><td>只有語音（WAV）</td><td><code>video.zh-TW.wav</code></td><td>在其他影片軟體中編輯</td></tr>
<tr><td>新字幕，配合新語音重新計時</td><td><code>video.zh-TW.srt</code></td><td>配音影片的字幕</td></tr>
<tr><td>原文字幕</td><td><code>video.en.srt</code></td><td>原始影片的字幕</td></tr>
<tr><td>雙語字幕</td><td><code>video.en+zh-TW.srt</code></td><td>每行兩種語言，供檢查或教學使用</td></tr></table>
{fig(L, "11-step5", "步驟 5：最常用的三個檔案已預先勾選。")}

<h2><span class="n">11</span>已有字幕的影片</h2>
<p>若影片已有品質良好的 <code>.srt</code>，可略過轉錄：</p>
<ol>
<li>按 {ui("開啟檔案")} 選擇 <code>.srt</code>，程式會從步驟 2 開始。</li>
<li>按 {ui("開啟影片")} 選擇對應的影片（步驟 3–5 需要）。</li>
<li>照常進行步驟 2 到 5。</li>
</ol>

<h2><span class="n">12</span>所需時間</h2>
<p>在 ETINSTW 筆電上實測（Intel Core Ultra 7，不需獨立顯示卡）：</p>
<table><tr><th>工作</th><th>14 分鐘影片</th><th>1 小時影片（估計）</th></tr>
<tr><td>步驟 1 轉錄（最佳）</td><td>約 6 分鐘</td><td>約 25–30 分鐘</td></tr>
<tr><td>步驟 2 翻譯</td><td>10 秒內</td><td>1 分鐘內</td></tr>
<tr><td>步驟 4 中文配音</td><td>約 11 分鐘</td><td>約 1 小時</td></tr>
<tr><td>步驟 4 英文配音</td><td>約 8 分鐘</td><td>約 40 分鐘</td></tr></table>
<p>程式啟動後第一次產生配音，會多花 30–80 秒載入語音模型。校對時間因人而異：第一次每 5 分鐘段落約需 10–20 分鐘，詞彙表累積後會越來越快。</p>
<div class="note"><b>長影片小技巧：</b>先開始轉錄，每段準備好就開始校對。配音可以排在下班前或午餐時間進行。</div>

<h2><span class="n">13</span>檔案存放位置</h2>
<table><tr><th>內容</th><th>位置</th></tr>
<tr><td>在步驟 5 或文字模式儲存的檔案</td><td>您的「下載」資料夾</td></tr>
<tr><td>進行中的工作、詞彙表、記錄檔</td><td><code>%LOCALAPPDATA%\\KokoroReader</code></td></tr>
<tr><td>程式與本手冊</td><td><code>%LOCALAPPDATA%\\Programs\\Kokoro Reader</code></td></tr></table>
<div class="warn"><b>解除安裝</b>（Windows 設定 → 應用程式 → Kokoro Reader → 解除安裝）會移除程式<b>以及</b>工作資料夾，
包括您的詞彙表。若要保留，請先按 {ui("詞彙表")} → {ui("匯出 .txt")}。直接安裝新版本覆蓋舊版會保留您的工作與詞彙表。</div>

<h2><span class="n">14</span>疑難排解</h2>
<table><tr><th>問題</th><th>處理方式</th></tr>
<tr><td>Windows 封鎖安裝程式</td><td>{ui("其他資訊")} → {ui("仍要執行")}（第 1 節）。</td></tr>
<tr><td>按下開始轉錄或產生後似乎沒反應</td><td>第一次載入可能需要一分鐘，請留意進度文字。</td></tr>
<tr><td>頁面顯示程式已停止</td><td>從開始功能表再次開啟 Kokoro Reader，按 {ui("繼續上次的工作：…")}。</td></tr>
<tr><td>重新開啟程式後步驟 5 是空的</td><td>結束程式後不會保留語音。回到步驟 4 再按一次 {ui("產生配音")}；您的修改都會保留。</td></tr>
<tr><td>部分句子的語音延遲</td><td>在步驟 3 縮短這些句子，或在步驟 4 提高最高加速。</td></tr>
<tr><td>產品名稱翻錯</td><td>加入詞彙表一次即可（第 8 節）。</td></tr>
<tr><td>某個中文詞發音怪怪的</td><td>中文語音模型的已知限制。請換個說法，品牌名稱可寫成英文。</td></tr>
<tr><td>語言判斷錯誤</td><td>重新開啟影片，在步驟 1 自行設定影片語言。</td></tr>
<tr><td>其他問題</td><td>將 <code>%LOCALAPPDATA%\\KokoroReader\\kokoro-reader.log</code> 傳給提供安裝程式的人。</td></tr></table>

<h2><span class="n">15</span>一頁檢查表</h2>
<div class="two"><div>
<h3>影片配音</h3>
<ul class="check">
<li>{ui("開啟影片")}</li>
<li>步驟 1：自動偵測 · 約 5 分鐘 · 最佳 → {ui("開始轉錄")}</li>
<li>步驟 2：自動</li>
<li>步驟 3：逐段 → 先看 ⚠ 標記 → 修改 → ✓ → {ui("標記本段已校對")}</li>
<li>用詞錯誤？選取 → 右鍵 → 加入詞彙表</li>
<li>步驟 4：確認語音 · 原始音訊 = 取代 → {ui("產生配音")}</li>
<li>在 {ui("播放與標示")} 觀看；修正延遲的句子後再產生一次</li>
<li>步驟 5：勾選檔案 → {ui("儲存已勾選")}</li>
<li>{ui("結束")}</li>
</ul></div><div>
<h3>朗讀文字</h3>
<ul class="check">
<li>{ui("開啟檔案")} → .txt / .md</li>
<li>語言與語音</li>
<li>{ui("產生")}</li>
<li>▶ 聆聽 · 點字詞可跳轉</li>
<li>儲存 WAV / MP3</li>
<li>{ui("結束")}</li>
</ul>
<h3>校對表格的鍵盤操作</h3>
<ul><li><b>Enter</b>：儲存修改</li><li><b>Esc</b>：取消修改或關閉詞彙框</li></ul>
</div></div>
"""


def build(lang, title, body, out_name):
    html = (f'<!doctype html><html lang="{"zh-Hant-TW" if lang == "zh" else "en"}"><head><meta charset="utf-8">'
            f"<title>{title}</title><style>{CSS}</style></head><body><div class=\"wrap\">{body}</div></body></html>")
    src = HERE / f"manual-{lang}.html"
    src.write_text(html, encoding="utf-8")
    pdf = HERE / out_name
    tmp = HERE / f"_print-{lang}.pdf"
    tmp.unlink(missing_ok=True)
    prof = tempfile.mkdtemp(prefix="kr-edge-")
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--user-data-dir={prof}",
                    f"--print-to-pdf={tmp}", src.as_uri()], check=True, timeout=120,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import time
    for _ in range(120):
        if tmp.exists() and tmp.stat().st_size > 0:
            time.sleep(1); break
        time.sleep(0.5)
    tmp.replace(pdf)
    print(pdf, pdf.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    build("en", "Kokoro Reader – Getting Started", en(), "Kokoro Reader - Getting Started.pdf")
    build("zh", "Kokoro Reader – 使用入門", zh(), "Kokoro Reader - 使用入門.pdf")
