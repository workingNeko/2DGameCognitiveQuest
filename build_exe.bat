@echo off
REM ============================================================
REM Build Script for Cognitive Maze Standalone Executable
REM ============================================================

cd /d "%~dp0"
echo ============================================================
echo   Building Cognitive Maze Windows Executable
echo ============================================================
echo.

REM 1. Check if PyInstaller is available
where pyinstaller >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] PyInstaller is not installed or not in PATH!
    echo Please install it by running: pip install pyinstaller
    pause
    exit /b 1
)

REM 2. Clean previous build artifacts
echo [1/3] Cleaning previous build folders...
if exist "dist\CognitiveMaze" rmdir /s /q "dist\CognitiveMaze"
if exist "build\CognitiveMaze" rmdir /s /q "build\CognitiveMaze"

REM 3. Run PyInstaller build
echo [2/3] Compiling Cognitive Maze using CognitiveMaze.spec...
pyinstaller --clean -y CognitiveMaze.spec

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] PyInstaller build failed! Check errors above.
    pause
    exit /b 1
)

REM 4. Complete
echo.
echo [3/3] Build completed successfully!
echo.
echo Executable folder created at: dist\CognitiveMaze\
echo You can run: dist\CognitiveMaze\CognitiveMaze.exe
echo.
echo ============================================================
pause
