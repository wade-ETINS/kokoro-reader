@echo off
rem Drag one or more video/audio files onto this file.
rem For each file it writes, next to the video:
rem   <name>.srt         subtitles in the spoken language (faster-whisper, local)
rem   <name>.zh-TW.srt   or <name>.en.srt  translated subtitles (Opus-MT, local)
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set HF_HUB_DISABLE_SYMLINKS_WARNING=1
set HF_HUB_OFFLINE=1
set PY=.venv\Scripts\python.exe

if "%~1"=="" (
  echo.
  echo  Drag one or more video files onto "Video to SRT.bat".
  echo  Or run:  "Video to SRT.bat" "C:\path\video.mp4"
  echo.
  pause
  exit /b
)

:next
if "%~1"=="" goto done
echo.
echo ==== %~nx1
echo [1/2] Transcribing (about half the video length)...
%PY% transcribe.py "%~1" --lang auto 2>"%TEMP%\video-to-srt-error.log"
if errorlevel 1 (
  echo   Transcription failed. Details: %TEMP%\video-to-srt-error.log
  shift
  goto next
)
echo [2/2] Translating...
%PY% translate_srt.py "%~dpn1.srt" --to auto 2>"%TEMP%\video-to-srt-error.log"
if errorlevel 1 echo   Translation failed. Details: %TEMP%\video-to-srt-error.log
shift
goto next

:done
echo.
echo All done. The .srt files are next to your videos.
pause
