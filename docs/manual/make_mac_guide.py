"""Write the 2-page "Install on a Mac" guides (EN + 繁中) that ship in the macOS zip.

Run: .venv\\Scripts\\python.exe docs\\manual\\make_mac_guide.py   (uses make_manual's style and Edge printing)
"""
from make_manual import LOGO, build, ui

VERSION = "1.1.1"
ZIP = f"KokoroReader-Setup-{VERSION}-macOS.zip"
QCMD = 'xattr -dr com.apple.quarantine "/Applications/Kokoro Reader.app"'
DATA = "~/Library/Application Support/KokoroReader"

EN = f"""
<div style="display:flex;align-items:center;gap:6mm;margin-bottom:4mm"><div class="cover" style="height:auto">{LOGO}</div>
<div><h1 style="margin:0">Kokoro Reader on a Mac</h1><div style="color:#4b4a45">Install guide · version {VERSION} ·
繁體中文版：《Kokoro Reader - Mac 安裝說明》</div></div></div>
<p>The Mac version works exactly like the Windows version described in <b>Kokoro Reader - Getting Started.pdf</b>.
This page covers what is different: installing, starting and where files are kept.</p>
<p><b>You need:</b> a Mac with Apple silicon (M1 or later; check Apple menu → About This Mac → Chip), macOS 14 Sonoma or later,
about 9 GB free disk space while installing (6 GB afterwards). 16 GB memory recommended for long videos.</p>

<h3>Install (once)</h3>
<ol>
<li>Double-click <code>{ZIP}</code> (about 3 GB). A folder <b>Kokoro Reader {VERSION}</b> appears next to it.</li>
<li>Drag <b>Kokoro Reader.app</b> from that folder into <b>Applications</b>. Please don't skip this: the app
refuses to start from the Downloads folder.</li>
<li>Open Applications and double-click <b>Kokoro Reader</b>. Because it is not from the App Store, macOS says it
could not check the app. Click {ui("Done")} (macOS 14: {ui("OK")}).</li>
<li>Open {ui("System Settings")} → {ui("Privacy &amp; Security")}. Scroll down to the message about
Kokoro Reader and click {ui("Open Anyway")}. Confirm with your password or Touch ID, then click {ui("Open Anyway")}
once more.</li>
<li>A notification says <i>Starting…</i>, and Kokoro Reader opens in your default browser. The first start takes up
to two minutes. Later starts are much quicker.</li>
</ol>
<div class="note">You only allow the app once. From then on, double-click it in Applications or find it with
Spotlight (<b>Cmd + Space</b>, type <i>Kokoro</i>).</div>
<div class="warn"><b>Still blocked, or more warnings about “python3.12” or a “.dylib” file?</b> Open <b>Terminal</b>
(Applications → Utilities), paste this line, press Return, then open Kokoro Reader again:<br>
<code>{QCMD}</code></div>

<h3>Differences from Windows</h3>
<table><tr><th>Topic</th><th>On a Mac</th></tr>
<tr><td>Start</td><td>Double-click Kokoro Reader in Applications. There is no Dock icon: the app lives in the browser tab.
Opening it again while it runs brings the page back.</td></tr>
<tr><td>Stop</td><td>Click {ui("Quit")} at the top of the page, or close the tab (it stops by itself about 5 minutes later).</td></tr>
<tr><td>Work, glossary, log file</td><td><code>{DATA}</code><br>Finder → Go → Go to Folder…, then paste the path.</td></tr>
<tr><td>The program</td><td><code>/Applications/Kokoro Reader.app</code> (includes all voices and models; works offline)</td></tr>
<tr><td>Saved WAV / MP3 / SRT / MP4</td><td>Your browser's download folder, usually <b>Downloads</b>.</td></tr>
<tr><td>Speed</td><td>Not measured on a Mac yet; expect roughly the times in the Getting Started manual, section 12.</td></tr></table>

<h3>Uninstall</h3>
<p>Drag Kokoro Reader from Applications to the Trash. To also remove your work and the glossary, delete
<code>{DATA}</code> and <code>~/Library/Caches/KokoroReader</code>.</p>

<h3>Troubleshooting</h3>
<table><tr><th>What you see</th><th>What to do</th></tr>
<tr><td>“Please drag Kokoro Reader into the Applications folder first”</td><td>Do step 2, then open it from Applications.</td></tr>
<tr><td>“needs a Mac with Apple silicon” / “needs macOS 14”</td><td>This Mac can't run Kokoro Reader. Use a newer Mac or the Windows version.</td></tr>
<tr><td>Nothing opens after two minutes</td><td>Open <code>http://127.0.0.1:7860</code> in the browser. If that fails, send
<code>{DATA}/kokoro-reader.log</code> to the person who gave you Kokoro Reader.</td></tr></table>
"""

ZH = f"""
<div style="display:flex;align-items:center;gap:6mm;margin-bottom:4mm"><div class="cover" style="height:auto">{LOGO}</div>
<div><h1 style="margin:0">在 Mac 上使用 Kokoro Reader</h1><div style="color:#4b4a45">安裝說明 · 版本 {VERSION} ·
English: “Kokoro Reader - Mac install”</div></div></div>
<p>Mac 版的操作方式與《Kokoro Reader - 使用入門.pdf》所介紹的 Windows 版完全相同。
本說明只介紹不同之處：安裝、啟動，以及檔案存放位置。</p>
<p><b>需求：</b>搭載 Apple 晶片（M1 或更新；在 Apple 選單 → 關於這台 Mac → 晶片 查看）的 Mac、macOS 14 Sonoma 或更新版本，
安裝時約需 9 GB 可用空間（安裝後佔用 6 GB）。處理長影片建議使用 16 GB 記憶體。</p>

<h3>安裝（只需一次）</h3>
<ol>
<li>按兩下 <code>{ZIP}</code>（約 3 GB），旁邊會出現資料夾 <b>Kokoro Reader {VERSION}</b>。</li>
<li>把資料夾中的 <b>Kokoro Reader.app</b> 拖到 <b>「應用程式」</b>。請不要略過這一步：程式無法從「下載項目」資料夾啟動。</li>
<li>打開「應用程式」，按兩下 <b>Kokoro Reader</b>。因為它不是來自 App Store，macOS 會說無法檢查此 App。
按 {ui("完成")}（macOS 14：{ui("好")}）。</li>
<li>打開 {ui("系統設定")} → {ui("隱私權與安全性")}，往下捲到關於 Kokoro Reader 的訊息，按 {ui("強制打開")}。
輸入密碼或使用 Touch ID 確認，再按一次 {ui("強制打開")}。</li>
<li>畫面會出現「啟動中…」通知，接著 Kokoro Reader 會在預設瀏覽器中開啟。第一次啟動最多需要兩分鐘，之後會快很多。</li>
</ol>
<div class="note">只需要允許一次。之後在「應用程式」中按兩下即可，或用 Spotlight（<b>Cmd + 空白鍵</b>，輸入 <i>Kokoro</i>）。</div>
<div class="warn"><b>仍然被阻擋，或又出現關於「python3.12」或「.dylib」檔案的警告？</b>
請打開 <b>終端機</b>（應用程式 → 工具程式），貼上下面這一行並按 Return，然後再開啟 Kokoro Reader：<br>
<code>{QCMD}</code></div>

<h3>與 Windows 版的差異</h3>
<table><tr><th>項目</th><th>在 Mac 上</th></tr>
<tr><td>啟動</td><td>在「應用程式」中按兩下 Kokoro Reader。Dock 上不會出現圖示，程式在瀏覽器分頁中運作。
程式執行中再開啟一次，會重新顯示頁面。</td></tr>
<tr><td>結束</td><td>按頁面上方的 {ui("結束")}，或關閉分頁（約 5 分鐘後會自動停止）。</td></tr>
<tr><td>工作、詞彙表、記錄檔</td><td><code>{DATA}</code><br>Finder → 前往 → 前往檔案夾…，貼上這個路徑。</td></tr>
<tr><td>程式本身</td><td><code>/Applications/Kokoro Reader.app</code>（內含所有語音與模型，可離線使用）</td></tr>
<tr><td>儲存的 WAV / MP3 / SRT / MP4</td><td>瀏覽器的下載資料夾，通常是 <b>「下載項目」</b>。</td></tr>
<tr><td>速度</td><td>尚未在 Mac 上實測；大致可參考《使用入門》第 12 節的時間。</td></tr></table>

<h3>解除安裝</h3>
<p>把 Kokoro Reader 從「應用程式」拖到垃圾桶。若要一併刪除您的工作與詞彙表，請刪除
<code>{DATA}</code> 和 <code>~/Library/Caches/KokoroReader</code>。</p>

<h3>常見問題</h3>
<table><tr><th>您看到</th><th>處理方式</th></tr>
<tr><td>「請先把 Kokoro Reader 拖到『應用程式』資料夾」</td><td>完成第 2 步，再從「應用程式」開啟。</td></tr>
<tr><td>「需要搭載 Apple 晶片的 Mac」／「需要 macOS 14」</td><td>這台 Mac 無法執行 Kokoro Reader，請改用較新的 Mac 或 Windows 版。</td></tr>
<tr><td>兩分鐘後仍沒有開啟</td><td>在瀏覽器開啟 <code>http://127.0.0.1:7860</code>。若仍無法使用，請把
<code>{DATA}/kokoro-reader.log</code> 傳給提供 Kokoro Reader 的人。</td></tr></table>
"""

if __name__ == "__main__":
    build("en-mac", "Kokoro Reader – Mac install", EN, "Kokoro Reader - Mac install.pdf")
    build("zh-mac", "Kokoro Reader – Mac 安裝說明", ZH, "Kokoro Reader - Mac 安裝說明.pdf")
