# HRlens Playwright Test Framework

A Python-based test automation framework using Playwright and pytest for the HRlens application.

## Project Structure

```
HRlens_Playwright/
├── core/
│   ├── config/settings.py          # Environment and app configuration
│   ├── driver/playwright_manager.py # Browser lifecycle management
│   └── fixtures/base_fixture.py    # Base pytest fixtures
├── hooks/test_hooks.py             # Pytest hooks (setup/teardown/reporting)
├── locators/modules/               # Element locators organized by module
├── logs/                           # Test execution logs
├── pages/
│   ├── common/                     # Shared/reusable page components
│   ├── modules/                    # Module-specific page objects
│   └── base_page.py                # Base page object class
├── reports/
│   ├── allure/                     # Allure report output
│   └── html/                      # HTML report output
├── testdata/
│   ├── dynamic/                    # Runtime-generated test data
│   └── static/                    # Static test data (JSON, CSV, etc.)
├── tests/
│   ├── e2e/                        # End-to-end test suites
│   ├── regression/                 # Regression test suites
│   ├── smoke/                      # Smoke test suites
│   └── conftest.py                 # Shared fixtures and test configuration
└── utils/
    ├── api/                        # API helper utilities
    ├── helpers/common_utils.py     # General-purpose utilities
    └── validators/assertions.py   # Custom assertion helpers
```

## Prerequisites

- Python 3.9+
- pip

## Installation

```bash
pip install -r requirements.txt
playwright install
```

## Running Tests

```bash
# Run all tests
pytest

# Run by suite
pytest tests/smoke/
pytest tests/regression/
pytest tests/e2e/

# Run with HTML report
pytest --html=reports/html/report.html

# Run with Allure report
pytest --alluredir=reports/allure
allure serve reports/allure
```

## Configuration

Environment settings are managed in `core/config/settings.py`. Update base URLs, credentials, and browser options there.

## Reporting

- HTML reports are saved to `reports/html/`
- Allure reports are saved to `reports/allure/`
- Logs are saved to `logs/`
