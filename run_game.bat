@echo off
REM Launcher for Cognitive Maze
cd /d "%~dp0"

IF EXIST ".venv\Scripts\python.exe" (
    echo Starting Cognitive Maze using virtual environment...
    .venv\Scripts\python.exe main.py
    goto end
)

where py >nul 2>nul
IF %ERRORLEVEL% EQU 0 (
    echo Starting Cognitive Maze using Python launcher...
    py -3.11 main.py || py main.py
    goto end
)

echo Starting Cognitive Maze using python...
python main.py

:end
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Game exited with error code %ERRORLEVEL%.
    pause
)
