Kokoro Reader 1.1.1 for macOS
=============================

Needs: a Mac with Apple silicon (M1 or later), macOS 14 Sonoma or later, about 6 GB free disk space.
Everything runs on your Mac, offline. Nothing is uploaded.

INSTALL (once)
1. Drag "Kokoro Reader.app" into the Applications folder.
2. Open Applications and double-click Kokoro Reader.
   macOS says it cannot check the app for malware (it is not from the App Store). Click "Done".
3. Open System Settings > Privacy & Security, scroll down to
   "Kokoro Reader was blocked to protect your Mac" and click "Open Anyway", then confirm with your
   password or Touch ID.
4. Kokoro Reader starts and opens in your web browser. The first start takes up to a minute or two.
   From then on, just double-click it like any other app.

If macOS keeps refusing, open Terminal (Applications > Utilities) and paste:
   xattr -dr com.apple.quarantine "/Applications/Kokoro Reader.app"
then open Kokoro Reader again.

USING IT
Everything works as described in "Kokoro Reader - Getting Started.pdf". Differences on a Mac:
- Start: double-click Kokoro Reader in Applications (or find it with Spotlight, Cmd+Space).
  There is no Dock icon; the app lives in the browser tab.
- Stop: click "Quit" at the top of the page, or just close the tab (it stops by itself about 5 minutes later).
- Your work, the glossary and the log file are kept in
  ~/Library/Application Support/KokoroReader
  (in Finder: Go > Go to Folder..., then paste that path).
- Uninstall: drag Kokoro Reader from Applications to the Trash; optionally also delete the folder above
  and ~/Library/Caches/KokoroReader.

If something goes wrong, send ~/Library/Application Support/KokoroReader/kokoro-reader.log to the person
who gave you Kokoro Reader.


Kokoro Reader 1.1.1 macOS 版
============================

需求：搭載 Apple 晶片（M1 或更新）的 Mac、macOS 14 Sonoma 或更新版本、約 6 GB 可用空間。
所有處理都在您的 Mac 上離線完成，不會上傳任何資料。

安裝（只需一次）
1. 把「Kokoro Reader.app」拖到「應用程式」資料夾。
2. 打開「應用程式」，按兩下 Kokoro Reader。
   macOS 會說無法檢查此 App 是否含有惡意軟體（因為它不是來自 App Store），按「完成」。
3. 打開「系統設定」>「隱私權與安全性」，往下捲到
   「已阻擋 Kokoro Reader 以保護您的 Mac」，按「強制打開」，再輸入密碼或使用 Touch ID 確認。
4. Kokoro Reader 會啟動並在網頁瀏覽器中開啟。第一次啟動最多需要一兩分鐘。
   之後就像其他 App 一樣按兩下即可。

如果 macOS 仍然拒絕開啟，請打開「終端機」（應用程式 > 工具程式），貼上：
   xattr -dr com.apple.quarantine "/Applications/Kokoro Reader.app"
然後再開啟 Kokoro Reader。

使用方式
操作方式與「Kokoro Reader - 使用入門.pdf」相同。Mac 上的差異：
- 啟動：在「應用程式」中按兩下 Kokoro Reader（或用 Spotlight，Cmd+空白鍵 搜尋）。
  Dock 上不會出現圖示，程式在瀏覽器分頁中運作。
- 結束：在頁面上方按「結束」，或直接關閉分頁（約 5 分鐘後會自動停止）。
- 您的工作、詞彙表與記錄檔保存在
  ~/Library/Application Support/KokoroReader
  （在 Finder 選「前往 > 前往檔案夾…」，貼上這個路徑）。
- 解除安裝：把 Kokoro Reader 從「應用程式」拖到垃圾桶；也可以一併刪除上面的資料夾和
  ~/Library/Caches/KokoroReader。

如果發生問題，請把 ~/Library/Application Support/KokoroReader/kokoro-reader.log
傳給提供 Kokoro Reader 的人。
