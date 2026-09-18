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
echo [4/4] Synchronizing runtime assets and database folders...
xcopy /E /I /Y "assets" "dist\CognitivePlay\assets" >nul
xcopy /E /I /Y "db" "dist\CognitivePlay\db" >nul
xcopy /E /I /Y "datasets" "dist\CognitivePlay\datasets" >nul

echo.
echo [5/5] Creating Desktop Shortcut...
powershell -Command "$desktop = [Environment]::GetFolderPath('Desktop'); $exe = (Resolve-Path 'dist\CognitivePlay\CognitivePlay.exe').Path; $dir = (Resolve-Path 'dist\CognitivePlay').Path; $lnk = Join-Path $desktop 'CognitivePlay.lnk'; $ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut($lnk); $s.TargetPath = $exe; $s.WorkingDirectory = $dir; $s.Description = 'Cognitive Quest 2D - Educational Math Adventure'; $s.Save(); Write-Host '[OK] Shortcut created at:' $lnk"

echo.
echo ==============================================================================
echo [SUCCESS] CognitivePlay.exe built successfully!
echo Executable located at: dist\CognitivePlay\CognitivePlay.exe
echo Desktop shortcut created: CognitivePlay.lnk
echo ==============================================================================
echo.
pause
