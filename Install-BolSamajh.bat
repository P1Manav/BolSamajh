@echo off
setlocal enabledelayedexpansion
title BolSamajh - Installation Wizard

echo =================================================================
echo   BolSamajh -- Bolo. Samjho. Installation Wizard
echo   Hinglish Voice Companion for Windows
echo =================================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "INSTALL_DIR=%LOCALAPPDATA%\Programs\BolSamajh"

echo [*] Target installation directory:
echo     %INSTALL_DIR%
echo.

:: 1. Create target folder if missing
if not exist "%INSTALL_DIR%" (
    echo [*] Creating application directory...
    mkdir "%INSTALL_DIR%"
)

:: 2. If running from the unzipped release package, copy files over
if exist "%SCRIPT_DIR%_internal" (
    echo [*] Installing application binaries...
    xcopy /E /I /Y /Q "%SCRIPT_DIR%*" "%INSTALL_DIR%\" >nul
    set "EXE_PATH=%INSTALL_DIR%\BolSamajh.exe"
) else if exist "%SCRIPT_DIR%dist\BolSamajh\BolSamajh.exe" (
    echo [*] Installing built application from dist...
    xcopy /E /I /Y /Q "%SCRIPT_DIR%dist\BolSamajh\*" "%INSTALL_DIR%\" >nul
    set "EXE_PATH=%INSTALL_DIR%\BolSamajh.exe"
) else (
    echo [*] Configuring workspace portable launcher...
    set "EXE_PATH=%SCRIPT_DIR%BolSamajh.bat"
)

:: 3. Create Desktop and Start Menu Shortcuts using PowerShell
echo [*] Creating Desktop and Start Menu shortcuts...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ws = New-Object -ComObject WScript.Shell; " ^
    "$desktop = [Environment]::GetFolderPath('Desktop'); " ^
    "$startMenu = [Environment]::GetFolderPath('Programs'); " ^
    "$target = '%EXE_PATH%'; " ^
    "$workDir = Split-Path -Path $target -Parent; " ^
    "$ico = Join-Path $workDir 'assets\bolsamajh.ico'; " ^
    "if (-not (Test-Path $ico)) { $ico = Join-Path '%SCRIPT_DIR%' 'assets\bolsamajh.ico' }; " ^
    "$deskLnk = Join-Path $desktop 'BolSamajh.lnk'; " ^
    "$s1 = $ws.CreateShortcut($deskLnk); " ^
    "$s1.TargetPath = $target; " ^
    "$s1.WorkingDirectory = $workDir; " ^
    "$s1.Description = 'BolSamajh - Bolo. Samjho. Voice Companion'; " ^
    "if (Test-Path $ico) { $s1.IconLocation = $ico + ',0' }; " ^
    "$s1.Save(); " ^
    "Write-Host '[OK] Desktop shortcut created: ' $deskLnk; " ^
    "$smLnk = Join-Path $startMenu 'BolSamajh.lnk'; " ^
    "$s2 = $ws.CreateShortcut($smLnk); " ^
    "$s2.TargetPath = $target; " ^
    "$s2.WorkingDirectory = $workDir; " ^
    "$s2.Description = 'BolSamajh - Bolo. Samjho. Voice Companion'; " ^
    "if (Test-Path $ico) { $s2.IconLocation = $ico + ',0' }; " ^
    "$s2.Save(); " ^
    "Write-Host '[OK] Start Menu shortcut created: ' $smLnk;"

echo.
echo =================================================================
echo   [OK] Installation Completed Successfully!
echo   You can now launch BolSamajh from:
echo   - Your Windows Desktop (BolSamajh shortcut)
echo   - Windows Start Menu (type 'BolSamajh')
echo =================================================================
echo.

set /p LAUNCH="Do you want to launch BolSamajh now? (Y/N, default Y): "
if /i "%LAUNCH%"=="N" goto end

echo [*] Starting BolSamajh...
start "" "%EXE_PATH%"

:end
timeout /t 3 >nul
exit /b 0

