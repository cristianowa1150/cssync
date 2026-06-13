@echo off
rem Abre o CSSync (interface grafica)
start "" powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -WindowStyle Hidden -File "%~dp0CSSync.ps1"
