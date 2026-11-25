// Getting started manual shown from the "Getting started" button. English and Traditional Chinese.
const WORKDIR = /Mac/.test(navigator.platform || navigator.userAgent)
  ? '~/Library/Application Support/KokoroReader' : '%LOCALAPPDATA%\\KokoroReader';
const GUIDE = {
  en: `
<div class="toc"><a href="#ge1">Start &amp; stop</a><a href="#ge2">Read a text aloud</a><a href="#ge3">Dub a video: steps 1–5</a><a href="#ge4">Review tips</a><a href="#ge5">Glossary</a><a href="#ge6">Video with an .srt</a><a href="#ge7">Problems</a></div>

<h3 id="ge1">1. Start and stop</h3>
<ol>
  <li>Open <b>Kokoro Reader</b> from the Start menu. It opens in your web browser. Everything runs on this computer; nothing is uploaded.</li>
  <li>Switch the interface between <b>EN</b> and <b>繁中</b> at the top right. Hover over any dashed label to see what a setting does.</li>
  <li>When you finish, click <b>Quit</b> (top right). If you only close the tab, the app stops by itself about 5 minutes later.</li>
</ol>

<h3 id="ge2">2. Read a text file aloud</h3>
<ol>
  <li>Click <b>Open file</b> and choose a <code>.txt</code> or <code>.md</code> file.</li>
  <li>Choose the <b>Language</b> and <b>Voice</b>, and if you like a tone, speed and pauses.</li>
  <li>Click <b>Generate</b>. The first time after starting takes 30–40 seconds longer while the voice loads.</li>
  <li>Press ▶ to listen. English highlights each word as it is spoken; Chinese highlights the sentence. Click any word to play from there.</li>
  <li>Click <b>Save audio</b> under the player.</li>
</ol>

<h3 id="ge3">3. Translate and dub a video, step by step</h3>
<p>Click <b>Open video</b>. A step bar appears: <b>1 Transcribe → 2 Translate → 3 Review → 4 Voice → 5 Export</b>. Done steps turn green ✓; locked steps 🔒 open when the step before is ready. Each step has <b>← Back</b> and <b>Next →</b>.</p>
<ol>
  <li><b>Transcribe.</b> Leave <i>Spoken language</i> on Auto, <i>Chunk length</i> on About 5 min and <i>Accuracy</i> on Best, then click <b>Start transcribing</b>. It takes about half the video's length (a 1-hour video ≈ 30 min); keep the laptop plugged in. <b>Stop</b> pauses; <b>Resume</b> carries on where it stopped.</li>
  <li><b>Translate.</b> <i>Translate to</i> Automatic turns an English video into 繁體中文 and a Chinese video into English. Choose <i>Off</i> to re-voice in the same language. Each chunk is translated as soon as it is transcribed, so you can go on while the rest runs.</li>
  <li><b>Review.</b> Check the table in the <b>Review</b> tab chunk by chunk (see 4 below). Tick ✓ for each good line, or click <b>Mark chunk reviewed</b>.</li>
  <li><b>Voice.</b> Pick the voice (defaults: <code>zm_009</code> for Chinese, <code>af_bella</code> for English). <i>Original audio</i> is <b>Replace</b>: the video's old sound is removed and only the new voice remains, so you never hear two voices. Click <b>Generate voice</b>, then watch the result in <b>Play &amp; highlight</b>.</li>
  <li><b>Export.</b> Tick what you need: the MP4 with the new voice, the voice only (WAV), the new subtitles, the original subtitles and bilingual subtitles. Click <b>Save selected</b>. Files go to your Downloads folder, named after the video.</li>
</ol>

<h3 id="ge4">4. Review tips</h3>
<ul>
  <li>Click a line to edit it. <b>Enter</b> saves, <b>Esc</b> cancels, <b>Re-translate</b> asks the translator again, <b>Undo edit</b> brings back the machine translation. Edited lines show an <span class="tag">edited</span> tag.</li>
  <li>▶ plays that line in the video so you can hear what was really said.</li>
  <li>⚠ marks are hints: <b>⤓ join</b> = the sentence continues on the next line (click to merge them); <b>long</b> = probably too long for its time slot, shorten it; <b>unsure</b> = the transcriber was not sure, listen and fix the original.</li>
  <li>Use the filters <b>⚠ Flagged</b> and <b>Not reviewed</b> to find what is left. The chunk buttons jump between parts of the video.</li>
</ul>

<h3 id="ge5">5. Glossary: teach it your words once</h3>
<ul>
  <li>Select a wrong word in the table, <b>right-click</b>, and choose <b>Add to glossary</b>. Type the right term and click <b>Add + fix this line</b> or <b>Add + re-translate all</b>.</li>
  <li>Leave the Chinese empty to keep a term in English, such as <i>FLIR Thermal Studio</i>. Terms are underlined in green in the table.</li>
  <li>The <b>Glossary</b> button lists every term, where it came from and how often it is used. You can edit, delete, <b>Import .txt</b> and <b>Export .txt</b> to share the list with colleagues.</li>
</ul>

<h3 id="ge6">6. A video that already has subtitles</h3>
<ol>
  <li>Click <b>Open file</b> and choose the <code>.srt</code> file. Step 1 is skipped and you start at step 2.</li>
  <li>Click <b>Open video</b> and choose the matching video, so step 5 can make the MP4.</li>
  <li>Continue with steps 2–5 as above.</li>
</ol>
<p class="note">Your work is kept in <code>${WORKDIR}</code> until you save it. The glossary is kept there too.</p>

<h3 id="ge7">7. If something goes wrong</h3>
<ul>
  <li><b>"Windows protected your PC"</b> when installing: More info → Run anyway.</li>
  <li><b>Nothing seems to happen</b> after Start transcribing or Generate: the first load takes up to a minute; watch the progress text.</li>
  <li><b>The page says the app has stopped</b>: open Kokoro Reader from the Start menu again.</li>
  <li><b>The voice runs late</b> on some lines: shorten those translations in step 3, or raise Max speed-up in step 4.</li>
</ul>`,

  zh: `
<div class="toc"><a href="#gz1">啟動與結束</a><a href="#gz2">朗讀文字</a><a href="#gz3">影片配音：第 1–5 步</a><a href="#gz4">校對技巧</a><a href="#gz5">詞彙表</a><a href="#gz6">已有字幕的影片</a><a href="#gz7">常見問題</a></div>

<h3 id="gz1">1. 啟動與結束</h3>
<ol>
  <li>從「開始」功能表開啟 <b>Kokoro Reader</b>，程式會在瀏覽器中開啟。所有處理都在這台電腦上完成，不會上傳任何檔案。</li>
  <li>右上角可切換介面為 <b>EN</b> 或 <b>繁中</b>。滑鼠停在虛線標籤上可看到設定說明。</li>
  <li>使用完畢請按右上角的 <b>結束</b>。若只關閉分頁，程式約 5 分鐘後會自動結束。</li>
</ol>

<h3 id="gz2">2. 朗讀文字檔</h3>
<ol>
  <li>按 <b>開啟檔案</b>，選擇 <code>.txt</code> 或 <code>.md</code> 檔。</li>
  <li>選擇 <b>語言</b> 與 <b>聲音</b>，也可以調整語氣、語速和停頓。</li>
  <li>按 <b>產生</b>。每次啟動後第一次產生會多花 30–40 秒載入聲音。</li>
  <li>按 ▶ 播放。英文會逐字標示，中文以整句標示；點選任何字即可從該處播放。</li>
  <li>按播放器下方的 <b>儲存音訊</b>。</li>
</ol>

<h3 id="gz3">3. 依步驟翻譯並配音影片</h3>
<p>按 <b>開啟影片</b> 後會出現步驟列：<b>1 轉錄 → 2 翻譯 → 3 校對 → 4 配音 → 5 匯出</b>。完成的步驟會變成綠色 ✓；上鎖的步驟 🔒 會在前一步完成後開放。每一步都有 <b>← 上一步</b> 和 <b>下一步 →</b>。</p>
<ol>
  <li><b>轉錄。</b><i>影片語言</i> 保持「自動偵測」、<i>分段長度</i> 選「約 5 分鐘」、<i>準確度</i> 選「最佳」，再按 <b>開始轉錄</b>。所需時間約為影片長度的一半（1 小時影片約 30 分鐘），請接上電源。<b>停止</b> 可暫停，<b>繼續</b> 會從中斷處接著做。</li>
  <li><b>翻譯。</b><i>翻譯成</i> 選「自動」時，英文影片會翻成繁體中文、中文影片會翻成英文；選「關閉」則以同一語言重新配音。每段轉錄完成就會立刻翻譯，其餘段落進行時您就可以繼續下一步。</li>
  <li><b>校對。</b>在 <b>校對</b> 分頁逐段檢查表格（見下方第 4 點）。每一行確認後勾選 ✓，或按 <b>標記本段已校對</b>。</li>
  <li><b>配音。</b>選擇聲音（預設：中文 <code>zm_009</code>、英文 <code>af_bella</code>）。<i>原始音訊</i> 預設為 <b>取代</b>：移除影片原本的聲音，只保留新配音，不會同時聽到兩個聲音。按 <b>產生配音</b>，再到 <b>播放與標示</b> 分頁觀看成果。</li>
  <li><b>匯出。</b>勾選需要的檔案：換上新配音的 MP4、只有配音的 WAV、新字幕、原文字幕和雙語字幕，再按 <b>儲存已勾選</b>。檔案會以影片名稱命名，存到「下載」資料夾。</li>
</ol>

<h3 id="gz4">4. 校對技巧</h3>
<ul>
  <li>點選一行即可修改。<b>Enter</b> 儲存、<b>Esc</b> 取消；<b>重新翻譯</b> 會請翻譯器再翻一次；<b>復原修改</b> 會還原機器翻譯。修改過的行會顯示 <span class="tag">已修改</span>。</li>
  <li>▶ 會在影片中播放這一行，方便確認實際說了什麼。</li>
  <li>⚠ 只是提示：<b>⤓ 合併</b>＝句子延續到下一行（點選即可合併）；<b>太長</b>＝可能超出時間，請精簡；<b>不確定</b>＝轉錄時不太確定，請聆聽並修正原文。</li>
  <li>用 <b>⚠ 標記</b> 和 <b>未校對</b> 篩選尚未處理的行；段落按鈕可在影片各段之間切換。</li>
</ul>

<h3 id="gz5">5. 詞彙表：教一次就記住</h3>
<ul>
  <li>在表格中選取翻錯的字詞，按 <b>右鍵</b> 並選 <b>加入詞彙表</b>。輸入正確譯法後，按 <b>加入並修正這一行</b> 或 <b>加入並重新翻譯全部</b>。</li>
  <li>中文留空表示保留英文原詞，例如 <i>FLIR Thermal Studio</i>。詞彙表中的詞在表格裡會有綠色底線。</li>
  <li><b>詞彙表</b> 按鈕會列出所有詞彙、來源和使用次數。可以編輯、刪除，也可以 <b>匯入 .txt</b> 和 <b>匯出 .txt</b> 與同事共用。</li>
</ul>

<h3 id="gz6">6. 已有字幕檔的影片</h3>
<ol>
  <li>按 <b>開啟檔案</b> 選擇 <code>.srt</code> 字幕檔，會略過第 1 步，直接從第 2 步開始。</li>
  <li>按 <b>開啟影片</b> 選擇對應的影片，第 5 步才能產生 MP4。</li>
  <li>接著依上方說明完成第 2–5 步。</li>
</ol>
<p class="note">儲存之前，您的工作會保存在 <code>${WORKDIR}</code>，詞彙表也存在這裡。</p>

<h3 id="gz7">7. 常見問題</h3>
<ul>
  <li>安裝時出現 <b>「Windows 已保護您的電腦」</b>：按「其他資訊」→「仍要執行」。</li>
  <li>按 <b>開始轉錄</b> 或 <b>產生</b> 後 <b>好像沒有反應</b>：第一次載入最多約 1 分鐘，請看進度文字。</li>
  <li><b>頁面顯示程式已停止</b>：從「開始」功能表重新開啟 Kokoro Reader。</li>
  <li><b>部分行的配音延遲</b>：在第 3 步精簡這些譯文，或在第 4 步提高「最高加速」。</li>
</ul>`,
};
