# HRlens Playwright Automation Framework

End-to-end automation framework for the HRlens Increment Module using **Playwright, Pytest, and API validation strategy**.

---

## 🚀 Tech Stack

| Tool        | Purpose              |
| ----------- | -------------------- |
| Python 3.9+ | Programming language |
| Playwright  | UI automation        |
| pytest      | Test runner          |
| Allure      | Reporting            |
| Requests    | API validation       |

---

## 🧠 Automation Strategy

This framework follows a **layered automation architecture**:

```
API Layer (Core Logic Validation)
        ↓
UI Layer (Representation Validation)
        ↓
E2E Layer (Business Flow Validation)
```

---

## 📂 Project Structure

```
HRlens_Playwright/
│
├── core/                  # Framework core (config, browser, fixtures)
├── hooks/                 # Pytest hooks
├── pages/                 # Page Object Model
│   ├── common/
│   └── modules/increment/
├── locators/              # UI locators
├── utils/
│   ├── api/               # API clients (source of truth)
│   ├── validators/        # Assertions + calculation validation
│   └── helpers/           # Utility functions
├── testdata/              # Static and dynamic test data
├── tests/
│   ├── api/               # Backend calculation tests
│   ├── integration/       # UI vs API validation
│   ├── regression/        # UI functional tests
│   ├── smoke/             # Basic sanity tests
│   └── e2e/               # Full workflow tests
├── reports/               # Test reports
├── logs/                  # Execution logs
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## 🔥 What This Framework Covers

### ✅ API Validation (Core Engine)

* Raw deduction calculation
* Discipline score logic
* Aggregate score computation
* Slab → increment mapping
* Eligibility validation

---

### ✅ UI Validation

* Appraisal summary rendering
* Discipline breakdown display
* Increment percentage visibility
* Negotiation UI behavior

---

### ✅ Integration Validation

* UI score = API score
* UI increment = API increment
* UI deduction = API deduction

---

### ✅ E2E Flow

* Login → Appraisal → Score Calculation → Increment Suggestion → Negotiation → Finalization

---

## ⚙️ Setup

```bash
# Clone repository
git clone https://github.com/Adarsh-tiwari1223/HRlens_Playwright.git
cd HRlens_Playwright

# Create virtual environment
python -m venv venv

# Activate environment
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

---

## ▶️ Running Tests

```bash
# Run all tests
pytest

# Run API tests
pytest tests/api/

# Run UI tests
pytest tests/regression/

# Run integration tests
pytest tests/integration/

# Run E2E tests
pytest tests/e2e/
```

---

## 📊 Reports

### HTML Report

```bash
pytest --html=reports/html/report.html
```

### Allure Report

```bash
pytest --alluredir=reports/allure
allure serve reports/allure
```

---

## 🧪 Example Validation

```python
def test_discipline_score():
    api_data = increment_api.get_employee(emp_id)

    expected = calculate_discipline_score(api_data)
    actual = api_data["discipline"]["disciplineScore"]

    assert expected == actual
```

---

## 💣 Key Design Principle

```
API = Source of Truth
UI = Representation Layer
```

---

## 🎯 Testing Focus

* Calculation accuracy
* Data integrity
* Business workflow validation
* Cross-layer consistency (API ↔ UI)

---

## 🚀 Future Enhancements

* GitHub Actions (CI/CD pipeline)
* Parallel test execution
* Data-driven test execution
* Docker-based execution environment
