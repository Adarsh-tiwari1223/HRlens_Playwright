# HRlens Playwright

End-to-end test automation for the HRlens Increment Module — Playwright + pytest + API validation.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Playwright](https://img.shields.io/badge/Playwright-latest-green)
![pytest](https://img.shields.io/badge/pytest-latest-orange)

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
│   ├── config/settings.py        # Env config, credentials
│   └── fixtures/base_fixture.py  # Browser + page fixtures
├── pages/
│   ├── base_page.py              # Core page actions
│   ├── login_page.py
│   └── increment/
│       ├── increment_page.py
│       └── negotiation_page.py
├── utils/
│   ├── api_client.py             # API calls
│   ├── assertions.py             # UI assertions
│   └── helpers.py                # Shared utilities
├── testdata/
│   └── static/                   # JSON test data
├── tests/
│   ├── smoke/
│   ├── regression/
│   └── e2e/
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
HEADLESS=False
ADMIN_USERNAME=admin@hrlens.com
ADMIN_PASSWORD=your_password
```

---

## Running Tests

```bash
pytest tests/smoke/
pytest tests/regression/
pytest tests/e2e/
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
