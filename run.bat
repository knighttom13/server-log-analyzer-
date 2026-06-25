@echo off
set HTTP_PROXY=
set HTTPS_PROXY=
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

REM ============================================
REM Server Log Intelligent Analyzer - Launcher
REM Auto-detect Docker Desktop / Podman
REM ============================================

echo ==========================================
echo   Server Log Intelligent Analyzer
echo ==========================================
echo.

REM Clear proxy settings to avoid pull failures
if defined HTTP_PROXY (
    echo [INFO] Clearing proxy settings...
    set HTTP_PROXY=
    set HTTPS_PROXY=
    set ALL_PROXY=
)
set NO_PROXY=localhost,127.0.0.1,10.0.0.0/8,192.168.0.0/16

REM Detect container runtime: prefer Podman, fallback to Docker
set CONTAINER_CMD=
set COMPOSE_CMD=

REM
where podman >nul 2>&1
if !errorlevel! equ 0 (
    podman info >nul 2>&1
    if !errorlevel! equ 0 (
        set CONTAINER_CMD=podman
        goto :check_compose
    )
)

REM
for %%p in (
    "%ProgramFiles%\RedHat\Podman"
    "%LOCALAPPDATA%\Programs\Podman"
    "%ProgramFiles%\Podman"
    "%USERPROFILE%\scoop\apps\podman\current"
    "C:\tools\Podman"
) do (
    if exist "%%~p\podman.exe" (
        set "PATH=%%~p;%PATH%"
        podman info >nul 2>&1
        if !errorlevel! equ 0 (
            set CONTAINER_CMD=podman
            goto :check_compose
        )
    )
)

REM Check Docker
docker version >nul 2>&1
if !errorlevel! equ 0 (
    set CONTAINER_CMD=docker
    goto :check_compose
)

echo [ERROR] Neither Docker nor Podman found. Please install and start a container runtime.
pause
exit /b 1

:check_compose
REM Detect compose command
if "!CONTAINER_CMD!"=="docker" (
    docker compose version >nul 2>&1
    if !errorlevel! equ 0 (
        set "COMPOSE_CMD=docker compose"
        goto :compose_done
    )
    docker-compose --version >nul 2>&1
    if !errorlevel! equ 0 (
        set "COMPOSE_CMD=docker-compose"
        goto :compose_done
    )
) else (
    if exist "%~dp0venv\Scripts\python.exe" (
        "%~dp0venv\Scripts\python.exe" -m podman_compose --version >nul 2>&1
        if !errorlevel! equ 0 (
            set "COMPOSE_CMD=%~dp0venv\Scripts\python.exe -m podman_compose"
            goto :compose_done
        )
    )
    set "COMPOSE_CMD=podman compose"
)

:compose_done
if "!COMPOSE_CMD!"=="" (
    echo [ERROR] No compose tool found. Please install docker-compose or podman-compose.
    pause
    exit /b 1
)

echo [INFO] Detected: !CONTAINER_CMD! + !COMPOSE_CMD!
echo.

REM Clean up any conflicting networks from previous runs
echo [1/4] Preparing container environment...
cd /d "%~dp0docker"
!CONTAINER_CMD! network rm -f log-analyzer-net docker_log-analyzer-net 2>nul

echo Starting containers...
!COMPOSE_CMD! up -d --force-recreate
if !errorlevel! neq 0 (
    echo [ERROR] Container startup failed. Please check if !CONTAINER_CMD! is running.
    pause
    exit /b 1
)
echo [OK] Containers running

REM Ensure nginx has fresh config
!CONTAINER_CMD! exec log-analyzer-nginx nginx -s reload 2>nul

REM Wait for containers to be ready
echo [2/4] Waiting for containers to be ready...
timeout /t 10 /nobreak >nul

REM Activate venv (run setup.bat first if missing)
echo [3/4] Activating Python virtual environment...
if not exist "%~dp0venv\Scripts\activate.bat" (
    echo [ERROR] venv not found. Please run setup.bat first.
    pause
    exit /b 1
)
call "%~dp0venv\Scripts\activate.bat"
echo [OK] venv activated

REM Start Streamlit dashboard
echo [4/4] Starting Streamlit dashboard...
cd /d "%~dp0src"
start http://localhost:8501
streamlit run app.py

pause
