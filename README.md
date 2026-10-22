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
* **Zero-Touch Onboarding & Auto-Configuration**:
  - One-click setup scripts (`setup.bat` for Windows, `setup.sh` for Linux/Mac/WSL) automatically create the virtual environment, install requirements, download Playwright Chromium, and initialize `.env` from `.env.example`.
* **Model Context Protocol (MCP) Workspace Integration**:
  - Auto-discovered workspace configuration (`.agents/mcp_config.json`) connects AI coding assistants directly to the Google Sheets MCP server (`npx -y mcp-gsheets`) for automated test execution tracking and defect syncing without machine-specific setup.
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
* **Centralized Stage Email Verification (Gmail API & MCP Integration)**:
  - The Stage environment (`stg`) routes all outgoing emails (candidate offboarding, resignation notifications, offer letters/LOIs, meeting invites, and approval alerts) through a centralized QA mailbox.
  - Integrated with the **Gmail REST API** (`utils/mail/gmail_client.py`) and **Gmail MCP** to programmatically fetch, inspect, and verify transactional mail delivery, extract OTPs/verification links, and assert against email headers and HTML bodies in automated test suites.
* **Visual Playwright Tracing & Reports**: Automatic step-by-step DOM visual tracing (`reports/trace_*.zip`), Allure Reporting, and self-contained HTML reports (`reports/report.html`).

---

## 📁 Project Structure

```
HRlens_Playwright/
├── .agents/                          # AI Agent Rules, Workflows & MCP Discovery
│   ├── mcp_config.json               # Auto-discovered Google Sheets MCP configuration
│   ├── rules/                        # Agent execution & QA methodology rules
│   └── workflows/                    # Standard agent verification workflows
├── .github/workflows/                # CI/CD & Automation Pipelines
│   ├── playwright.yml                # Parallel test execution & automated PR pipeline
│   └── docker-publish.yml            # Automated Docker Hub cloud build & push pipeline
├── docker/                           # Production Containerization Layer
│   ├── Dockerfile                    # Optimized Playwright Python base image
│   └── compose.yaml                  # Docker Compose orchestration
├── core/                             # Framework Infrastructure & Config
│   ├── auth/                         # Authentication & session pooling
│   │   ├── auth_manager.py           # Multi-persona authentication engine
│   │   └── credentials/              # Isolated, gitignored OAuth credentials
│   ├── browser/browser_manager.py    # Playwright browser lifecycle & context
│   ├── config/settings.py            # Environment settings & user credentials
│   └── reporting/trace_manager.py    # Playwright visual trace capture
├── pages/                            # Layer 1: Page Object Model (POM)
│   ├── base_page.py                  # Base class with safe auto-waiting wrappers
│   ├── login_page.py                 # Authentication page object
│   ├── hrlense_portal/               # HRlens Portal page objects
│   │   ├── admin_control/            # Hierarchy & settings
│   │   ├── asset/                    # Asset management page objects
│   │   ├── attendance/               # Leave & attendance tracking
│   │   ├── employee/                 # Salary settings, onboarding & profile
│   │   ├── master/                   # Company master configurations
│   │   ├── payroll/                  # Salary & payroll configuration
│   │   └── resignation/              # Employee & HR resignation lifecycle
│   └── recruitment_portal/           # Recruitment Portal page objects
│       └── active_job/               # Job opening, drafts & candidate pages
├── workflows/                        # Layer 2: Business Process Workflows
│   ├── hrlense_portal/               # Multi-role cross-page business workflows
│   └── recruitment_portal/           # End-to-end recruitment & job workflows
├── tests/                            # Layer 3: Test Suites
│   ├── conftest.py                   # Hooks, per-test logging & fixtures
│   ├── hrlense_portal/               # HRlens Portal Test Suites (UI & API)
│   │   ├── ui/                       # Domain UI test suites
│   │   └── api/                      # REST API contract & validation tests
│   └── recruitment_portal/           # Recruitment Portal Test Suites
├── utils/                            # Helper Utilities & API Clients
│   ├── api/                          # Domain API Clients
│   └── mail/gmail_client.py          # Gmail OAuth OTP & notification reader
├── testdata/                         # Static templates & dynamic Faker factories
├── .env.example                      # Template environment configuration
├── setup.bat                         # Automated 1-click Windows setup
├── setup.sh                          # Automated 1-click Mac/Linux/WSL setup
├── pytest.ini                        # Marker registry & default exclusion options
└── requirements.txt                  # Locked Python dependencies
```

---

## 🚀 Getting Started (1-Click Clone & Setup)

Getting started requires **zero manual configuration**:

### 1. Clone the Repository
```bash
git clone https://github.com/Adarsh-tiwari1223/HRlens_Playwright.git
cd HRlens_Playwright
```

### 2. Run Automated Setup
The setup script automatically creates the virtual environment, installs dependencies, downloads Playwright Chromium, initializes `.env` from `.env.example`, and prepares all runtime logging directories:

**Windows:**
```powershell
.\setup.bat
```

**Linux / Mac / WSL:**
```bash
chmod +x setup.sh
./setup.sh
```

### 3. Activate Virtual Environment
```powershell
# Windows
venv\Scripts\activate

# Linux / Mac / WSL
source venv/bin/activate
```

### 4. Configure Environment Variables (`.env`)
The setup script automatically copies `.env.example` to `.env`. Open `.env` to customize settings or test credentials:
- **`ENV`**: Set to `stg` (default) or `prod`.
- **`HEADLESS`**: Set `False` for visible browser execution, or `True` for headless runs.
- **Persona Credentials**: Fill in your test credentials (`ADMIN_USERNAME_STG`, `ADMIN_PASSWORD_STG`, etc.). Real credentials are gitignored and never committed.
- **Gmail OAuth OTP (Optional)**: If testing MFA/OTP flows, place Google OAuth credentials (`client_sec.json`, `token.json`) inside the gitignored directory `core/auth/credentials/`.

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

### 1. Local Container Execution (Optional)
Run the automation suite inside containerized environments using Docker Desktop or Docker Engine:

```powershell
# Run regression suite inside Docker container
docker compose --progress quiet -f docker/compose.yaml run --rm tests pytest -m regression -n auto

# Rebuild image and run smoke suite
docker compose --progress quiet -f docker/compose.yaml run --rm --build tests pytest -m smoke
```

### 2. Automated Cloud Publishing (CI/CD)
The `.github/workflows/docker-publish.yml` workflow automatically builds and pushes the container image `adarsh7777/hrlense_playwright:latest` to Docker Hub directly in the cloud:
- **Triggers**: Automatically runs on push to `main` or `develop` when changes are made to `requirements.txt` or `docker/Dockerfile`.
- **Manual Trigger**: Can be dispatched on-demand with 1 click from the GitHub **Actions** tab.
- **Layer Caching**: Uses GitHub Actions cloud cache (`type=gha`) for fast builds.
- **Authentication**: Authenticates securely using repository secrets (`DOCKERHUB_TOKEN` and `DOCKERHUB_USERNAME`).

### 3. Automated Test Pipeline (`.github/workflows/playwright.yml`)
The framework includes an enterprise GitHub Actions CI pipeline:
- **Containerized Test Runs**: Executes tests directly inside the pre-built `adarsh7777/hrlense_playwright:latest` container on `ubuntu-latest`.
- **Parallel Workers**: Runs parallel tests dynamically across CPU cores using `pytest-xdist` (`-n auto`).
- **Automated Pull Request Creation**: Automatically opens comparison PRs against `main` when feature branches are pushed.
- **Artifact Archiving**: Automatically captures and uploads test execution logs, Playwright traces (`reports/trace_*.zip`), and HTML test reports on any test failure.

---

## 🤖 AI Agent & MCP Integration

The HRlens automation repository is natively optimized for autonomous AI coding agents (such as **Google Antigravity**, **Claude Code**, **Cursor**, and **GitHub Copilot**). It features a dedicated Model Context Protocol (MCP) toolchain and standardized architectural guardrails:

### 1. Zero-Touch Model Context Protocol (`.agents/mcp_config.json`)
AI agents working inside this repository automatically discover workspace MCP servers without manual user configuration:
- **Google Sheets MCP Server (`mcp-gsheets`)**: Dynamically launched via `npx -y mcp-gsheets`.
- **Capabilities**:
  - **Test Plan & Matrix Syncing**: Agents directly read test scenario definitions, user stories, and test data requirements from project Google Sheets.
  - **Live Defect & Status Logging**: Agents update execution matrices, log pass/fail status, record bug references, and format cell ranges automatically.
  - **Zero Hardcoded Paths**: Configured via universal `npx` execution, ensuring it works seamlessly on any developer's machine immediately upon cloning.

```json
{
  "mcpServers": {
    "google-sheets": {
      "command": "npx",
      "args": ["-y", "mcp-gsheets"]
    }
  }
}
```

- **Centralized Email Delivery Verification (Gmail API & MCP)**:
  - Because the Stage environment routes all outgoing emails centrally to a designated QA test inbox, AI agents leverage the integrated Gmail REST API client (`utils/mail/gmail_client.py`) and Gmail MCP tools.
  - Agents can autonomously query transactional message threads, verify delivery status, validate HTML email contents (such as resignation notifications, candidate LOI links, and interview invites), and extract OTP tokens during end-to-end testing without manual human intervention.

### 2. Standardized Agent Rules (`.agents/rules/hrlense-v1.md`)
AI assistants operating on this codebase are bounded by strict engineering rules to maintain test reliability and framework integrity:
* **Strict 3-Tier Layer Separation**: Page Objects own DOM locators and actionability; Workflows orchestrate business logic; Tests own assertions. Agents are forbidden from placing test assertions inside Page Objects.
* **Zero Hardcoded Sleeps**: Prohibits `time.sleep()`. All waiting logic must use Playwright's web-first reactive auto-waits (`expect(locator).to_be_visible()`, `to_be_hidden()`).
* **Credential & Secret Protection**: Strict prohibition against leaking or committing real employee emails, API keys, or passwords. All tests use sanitized `.env` variables and dummy mock templates.
* **Hard Business Assertions**: Enforces deterministic, high-integrity assertions over soft assertions or silent warning suppressions.

### 3. Verification & Diagnostic Workflows (`.agents/workflows/hrlense-v1.md`)
Standardized step-by-step diagnostic workflows empower AI agents to:
1. Inspect trace artifacts (`reports/trace_*.zip`) and per-test logs (`logs/*/*.log`) before attempting fixes.
2. Form evidence-backed hypotheses before making code modifications.
3. Validate fixes with targeted pytest runs and markers before reporting completion.


