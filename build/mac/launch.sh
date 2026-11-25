#!/bin/bash
# Kokoro Reader for macOS: Contents/MacOS/Kokoro Reader inside the .app bundle.
# Starts the local app in the background (the launcher opens the default browser when it is ready),
# then exits, so opening the app again while it runs simply brings the browser page back.
APP="$(cd "$(dirname "$0")/../.." && pwd)"
RES="$APP/Contents/Resources"
PY="$RES/python/bin/python3.12"

alert() {  # $1 = message (English / 繁中)
  /usr/bin/osascript -e "display dialog \"$1\" with title \"Kokoro Reader\" buttons {\"OK\"} default button 1 with icon caution" >/dev/null 2>&1
}

if [ "$(/usr/bin/uname -m)" != "arm64" ]; then
  alert "Kokoro Reader needs a Mac with Apple silicon (M1 or later).\n\nKokoro Reader 需要搭載 Apple 晶片（M1 或更新）的 Mac。"
  exit 1
fi
if [ "$(/usr/bin/sw_vers -productVersion | cut -d. -f1)" -lt 14 ]; then
  alert "Kokoro Reader needs macOS 14 Sonoma or later.\n\nKokoro Reader 需要 macOS 14 Sonoma 或更新版本。"
  exit 1
fi
case "$APP" in
  */AppTranslocation/*)
    alert "Please drag Kokoro Reader into the Applications folder first, then open it from there.\n\n請先把 Kokoro Reader 拖到「應用程式」資料夾，再從那裡開啟。"
    exit 1 ;;
esac

# Downloaded files carry a quarantine flag; once you have allowed the app, clear it from the
# bundled Python and libraries too, so macOS does not ask again for each of them.
if /usr/bin/xattr -p com.apple.quarantine "$PY" >/dev/null 2>&1; then
  /usr/bin/xattr -dr com.apple.quarantine "$APP" 2>/dev/null
fi

export PYTHONNOUSERSITE=1
export PYTHONPYCACHEPREFIX="$HOME/Library/Caches/KokoroReader/pycache"
/usr/bin/osascript -e 'display notification "Starting… the browser opens in a moment. 啟動中…瀏覽器稍後會開啟。" with title "Kokoro Reader"' >/dev/null 2>&1 &
nohup "$PY" "$RES/app/launcher.pyw" >/dev/null 2>&1 &
disown
exit 0
