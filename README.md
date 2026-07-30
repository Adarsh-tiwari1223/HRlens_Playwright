# HRlens Playwright Automation Suite

End-to-end test automation, parallel execution engine, and API validation framework for the **HRlens** platform — powered by **Playwright**, **pytest**, **pytest-xdist**, **Docker**, and a structured **Page Object Model (POM)** pattern.

![Python Version](https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python)
![Playwright Version](https://img.shields.io/badge/Playwright-1.49+-green?style=for-the-badge&logo=playwright)
![pytest](https://img.shields.io/badge/pytest-8.3+-orange?style=for-the-badge&logo=pytest)
![Docker Container](https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker)

---

## 🏗️ Architecture & Core Capabilities

* **Browser Automation**: [Playwright](https://playwright.dev/python/) for fast, reliable, and modern web testing across Chromium, Firefox, and WebKit.
* **Parallel Execution Engine (`pytest-xdist`)**: Smart multi-worker allocation engine that auto-scales test workers (`-n auto`) to execute test suites in parallel, reducing smoke suite execution time from **63s $\rightarrow$ ~22s**.
* **Prioritized Execution Engine**: Native `pytest_collection_modifyitems` hook dynamically prioritizes authentication and login tests (`test_login`) to run **FIRST** before feature tests across all suites.
* **Production-Grade Docker Containerization**: Zero-dependency execution using `mcr.microsoft.com/playwright/python:v1.49.0-jammy` with Docker Compose orchestration.
* **Strict Environment Scoping Policy**: Whitelisted environment enforcement (`ALLOWED_ENVS = {"stg", "prod"}`). Defaults to **Stage (`stg`)**; requires explicit user opt-in (`-e ENV=prod`) for Production runs.
* **Dual Marker Composition**: Flexible test suite composition blending **Execution Markers** (`smoke`, `sanity`, `regression`) with **Functional Domain Markers** (`ui`, `api`, `payroll`, `recruitment`, `attendance`).
* **CI/CD Automation & Early Warning System**: Container-optimized GitHub Actions pipelines with concurrency cancellation, trace artifact retention, and `$GITHUB_STEP_SUMMARY` execution dashboards.
* **Visual Playwright Tracing & Reports**: Automatic step-by-step DOM visual tracing (`reports/trace_*.zip`), Allure Reporting, and self-contained HTML reports (`reports/report.html`).

---

## 💎 CI-Enabled Page Object Model (POM)

The framework implements a high-performance, resilient, and **CI-Ready Page Object Model (POM)**:

* **CI-Ready Viewport Optimization**: On **Local Runs (Headed)**, browser windows maximize to match host screen resolution. On **CI/Docker Runs (Headless)**, viewports default to a high-res `1920x1080` desktop layout to keep sidebars and navigation drawers fully expanded.
* **Native Auto-Waiting Engine**: Wrapper actions in [BasePage](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/pages/base_page.py) utilize Playwright's native Actionability Checks (waiting for stable, visible, and enabled states), replacing fragile hardcoded sleep loops.
* **Auto-Recovery & Sign-In Fallback**: If a test loses session context during navigation, the engine auto-recovers by re-authenticating and navigating back to the target page without aborting the test runner.
* **Sanitized Credentials Parser**: `_get_env()` automatically strips accidental whitespace from environment secrets, preventing authentication timeouts.

---

## 📁 Project Structure

```
HRlens_Playwright/
├── docker/                           # Production Containerization Layer
│   ├── Dockerfile                    # Optimized Playwright Python base image with layer caching
│   └── compose.yaml                  # Docker Compose orchestration with bind-mounts and env policy
├── .dockerignore                     # Root build context ignore rules
├── .github/
│   └── workflows/
│       ├── playwright.yml             # Container-optimized CI workflow (Runs on push & PR)
│       └── nightly_regression.yml     # Containerized Nightly Regression workflow (12:00 AM UTC)
├── core/
│   ├── config/settings.py            # Environment whitelist, sanitized USERS dict & API URLs
│   └── base_api.py                   # REST API client with payload redaction & truncation
├── pages/                            # Page Object Model (POM) Layer
│   ├── base_page.py                  # Base class with safe action wrappers & auto-waiting
│   ├── login_page.py                 # Authentication page object
│   ├── hrlense_portal/
│   │   ├── admin_control/            # Hierarchy & management interactions
│   │   ├── attendance/               # Leave application & attendance sheets
│   │   ├── director/                 # Director document sharing page objects
│   │   ├── master/                   # Company master page objects
│   │   └── payroll/                  # Salary & payroll settings
│   └── recruitment_portal/
│       └── active_job/               # Job opening & candidate management page objects
├── workflows/                        # Reusable Business Process Workflows
│   ├── hrlense_portal/               # Leave, attendance, and increment workflows
│   └── recruitment_portal/           # End-to-end job creation & candidate onboarding workflows
├── testdata/
│   ├── dynamic/candidate_data.py     # Dynamic Faker data generator
│   └── static/                       # Static company templates & leave configs
├── tests/                            # Pytest Test Suites
│   ├── conftest.py                   # Auth prioritization, smart xdist allocation & tracing
│   ├── hrlense_portal/               # UI, API & E2E tests for HRlens portal
│   └── recruitment_portal/           # UI & E2E tests for Recruitment portal
├── .env                              # Local environment secrets (Git ignored)
├── commands.md                       # Comprehensive Docker & Pytest CLI runbook
├── pytest.ini                        # Execution & functional marker registry
├── requirements.txt                  # Locked Python dependencies (includes pytest-xdist)
└── setup.bat                         # Automated local environment setup script for Windows
```

---

## 🐳 Docker Execution (Recommended)

Run the entire automation suite inside containerized environments using Docker Desktop or Docker Engine without needing local Python or Playwright browser setups.

### Quick Start: Quiet Parallel Execution

```powershell
# Run Smoke Suite in parallel with clean output (RECOMMENDED)
docker compose --progress quiet -f docker/compose.yaml run --rm tests pytest -m smoke -n auto

# Run Sanity Suite in parallel
docker compose --progress quiet -f docker/compose.yaml run --rm tests pytest -m sanity -n auto

# Run Full Regression Suite in parallel
docker compose --progress quiet -f docker/compose.yaml run --rm tests pytest -m regression -n auto

# Force rebuild container image before test run
docker compose --progress quiet -f docker/compose.yaml run --rm --build tests pytest -m smoke -n auto
```

### Docker Execution Features:
* **`--progress quiet`**: Hides noisy Docker build output and container creation logs for crystal-clear terminal output.
* **`-n auto`**: Uses `pytest-xdist` to run tests across parallel CPU workers.
* **Smart Worker Allocation**: Automatically caps worker processes to optimize RAM & CPU startup.
* **Persisted Reports**: HTML reports (`reports/report.html`), logs (`logs/`), and Playwright trace zips (`reports/trace_*.zip`) are automatically bind-mounted to your host machine.

---

## 🛡️ Environment Execution Policy

The framework enforces strict environment scoping to protect target systems:

* **Default Target**: Always executes against **Stage (`ENV=stg`)** (`https://stg-hrlense.jobvritta.com`).
* **Development (`dev`)**: Strictly prohibited in Docker and CI/CD pipelines. Unallowed environments fall back to `stg` with a warning log.
* **Production (`prod`) Opt-in**: Requires explicit CLI user opt-in (`-e ENV=prod`):

```powershell
# Explicit Production Execution (Opt-in ONLY)
docker compose --progress quiet -f docker/compose.yaml run --rm -e ENV=prod tests pytest -m smoke
```

---

## ⚡ Local Setup & Execution

### 1. Installation

```powershell
# Windows automated setup
.\setup.bat

# Manual Setup (macOS / Linux)
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Flexible Test Commands

```powershell
# Run smoke tests in parallel
pytest -m "smoke" -n auto --disable-warnings

# Combine functional & execution markers
pytest -m "recruitment and regression"
pytest -m "ui and sanity"
pytest -m "api and not regression"

# Open Playwright Trace Viewer for failed runs
playwright show-trace reports/trace_<test_name>.zip
```

---

## 📊 Generating Reports

```powershell
# Generate self-contained HTML report
pytest -m smoke --html=reports/report.html --self-contained-html

# Serve Allure Dashboard
pytest --alluredir=reports/allure
allure serve reports/allure
```
