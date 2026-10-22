@echo off
setlocal enabledelayedexpansion
echo ===================================================
echo Setting up HRlens Playwright Test Framework...
echo ===================================================

:: 1. Initialize Virtual Environment
if not exist venv (
    echo [*] Creating Python virtual environment (venv)...
    python -m venv venv
) else (
    echo [OK] Virtual environment (venv) already exists.
)

call venv\Scripts\activate

:: 2. Install Python Dependencies
echo [*] Installing requirements...
pip install -r requirements.txt --quiet

:: 3. Install Playwright Browsers
echo [*] Installing Playwright Chromium browser...
playwright install chromium

:: 4. Auto-setup .env configuration if missing
if not exist .env (
    if exist .env.example (
        echo [*] Initializing .env configuration from .env.example...
        copy .env.example .env >nul
        echo [OK] Created .env with default Stage environment settings.
    ) else (
        echo [!] Warning: .env.example not found.
    )
) else (
    echo [OK] .env configuration already present.
)

:: 5. Create required runtime directories
if not exist reports mkdir reports
if not exist logs mkdir logs
if not exist logs\hrlense_portal mkdir logs\hrlense_portal
if not exist logs\recruitment_portal mkdir logs\recruitment_portal
if not exist logs\general mkdir logs\general

echo.
echo ===================================================
echo [SUCCESS] HRlens Playwright setup complete!
echo To run tests:
echo   1. Activate venv:   venv\Scripts\activate
echo   2. Run smoke suite: pytest -m smoke
echo ===================================================
pause
