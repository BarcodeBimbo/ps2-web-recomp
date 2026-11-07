@echo off
cd /d "%~dp0"
set "PATH=%~dp0runtime-deps;%~dp0tools\msys64\clang64\bin;%~dp0third_party\wgpu-native\lib;%PATH%"
if exist "%~dp0Setup.cmd" (
  call "%~dp0Setup.cmd"
  exit /b %ERRORLEVEL%
)
echo Setup.cmd missing
exit /b 1
