# HRlens Playwright Automation Framework

Enterprise-grade end-to-end test automation, parallel execution engine, and API validation framework for the **HRlens** and **Recruitment** platforms — powered by **Playwright**, **pytest**, **pytest-xdist**, **Docker**, and a structured **3-Tier Architecture (Page Object Model $\rightarrow$ Workflow Layer $\rightarrow$ Test Suites)**.

![Python Version](https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python)
![Playwright Version](https://img.shields.io/badge/Playwright-1.49+-green?style=for-the-badge&logo=playwright)
![pytest](https://img.shields.io/badge/pytest-8.3+-orange?style=for-the-badge&logo=pytest)
![Docker Container](https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker)

---

## 🏗️ Architecture & Core Capabilities

* **3-Tier Architecture**:
  1. **Page Object Model (`pages/`)**: Encapsulates raw DOM locators, actionability checks, and UI interactions with zero hardcoded sleeps.
  2. **Workflow Layer (`workflows/`)**: Orchestrates complex multi-step business logic (e.g. Job Creation, Candidate Pipeline, Interview Scheduling, Salary Calculations).
  3. **Test Suite Layer (`tests/`)**: Houses clean, declarative pytest test cases separated into `hrlense_portal/` and `recruitment_portal/`.
* **Portal-Specific Per-Test Logging Engine**:
  - Automatically isolates logs per test case into dedicated files:
    - `logs/hrlense_portal/{test_name}.log`
    - `logs/recruitment_portal/{test_name}.log`
  - High-visibility semantic tagging (`[UI]`, `[STEP]`, `[ACTION]`, `[VERIFY]`, `[PASS]`, `[LOGIN API SUCCESS]`).
  - Thread-safe for parallel execution with `pytest-xdist`.
* **Default Run Exclusion & Selective Triggering**:
  - Standard `pytest` execution automatically excludes external invite / long-running suites (`meeting`, `interview`, `increment`, `appraisal`, `payroll`, `calendar`).
  - Can be triggered on-demand via dedicated terminal markers or file paths.
* **Resilient Draft & Form Lifecycle Handling**:
  - Unsaved changes modal auto-handling (`Save as Draft`, `Discard Changes`, `Keep Editing`).
  - Unique `DRAFT-N` invariant anchoring for draft title rules and updates.
  - Automatic conversion to **Paid Intern** modal validation when Gross Salary $< ₹15,000$.
* **Parallel Execution Engine (`pytest-xdist`)**: Smart multi-worker allocation engine (`-n auto`) dynamically scaling across CPU cores.
* **Strict Environment Scoping Policy**: Whitelisted environment enforcement (`ALLOWED_ENVS = {"stg", "prod"}`). Defaults to **Stage (`stg`)**; requires explicit user opt-in (`-e ENV=prod`) for Production.
* **Visual Playwright Tracing & Reports**: Automatic step-by-step DOM visual tracing (`reports/trace_*.zip`), Allure Reporting, and self-contained HTML reports (`reports/report.html`).

---

## 📁 Project Structure

```
HRlens_Playwright/
├── docker/                           # Production Containerization Layer
│   ├── Dockerfile                    # Optimized Playwright Python base image
│   └── compose.yaml                  # Docker Compose orchestration
├── core/                             # Framework Infrastructure & Config
│   ├── auth/auth_manager.py          # Session authentication & token management
│   ├── browser/browser_manager.py    # Playwright browser lifecycle & context
│   ├── config/settings.py            # Environment settings & user credentials
│   └── reporting/trace_manager.py    # Playwright visual trace capture
├── pages/                            # Layer 1: Page Object Model (POM)
│   ├── base_page.py                  # Base class with safe auto-waiting wrappers
│   ├── login_page.py                 # Authentication page object
│   ├── hrlense_portal/               # HRlens Portal page objects
│   │   ├── admin_control/            # Hierarchy & settings
│   │   ├── attendance/               # Leave & attendance tracking
│   │   ├── employee/                 # Salary settings, onboarding & profile
│   │   ├── master/                   # Company master configurations
│   │   └── payroll/                  # Salary & payroll configuration
│   └── recruitment_portal/           # Recruitment Portal page objects
│       └── active_job/               # Job opening, drafts & candidate pages
├── workflows/                        # Layer 2: Business Process Workflows
│   ├── hrlense_portal/               # Multi-role attendance & leave workflows
│   └── recruitment_portal/           # End-to-end recruitment & job workflows
├── tests/                            # Layer 3: Test Suites
│   ├── conftest.py                   # Hooks, per-test logging & fixtures
│   ├── hrlense_portal/               # HRlens Portal Test Suites
│   │   ├── ui/                       # Domain test suites (tagged with @pytest.mark.e2e)
│   │   │   ├── admin_control/        # Settings & hierarchy tests
│   │   │   ├── asset/                # Asset lifecycle & master E2E flows
│   │   │   ├── attendance/           # Leave application & approval E2E flows
│   │   │   ├── auth/                 # Authentication & security tests
│   │   │   ├── employee/             # Onboarding & salary calculation tests
│   │   │   ├── increment/            # Increment & appraisal E2E flows
│   │   │   ├── master/               # Company master configurations
│   │   │   ├── meeting/              # Calendar & meeting scheduling tests
│   │   │   └── payroll/              # Salary settings & UI payroll tests
│   │   ├── api/                      # REST API contract & absence validation tests
│   │   └── test_payroll_comparison.py# Dynamic Excel vs API payroll reconciliation
│   └── recruitment_portal/           # Recruitment Portal Test Suites
│       └── ui/active_job/            # Drafts, creation, candidate & offer E2E flows
├── logs/                             # Automatic Per-Test Execution Logs
│   ├── hrlense_portal/               # Dedicated logs for HRlens portal tests
│   └── recruitment_portal/           # Dedicated logs for Recruitment portal tests
├── testdata/                         # Static templates & dynamic Faker generators
├── pytest.ini                        # Marker registry & default exclusion options
└── requirements.txt                  # Locked Python dependencies
```

---

## ⚡ Quick Start & Test Execution

### 1. Run Complete Portals or Specific Test Suites

```powershell
# Run Recruitment Portal Draft Tests (8 tests)
$env:HEADLESS="false"; venv\Scripts\pytest.exe tests/recruitment_portal/ui/active_job/test_job_opening_drafts.py -v -s

# Run Job Opening Creation Tests (Manual & AI JD Generation)
$env:HEADLESS="false"; venv\Scripts\pytest.exe tests/recruitment_portal/ui/active_job/test_job_opening_creation.py -v -s

# Run Full End-to-End Recruitment Flow (Job -> Candidate -> Interview -> LOI)
$env:HEADLESS="false"; venv\Scripts\pytest.exe tests/recruitment_portal/ui/active_job/test_recruitment_flow.py -v -s -m "recruitment_flow"

# Run Candidate & Offer/LOI Validation Suites
$env:HEADLESS="false"; venv\Scripts\pytest.exe tests/recruitment_portal/ui/active_job/test_offer_loi_validation.py -v -s
$env:HEADLESS="false"; venv\Scripts\pytest.exe tests/recruitment_portal/ui/active_job/test_candidate_form_validation.py -v -s
```

---

### 2. Run All End-to-End Workflows (`@pytest.mark.e2e`)

```powershell
# Run all E2E cross-role multi-step workflows across both portals
venv\Scripts\pytest.exe -m "e2e" -v -s

# Run E2E workflows in parallel
pytest -m "e2e" -n auto
```

---

### 3. Run Excluded / Dedicated Suites via Terminal

The following suites are excluded from default runs and can be executed explicitly:

```powershell
# Meeting & Calendar Suite
venv\Scripts\pytest.exe tests/hrlense_portal/ui/meeting/ -v -s
# or via marker:
venv\Scripts\pytest.exe -m "meeting or calendar" -v -s

# Increments & Appraisals Suite
venv\Scripts\pytest.exe tests/hrlense_portal/ui/increment/ -v -s
# or via marker:
venv\Scripts\pytest.exe -m "increment or appraisal" -v -s

# Payroll & Reconciliation Suite
venv\Scripts\pytest.exe tests/hrlense_portal/test_payroll_comparison.py -v -s
# or via marker:
venv\Scripts\pytest.exe -m "payroll" -v -s
```

---

### 3. Parallel Execution (`pytest-xdist`)

```powershell
# Run tests across parallel workers (Headless)
pytest tests/recruitment_portal/ -n auto

# Run specific functional markers in parallel
pytest -m "regression" -n auto
```

---

## 📊 Logs & Reporting

### 1. Isolated Test Logs
Logs are automatically written to `logs/hrlense_portal/{test_name}.log` and `logs/recruitment_portal/{test_name}.log`. Each file contains clean execution timestamps, component tags, and status outcomes.

### 2. Visual Playwright Tracing
On any test failure, a full visual trace is saved to `reports/trace_<test_name>.zip`. To inspect DOM snapshots, network calls, and action timelines:

```powershell
playwright show-trace reports/trace_<test_name>.zip
```

### 3. HTML & Allure Reports

```powershell
# Generate self-contained HTML Report
pytest --html=reports/report.html --self-contained-html

# Generate and view Allure Dashboard
pytest --alluredir=reports/allure
allure serve reports/allure
```

---

## 🐳 Docker Execution

Run the entire automation suite inside containerized environments using Docker Desktop or Docker Engine:

```powershell
# Run regression suite inside Docker container
docker compose --progress quiet -f docker/compose.yaml run --rm tests pytest -m regression -n auto

# Rebuild image and run smoke suite
docker compose --progress quiet -f docker/compose.yaml run --rm --build tests pytest -m smoke
```
