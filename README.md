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
│   └── config/settings.py        # Env config, credentials, USERS, APPROVERS maps
├── pages/
│   ├── base_page.py              # Core page actions with logging
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
│   ├── api/
│   │   ├── base_api.py           # get/post/put, token cache, logging
│   │   ├── leave_api.py          # apply_leave, reject_leave, get_pending_leaves, get_my_leaves
│   │   └── increment_api.py      # increment settings endpoints
│   ├── auto_healer.py            # AI-powered test self-healing
│   └── helpers.py
├── testdata/
│   └── static/                   # JSON test data
├── tests/
│   ├── conftest.py               # browser, page, logged_in_page fixtures
│   ├── test_login.py
│   ├── test_leave.py
│   ├── test_leave_api.py         # Leave API tests
│   ├── test_regularization.py
│   ├── test_hr_lens_auth.py
│   ├── test_increment.py
│   ├── test_negotiation.py
│   └── test_e2e_workflow.py
├── specs/                        # Test plans and specs
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
DEFAULT_TIMEOUT=10000

# Leave offsets
LEAVE_FROM_OFFSET=10        # future leave: today + N days
LEAVE_TO_OFFSET=1           # leave duration in days
LEAVE_BACK_DATE_OFFSET=1    # back date leave: today - N days

# Default employee for leave tests
EMPLOYEE_USER=adarsh_tiwari

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
ADARSH_TIWARI=<username>
ADARSH_TIWARI_PASSWORD=<your_password>
```

---

## Running Tests

Tests are categorized using pytest markers, not folders.

```bash
pytest tests/ -m smoke
pytest tests/ -m regression
pytest tests/ -m e2e
pytest tests/ -m api
pytest tests/ -m "smoke or regression"
pytest tests/                          # run everything
```

With live logs:
```bash
pytest tests/ -m api -v --log-cli-level=INFO
```

---

## API Tests — Leave Module

`tests/test_leave_api.py` covers the full leave workflow:

| Test | Description |
| ---- | ----------- |
| `test_apply_leave_response_is_dict` | Apply leave returns a dict |
| `test_apply_leave_has_message` | Response contains message/status |
| `test_apply_duplicate_leave` | Duplicate leave returns expected message |
| `test_apply_leave_invalid_token` | Invalid token returns 401/403 |
| `test_apply_leave_missing_payload` | Empty payload returns 400/422 |
| `test_pending_leave_data_is_valid` | Pending leave has required fields |
| `test_reject_leave_by_approver` | Approver rejects leave via PUT |
| `test_apply_back_date_leave` | Apply leave for yesterday (today - `LEAVE_BACK_DATE_OFFSET`) |

### Fixture Dependency Chain

```
leave_dates / back_leave_dates
       ↓
leave_response / back_leave_response   ← applies leave as EMPLOYEE_USER
       ↓
pending_leave                          ← reads approvalManager from employee's own list
       ↓                                 maps to APPROVERS → fetches approver's queue
test_reject_leave_by_approver          ← rejects matched leave via PUT
```

### Run only leave API tests

```bash
pytest tests/test_leave_api.py -m api -v --log-cli-level=INFO
```

### Run only back date test

```bash
pytest tests/test_leave_api.py::test_apply_back_date_leave -v --log-cli-level=INFO
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
