@echo off
rem ==============================================================================
rem AgentFeed Desktop Launcher (Windows)
rem ==============================================================================
cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

python desktop.py
pause
