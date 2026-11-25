@echo off
rem Starts Kokoro Reader and opens it in your browser. Close this window to stop it.
cd /d "%~dp0"
title Kokoro Reader
".venv\Scripts\python.exe" "app\server.py"
pause
