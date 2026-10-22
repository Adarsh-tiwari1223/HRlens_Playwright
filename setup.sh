#!/usr/bin/env bash
set -e

echo "==================================================="
echo "Setting up HRlens Playwright Test Framework..."
echo "==================================================="

# 1. Virtual Environment
if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment (venv)..."
    python3 -m venv venv
else
    echo "[OK] Virtual environment (venv) already exists."
fi

source venv/bin/activate

# 2. Python Dependencies
echo "[*] Installing Python dependencies..."
pip install -r requirements.txt --quiet

# 3. Playwright browser
echo "[*] Installing Playwright Chromium browser..."
playwright install chromium

# 4. Environment config
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "[*] Initializing .env from .env.example..."
        cp .env.example .env
        echo "[OK] Created .env with default Stage environment settings."
    fi
else
    echo "[OK] .env configuration already present."
fi

# 5. Runtime directories
mkdir -p reports logs/hrlense_portal logs/recruitment_portal logs/general

echo ""
echo "==================================================="
echo "[SUCCESS] HRlens Playwright setup complete!"
echo "To run tests:"
echo "  1. Activate venv:   source venv/bin/activate"
echo "  2. Run smoke suite: pytest -m smoke"
echo "==================================================="
