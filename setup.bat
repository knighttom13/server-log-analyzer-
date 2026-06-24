@echo off
chcp 65001 >nul 2>&1
setlocal

title AI-OPS Environment Setup

echo ==========================================
echo   AI-OPS Environment Setup
echo ==========================================
echo.

REM -- 1. Check Python --
echo [1/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    echo.
    echo   Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo [OK] Python %%v

REM -- 2. Create virtual environment --
echo.
echo [2/3] Creating virtual environment...
if exist "%~dp0venv" (
    echo [SKIP] venv already exists, skipping
) else (
    python -m venv "%~dp0venv"
    if errorlevel 1 (
        echo [ERROR] Failed to create venv
        pause
        exit /b 1
    )
    echo [OK] venv created
)

REM -- 3. Install dependencies --
echo.
echo [3/3] Installing Python dependencies...
call "%~dp0venv\Scripts\activate.bat"
pip install -r "%~dp0requirements.txt" -q
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies. Check your network.
    pause
    exit /b 1
)
echo [OK] Dependencies installed

REM -- Check .env --
echo.
if not exist "%~dp0.env" (
    echo [WARN] .env not found, copying from template...
    copy "%~dp0.env.example" "%~dp0.env" >nul
    echo [TODO] Please edit .env to add your DeepSeek API Key and email config
) else (
    echo [INFO] .env exists, skipping
)

echo.
echo ==========================================
echo   Setup complete!
echo   Edit .env to configure API Key
echo   Then run run.bat to start the project
echo ==========================================
pause
