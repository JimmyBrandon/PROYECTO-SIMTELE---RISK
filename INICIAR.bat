@echo off
cd /d "%~dp0"
py -3 server.py --open-browser
if errorlevel 1 pause
