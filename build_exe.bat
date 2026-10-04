@echo off
REM ==============================================================================
REM Build Executable for Cognitive Play using PyInstaller
REM ==============================================================================
cd /d "%~dp0"

echo [1/3] Detecting Python environment...
set "PYTHON_EXE="

if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
    echo Using virtual environment Python: .venv\Scripts\python.exe
) else (
    where py >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        set "PYTHON_EXE=py -3.11"
        echo Using Python launcher: py -3.11
    ) else (
        set "PYTHON_EXE=python"
        echo Using system Python: python
    )
)

echo.
echo [2/3] Checking PyInstaller...
%PYTHON_EXE% -m pip show pyinstaller >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo PyInstaller not found. Installing PyInstaller...
    %PYTHON_EXE% -m pip install pyinstaller
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to install PyInstaller.
        pause
        exit /b 1
    )
)

echo.
echo [3/3] Compiling CognitivePlay.exe with PyInstaller...
%PYTHON_EXE% -m PyInstaller --clean -y CognitivePlay.spec

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Build failed with error code %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [4/4] Deploying standalone game to Desktop\Cognitive Maze and creating shortcut...
powershell -ExecutionPolicy Bypass -File .\deploy_desktop.ps1
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Deployment to Desktop failed with error code %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ==============================================================================
echo [SUCCESS] Cognitive Maze standalone executable ready!
echo Output folder: %USERPROFILE%\Desktop\Cognitive Maze
echo Executable:    %USERPROFILE%\Desktop\Cognitive Maze\CognitiveMaze.exe
echo Desktop link:  %USERPROFILE%\Desktop\Cognitive Maze.lnk
echo ==============================================================================
echo.
pause
