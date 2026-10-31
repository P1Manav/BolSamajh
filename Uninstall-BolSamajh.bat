@echo off
setlocal enabledelayedexpansion
title BolSamajh - Uninstaller

echo =================================================================
echo   BolSamajh -- Uninstallation Wizard
echo =================================================================
echo.

set "INSTALL_DIR=%LOCALAPPDATA%\Programs\BolSamajh"
set "DATA_DIR=%LOCALAPPDATA%\BolSamajh"

echo [*] Stopping running BolSamajh processes...
taskkill /F /IM BolSamajh.exe >nul 2>&1

echo [*] Removing desktop shortcuts...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$desktop = [Environment]::GetFolderPath('Desktop'); " ^
    "$startMenu = [Environment]::GetFolderPath('Programs'); " ^
    "$deskLnk = Join-Path $desktop 'BolSamajh.lnk'; " ^
    "$smLnk = Join-Path $startMenu 'BolSamajh.lnk'; " ^
    "if (Test-Path $deskLnk) { Remove-Item $deskLnk -Force; Write-Host '[OK] Removed Desktop shortcut.' }; " ^
    "if (Test-Path $smLnk) { Remove-Item $smLnk -Force; Write-Host '[OK] Removed Start Menu shortcut.' };"

if exist "%INSTALL_DIR%" (
    echo [*] Removing application files from %INSTALL_DIR%...
    rmdir /S /Q "%INSTALL_DIR%"
    echo [OK] Removed application directory.
)

if exist "%DATA_DIR%\runtime.json" (
    del /F /Q "%DATA_DIR%\runtime.json" >nul 2>&1
)

echo.
echo =================================================================
echo   [OK] BolSamajh has been cleanly uninstalled from this computer.
echo =================================================================
pause

