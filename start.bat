@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
set "launcher_result=%ERRORLEVEL%"
if not "%launcher_result%"=="0" if not defined DEMO_NO_BROWSER pause
exit /b %launcher_result%
