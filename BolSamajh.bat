@echo off
rem ==============================================================================
rem BolSamajh — Direct Windows Application Launcher
rem Double-click this file to launch BolSamajh directly without typing any command.
rem ==============================================================================
cd /d "%~dp0"

if exist "venv\Scripts\pythonw.exe" (
    start "" "venv\Scripts\pythonw.exe" -m bolsamajh.main %*
) else if exist "venv\Scripts\python.exe" (
    start "" "venv\Scripts\python.exe" -m bolsamajh.main %*
) else (
    where python >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        start "" python -m bolsamajh.main %*
    ) else (
        echo [ERROR] Python not found. Please run the setup instructions in README.md.
        pause
    )
)
