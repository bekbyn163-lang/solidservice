@echo off
title Stadlinjen AB - Lead-motor
cd /d "%~dp0"
echo ============================================
echo   Stadlinjen AB - Lead-motor startar...
echo ============================================
pip install flask -q 2>nul
python app.py
pause
