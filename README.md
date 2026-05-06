# HRlens Playwright

End-to-end test automation for the HRlens platform — Playwright + pytest + API validation.

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![Playwright](https://img.shields.io/badge/Playwright-1.49.0-green)
![pytest](https://img.shields.io/badge/pytest-8.3.5-orange)

---

## Tech Stack

| Tool        | Purpose            |
| ----------- | ------------------ |
| Python 3.12 | Language           |
| Playwright  | Browser automation |
| pytest      | Test runner        |
| Allure      | Reporting          |
| Requests    | API validation     |

---

## Project Structure

```
HRlens_Playwright/
├── core/
│   └── config/settings.py          # Env config, credentials, timeouts
├── pages/
│   ├── base_page.py                # Core page actions with logging
│   ├── login_page.py
│   ├── attendance/
│   │   ├── leave_page.py
│   │   └── regularization_page.py
│   ├── employee/
│   │   └── employee_page.py
│   └── increment/
│       ├── increment_page.py
│       └── negotiation_page.py
├── utils/
│   ├── api_client.py               # API calls with token caching
│   ├── auto_healer.py              # AI-powered test self-healing
│   └── helpers.py                  # load_test_data
├── testdata/
│   └── static/                     # JSON test data
├── tests/
│   ├── conftest.py                 # browser, page, logged_in_page fixtures
│   ├── test_login.py
│   ├── test_leave.py
│   ├── test_regularization.py
│   ├── test_hr_lens_auth.py
│   ├── test_increment.py
│   ├── test_negotiation.py
│   └── test_e2e_workflow.py
├── .env                            # Local secrets (not committed)
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
py -3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Add a `.env` file in the root:
```env
BASE_URL=https://stg-hrlense.jobvritta.com
API_BASE_URL=https://audit.jobvritta.com/api
HEADLESS=False
DEFAULT_TIMEOUT=60000
EMPLOYEE_USER=sanidhy
LEAVE_FROM_OFFSET=1
LEAVE_TO_OFFSET=1

# Admin
ADMIN_USERNAME=admin@hrlens.com
ADMIN_PASSWORD=<your_password>

# Branch Head
VIVEK_USERNAME=<username>
VIVEK_PASSWORD=<your_password>

# HR Manager
TEJASWINI=<username>
TEJSWINI_PASSWORD=<your_password>
SHIVA=<username>
SHIVA_PASSWORD=<your_password>

# Employees
SANIDHY_USERNAME=<username>
SANIDHY_PASSWORD=<your_password>
KUMAR_PIYUSH_USERNAME=<username>
KUMAR_PIYUSH_PASSWORD=<your_password>
RITESH_SINGH_USERNAME=<username>
RITESH_SINGH_PASSWORD=<your_password>
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

# Trace viewer (opens automatically after test run)
playwright show-trace reports/trace_<name>.zip
```

---

## Design Principle

```
API = Source of Truth
UI  = Representation Layer
```

| Layer | Validates                         |
| ----- | --------------------------------- |
| API   | Calculation logic, data integrity |
| UI    | Rendering, display accuracy       |
| E2E   | Full business workflow            |
