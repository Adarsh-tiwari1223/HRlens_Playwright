# HRlens Playwright Automation Suite

End-to-end test automation and API validation for the **HRlens** platform — powered by **Playwright**, **pytest**, and a structured **Page Object Model (POM)** pattern.

![Python Version](https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python)
![Playwright Version](https://img.shields.io/badge/Playwright-1.49+-green?style=for-the-badge&logo=playwright)
![pytest](https://img.shields.io/badge/pytest-8.3+-orange?style=for-the-badge&logo=pytest)

---

## 🛠️ Tech Stack & Key Capabilities

* **Browser Automation**: [Playwright](https://playwright.dev/python/) for fast, reliable, and modern web testing.
* **Test Runner**: [pytest](https://docs.pytest.org/) for execution, filtering, and tagging.
* **CI/CD Integration**: Fully integrated GitHub Actions CI pipeline running headlessly with automated artifacts.
* **Reports**: Allure Reporting and native HTML reports with automatically attached Playwright execution traces on failure.
* **Data Mocking**: `Faker` for dynamic candidate data generation.

---

## 💎 CI-Enabled Page Object Model (POM)

The framework implements a high-performance, resilient, and **CI-Ready Page Object Model (POM)** designed to run flawlessly locally and in CI/CD pipelines (GitHub Actions):

* **CI-Ready Viewport Optimization**: Automatically detects running environments. On **Local Runs**, it maximizes the browser window to match user screen resolution. On **CI Runs (Headless)**, it defaults to a clean `1920x1080` viewport to ensure sidebar links are expanded and reachable.
* **Safe Native Auto-Waiting Engine**: Wrapper actions in [BasePage](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/pages/base_page.py) utilize Playwright's native Actionability Checks (waiting for stable, visible, and enabled states), replacing fragile hardcoded sleep loops.
* **Auto-Recovery & Sign-In Fallback**: If a test loses session context during navigation, the navigation engine auto-recovers by logging back in and returning to the target page without aborting the test runner.
* **Dynamic Dialog Scoping**: Automatically scopes input fields and dropdowns inside the active dialog container (`[role='dialog']`), handling fallback fields when placeholder texts disappear in Edit modal states.
* **Tab & Dropdown Integration Checks**: Exposes helper methods to set record states (e.g., `set_category_inactive`) and assert that inactive records are pruned from dropdown select options (`verify_category_not_in_dropdown`) in downstream creation drawers.

---

## 📁 Project Structure

```
HRlens_Playwright/
├── .github/
│   └── workflows/
│       └── playwright.yml             # GitHub Actions CI workflow (Playwright Tests)
├── core/
│   └── config/settings.py            # Global environment configuration and user mappings
├── pages/                            # Page Object Model (POM) layer
│   ├── base_page.py                  # Custom BasePage with safe action logs
│   ├── login_page.py                 # LoginPage implementation
│   ├── attendance/
│   │   ├── leave_page.py
│   │   ├── regularization_page.py
│   │   └── unauthorized_absence_page.py
│   ├── employee/
│   │   ├── appointment_letter_template_page.py
│   │   ├── candidate_page.py
│   │   ├── employee_page.py
│   │   ├── offer_letter_template_page.py
│   │   ├── onboarding_page.py
│   │   └── salary_settings_page.py
│   ├── payroll/
│   │   └── payroll_page.py
│   └── recruitment/
│       └── job_opening_page.py
├── testdata/
│   ├── dynamic/
│   │   ├── __init__.py
│   │   └── candidate_data.py         # Dynamic Faker data generator
│   └── static/                       # Static templates and leave configs
├── tests/                            # Test Suite
│   ├── conftest.py                   # Pytest fixtures and viewport configuration
│   ├── api/                          # API test modules (payroll, attendance, leaves)
│   ├── e2e/                          # Full end-to-end integration workflows
│   └── ui/                           # UI-level system tests (smoke, leaves, recruitment)
├── .env                              # Local secrets (ignored from Git)
├── pytest.ini                        # Pytest markers and configuration settings
├── requirements.txt                  # Python locked dependencies
└── setup.bat                         # Automated local environment setup script
```

---

## 🚀 Getting Started

### 1. Installation

Clone the repository and navigate to the project directory:
```powershell
git clone https://github.com/Adarsh-tiwari1223/HRlens_Playwright.git
cd HRlens_Playwright
```

* **Windows**: Run the automated setup script to generate the virtual environment and fetch binaries:
  ```powershell
  .\setup.bat
  ```
* **macOS / Linux**:
  ```bash
  python3.12 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  playwright install chromium
  ```

### 2. Configure Environment Variables
Create a `.env` file in the root of the project:
```env
BASE_URL=https://stg-hrlense.jobvritta.com
API_BASE_URL=https://audit.jobvritta.com/api
HEADLESS=False
DEFAULT_TIMEOUT=10000

# Default test users
EMPLOYEE_USER=adarsh_tiwari
ADMIN_USERNAME=admin@hrlens.com
ADMIN_PASSWORD=your_secure_password
```

---

## ⚡ Running Tests

The test suite is structured around custom **pytest markers** rather than files and directories:

```powershell
# Run only critical smoke tests
pytest -m "smoke" --disable-warnings

# Run only UI-level tests
pytest -m "ui" --disable-warnings

# Run only API-level validation tests
pytest -m "api" --disable-warnings

# Run everything
pytest
```

### Dynamic Viewport System
* **Local Runs (Headed)**: Automatically detects headed mode and launches the browser fully maximized to your screen resolution.
* **CI Runs (Headless)**: Automatically defaults to a high-resolution desktop viewport (`1920x1080`) to ensure sidebar nav links are expanded and visible.

### Intelligent REST API Logger
To keep the console clean and readable, the base API client automatically:
* Redacts sensitive payloads (e.g. `password` or `token`).
* Summarizes long listing arrays (e.g., instead of logging all 40 branches, it outputs `[List of 40 items]`).
* Truncates long response objects to `300` characters.

---

## 📊 Generating Reports

```powershell
# Generate standard HTML report
pytest --html=reports/report.html --self-contained-html

# Run tests and collect Allure trace results
pytest --alluredir=reports/allure
allure serve reports/allure

# Open Playwright Trace Viewer for failed tests
playwright show-trace reports/trace_<test_name>.zip
```
