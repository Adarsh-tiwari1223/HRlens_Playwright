# HRlens Playwright

End-to-end test automation for the HRlens Increment Module — Playwright + pytest + API validation.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Playwright](https://img.shields.io/badge/Playwright-1.49.0-green)
![pytest](https://img.shields.io/badge/pytest-8.2.2-orange)

---

## Tech Stack

| Tool        | Purpose            |
| ----------- | ------------------ |
| Python 3.9+ | Language           |
| Playwright  | Browser automation |
| pytest      | Test runner        |
| Allure      | Reporting          |
| Requests    | API validation     |

---

## Project Structure

```
HRlens_Playwright/
├── core/
│   └── config/settings.py        # Env config, credentials
├── pages/
│   ├── base_page.py              # Core page actions
│   ├── login_page.py
│   └── increment/
│       ├── increment_page.py
│       └── negotiation_page.py
├── utils/
│   ├── api_client.py             # API calls
│   └── helpers.py                # load_test_data
├── testdata/
│   └── static/                   # JSON test data
├── tests/
│   ├── conftest.py               # browser + page fixtures
│   └── test_login.py
├── .env                          # Local secrets (not committed)
├── pytest.ini
├── requirements.txt
└── setup.bat
```

---

## Setup

```bash
git clone https://github.com/Adarsh-tiwari1223/HRlens_Playwright.git
cd HRlens_Playwright
```

**Windows** — run `setup.bat` (creates venv, installs dependencies, installs browsers)

**Mac/Linux**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install
```

Add a `.env` file in the root:
```env
BASE_URL=https://stg-hrlense.jobvritta.com
API_BASE_URL=https://audit.jobvritta.com/api
HEADLESS=False
ADMIN_USERNAME=admin@hrlens.com
ADMIN_PASSWORD=<your_password>
```

---

## Running Tests

Tests are categorized using pytest markers, not folders.

```bash
pytest tests/ -m smoke
pytest tests/ -m regression
pytest tests/ -m e2e
pytest tests/ -m "smoke or regression"
pytest tests/                          # run everything
```

---

## Reports

```bash
# HTML
pytest --html=reports/html/report.html

# Allure
pytest --alluredir=reports/allure
allure serve reports/allure
```

---

## Design Principle

```
API = Source of Truth
UI  = Representation Layer
```

| Layer      | Validates                         |
| ---------- | --------------------------------- |
| API        | Calculation logic, data integrity |
| UI         | Rendering, display accuracy       |
| E2E        | Full business workflow            |
