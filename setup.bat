@echo off
echo Setting up HRlens Playwright...

python -m venv venv
call venv\Scripts\activate

pip install -r requirements.txt
playwright install

echo.
echo Setup complete. Run: venv\Scripts\activate
pause
