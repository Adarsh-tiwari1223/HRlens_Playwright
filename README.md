# HRlens Playwright Automation Framework

> End-to-end test automation framework for the HRlens Increment Module — built on Playwright, pytest, and a layered API-first validation strategy.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Playwright](https://img.shields.io/badge/Playwright-latest-green)
![pytest](https://img.shields.io/badge/pytest-latest-orange)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Configuration](#configuration)
- [Running Tests](#running-tests)
- [Reports](#reports)
- [Design Principles](#design-principles)
- [Future Enhancements](#future-enhancements)

---

## Tech Stack

| Tool        | Version  | Purpose              |
| ----------- | -------- | -------------------- |
| Python      | 3.9+     | Programming language |
| Playwright  | Latest   | Browser automation   |
| pytest      | Latest   | Test runner          |
| Allure      | Latest   | Test reporting       |
| Requests    | Latest   | API validation       |

---

## Architecture

This framework follows a **layered automation architecture** where the API is the source of truth and the UI is the representation layer.

```
┌─────────────────────────────────┐
│   API Layer  (Core Validation)  │  ← Calculation accuracy, business logic
├─────────────────────────────────┤
│   UI Layer   (Representation)   │  ← Rendering, display, user interactions
├─────────────────────────────────┤
│   E2E Layer  (Business Flow)    │  ← Full workflow validation
└─────────────────────────────────┘
```

---

## Project Structure

```
HRlens_Playwright/
│
├── core/
│   ├── config/
│   │   └── settings.py              # Env config, base URL, credentials
│   └── fixtures/
│       └── base_fixture.py          # Browser + page fixtures
│
├── hooks/
│   └── test_hooks.py                # pytest session hooks
│
├── pages/
│   ├── base_page.py                 # Core page actions
│   ├── common/
│   │   ├── login_page.py
│   │   └── navbar.py
│   └── modules/
│       └── increment/
│           ├── increment_page.py
│           ├── increment_summary_page.py
│           └── negotiation_page.py
│
├── locators/
│   └── modules/
│       ├── login_locators.py
│       └── increment_locators.py
│
├── utils/
│   ├── api/
│   │   ├── base_client.py           # Base HTTP client
│   │   └── increment_api.py         # Increment module API calls
│   ├── validators/
│   │   ├── assertions.py            # UI assertions
│   │   └── calculation_validator.py # Business logic validators
│   └── helpers/
│       └── common_utils.py          # Shared utilities
│
├── testdata/
│   ├── static/
│   │   └── increment_testdata.json
│   └── dynamic/                     # Runtime-generated data
│
├── tests/
│   ├── smoke/                       # Sanity checks
│   │   └── test_login.py
│   ├── regression/                  # Full UI coverage
│   │   ├── test_increment_ui.py
│   │   └── test_negotiation_flow.py
│   ├── api/                         # Backend logic tests
│   │   └── test_increment_calculation.py
│   ├── integration/                 # UI vs API cross-validation
│   │   └── test_ui_api_validation.py
│   └── e2e/                         # Full workflow tests
│       └── test_increment_full_flow.py
│
├── reports/
│   ├── html/
│   └── allure/
│
├── logs/
├── .env                             # Local secrets (not committed)
├── .gitignore
├── pytest.ini
├── requirements.txt
├── setup.bat                        # One-click setup for new members
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.9+
- Git

### Quick Start

```bash
# Clone the repository
git clone https://github.com/Adarsh-tiwari1223/HRlens_Playwright.git
cd HRlens_Playwright
```

### Windows — One-Click Setup

```bash
setup.bat
```

`setup.bat` automatically:
1. Creates a Python virtual environment (`venv`)
2. Activates the virtual environment
3. Installs all dependencies from `requirements.txt`
4. Installs Playwright browsers

### Mac/Linux — Manual Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install
```

### Environment Configuration

Create a `.env` file in the project root:

```env
BASE_URL=https://stg-hrlense.jobvritta.com
HEADLESS=False

ADMIN_USERNAME=admin@hrlens.com
ADMIN_PASSWORD=your_password
```

> `.env` is gitignored — never commit credentials.

---

## Configuration

| Variable         | Description              | Default |
| ---------------- | ------------------------ | ------- |
| `BASE_URL`       | Application base URL     | —       |
| `HEADLESS`       | Run browser headless     | `False` |
| `ADMIN_USERNAME` | Admin login email        | —       |
| `ADMIN_PASSWORD` | Admin login password     | —       |
| `ENV`            | Target environment       | `dev`   |

Switch environments:

```bash
ENV=staging pytest   # loads .env.staging
ENV=prod pytest      # loads .env.prod
```

---

## Running Tests

```bash
# All tests
pytest

# By suite
pytest tests/smoke/
pytest tests/regression/
pytest tests/api/
pytest tests/integration/
pytest tests/e2e/

# Verbose output
pytest tests/smoke/ -vs
```

---

## Reports

### HTML

```bash
pytest --html=reports/html/report.html
```

### Allure

```bash
pytest --alluredir=reports/allure
allure serve reports/allure
```

---

## Design Principles

```
API  = Source of Truth
UI   = Representation Layer
Test = Validation of both
```

| Layer       | Validates                          |
| ----------- | ---------------------------------- |
| API         | Calculation logic, data integrity  |
| UI          | Rendering, display accuracy        |
| Integration | UI value == API value              |
| E2E         | Full business workflow             |

---

## Future Enhancements

- [ ] GitHub Actions CI/CD pipeline
- [ ] Parallel test execution
- [ ] Data-driven test execution
- [ ] Docker-based execution environment
- [ ] Slack/email test result notifications
