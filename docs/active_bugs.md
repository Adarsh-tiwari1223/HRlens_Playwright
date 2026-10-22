# Active Bugs Log — HRlens Automation Framework

This document maintains an active record of verified application bugs and backend defects identified during Playwright test execution.

---

## 🐛 Bug Details

### `BUG-CMP-001`: Duplicate Company Code Creation Permitted

* **Bug ID:** `BUG-CMP-001`
* **Module:** Master Data — Company Management
* **Test Case:** [`tests/hrlense_portal/ui/master/test_company.py::test_company_code_uniqueness`](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/tests/hrlense_portal/ui/master/test_company.py#L283)
* **Severity:** High
* **Status:** Open / Unresolved Backend Defect
* **Environment:** Stage (`https://stg-hrlense.jobvritta.com`)
* **Date Reported:** 2026-09-12

---

### Description
When creating a new company, entering a `Company Code` that already exists in the database (e.g., `CODE4911`) is accepted by the application. The system responds with `"Company added successfully"` instead of rejecting the duplicate entry and displaying a validation error message.

---

### Steps to Reproduce
1. Navigate to **Company Master** (`/master/company`).
2. Click **Add New Company**.
3. Fill all mandatory fields using a unique company name and set **Company Code** to `CODE4911`.
4. Click **Add Company** (Submission succeeds with `"Company added successfully"`).
5. Click **Add New Company** again.
6. Fill mandatory fields with a different company name, but set **Company Code** to the exact same value `CODE4911`.
7. Click **Add Company**.

---

### Expected Result
The backend should validate uniqueness of `Company Code` and reject submission with an explicit error toast (e.g., *"Company code already exists"*).

---

### Actual Result
The application processes the request successfully and displays toast message: `"Company added successfully"`.

---

### Pytest Failure Output
```text
FAILED tests/hrlense_portal/ui/master/test_company.py::test_company_code_uniqueness
AssertionError: Failed: Duplicate company code 'CODE4911' was allowed: Company added successfully
```
