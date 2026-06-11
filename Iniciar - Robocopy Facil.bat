@echo off
rem Abre o Robocopy Facil (interface grafica)
start "" powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -WindowStyle Hidden -File "%~dp0RobocopyFacil.ps1"
