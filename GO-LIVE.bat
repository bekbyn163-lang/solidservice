@echo off
title Stadlinjen AB - LIVE
cd /d "%~dp0"
echo ============================================================
echo   STADLINJEN AB - startar sajten LIVE pa internet...
echo ============================================================
echo.
pip install flask -q 2>nul

REM Starta servern i eget fonster
start "Stadlinjen server" /min cmd /c "python app.py"

REM Vanta tills servern svarar
echo Startar server...
timeout /t 4 /nobreak >nul

echo.
echo Skapar publik live-lank (cloudflared)...
echo --> Din publika adress visas nedan som https://....trycloudflare.com
echo --> Dela den lanken / lagg in den dar kunder ser den.
echo --> Lat detta fonster vara oppet sa lange du vill vara live.
echo.
cloudflared.exe tunnel --url http://localhost:8810 --no-autoupdate
pause
