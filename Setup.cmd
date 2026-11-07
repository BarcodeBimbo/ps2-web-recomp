@echo off
setlocal
cd /d "%~dp0"
title CyberArcade - Setup and Host
echo CyberArcade - setup and host
echo Keep this window open while playing.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup-windows.ps1"
set "PS2_RESULT=%errorlevel%"
if not "%PS2_RESULT%"=="0" (
 echo.
 echo Setup or host stopped with error %PS2_RESULT%. Check the message above and tools\setup-report.json.
 pause
)
exit /b %PS2_RESULT%
