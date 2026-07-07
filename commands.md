# HRlens Playwright Command Runbook

This runbook lists common commands for setting up, running tests, switching environments, and generating reports.

---

## 🛠️ 1. Environment Setup

Run the setup batch script (on Windows) or setup manually:

### Windows (Automated)
```powershell
# Run the setup script to build venv, install requirements, and download Playwright browsers
.\setup.bat
```

### Windows/Mac/Linux (Manual Setup)
```bash
# 1. Create Python Virtual Environment
python -m venv venv

# 2. Activate Virtual Environment
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 3. Install Python Dependencies
pip install -r requirements.txt

# 4. Install Playwright Browsers
playwright install chromium
```

---

## 🔄 2. Switching Environments (Staging vs. Production)

We have configured environment-specific files `.env.stg` and `.env.prod`. You can switch environments by changing the `ENV` variable inside the main `.env` file.

### Option A: Edit the `.env` File (Persistent Switch)
Open your `.env` file and change the `ENV` value:

* **Switch to Staging:**
  ```env
  ENV=stg
  ```
* **Switch to Production:**
  ```env
  ENV=prod
  ```
* **Switch to Local/Dev:**
  ```env
  ENV=dev
  ```

### Option B: Command Line Environment Variable (One-off Switch)
On PowerShell, you can temporarily override the environment for a single command run:

* **Staging:**
  ```powershell
  $env:ENV="stg"; pytest tests/
  ```
* **Production:**
  ```powershell
  $env:ENV="prod"; pytest tests/
  ```

---

## 🧪 3. Running Tests

Before running tests, ensure your virtual environment is active (`.\venv\Scripts\activate`).

### Run Specific Test Categories (via Pytest Markers)
* **Smoke Tests:**
  ```bash
  pytest tests/ -m smoke
  ```
* **Regression Tests:**
  ```bash
  pytest tests/ -m regression
  ```
* **End-to-End (E2E) Tests:**
  ```bash
  pytest tests/ -m e2e
  ```
* **API Tests:**
  ```bash
  pytest tests/ -m api
  ```
* **Multiple categories (e.g. Smoke or Regression):**
  ```bash
  pytest tests/ -m "smoke or regression"
  ```
* **Run Everything:**
  ```bash
  pytest tests/
  ```

### Run Specific Modules or Individual Tests
* **Run Leave API Tests:**
  ```bash
  pytest tests/test_leave_api.py -v --log-cli-level=INFO
  ```
* **Run Back-Date Leave Test only:**
  ```bash
  pytest tests/test_leave_api.py::test_apply_back_date_leave -v
  ```
* **Run Increments UI Tests:**
  ```bash
  pytest tests/test_increment.py -v
  ```

---

## 📊 4. Running Blocker & Validation Reports

These scripts interact with the system APIs to extract data, compare it, and generate spreadsheets under the `reports/` folder.

### Blocker Reports (Missing parameters blocking payroll generation)
* **Scan All Branches:**
  ```bash
  python generate_all_blockers.py
  ```
* **Scan Specific Branches only:**
  ```bash
  python generate_all_blockers.py --branches="Agra,Varanasi,Noida"
  ```
* **Re-build Excel files from latest cached text report:**
  ```bash
  python generate_all_blockers.py --convert-existing
  ```

### Validation/Reconciliation Reports (Comparing Excel data vs. API data)
* **Run Reconciliation for All Companies:**
  ```bash
  python generate_all_validations.py
  ```

---

## 📈 5. Viewing Test Reports & Traces

### HTML Reports
```bash
# Generate report
pytest --html=reports/html/report.html

# Open reports/html/report.html in any browser to view results
```

### Allure Reports
```bash
# Generate allure data
pytest --alluredir=reports/allure

# Serve and open the Allure dashboard in your default browser
allure serve reports/allure
```

### Playwright Trace Viewer
If a test fails, Playwright saves a trace file (e.g., `trace_*.zip` in reports). You can inspect the step-by-step UI actions:
```bash
playwright show-trace reports/trace_<name>.zip
```
