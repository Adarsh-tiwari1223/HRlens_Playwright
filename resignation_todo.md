# 📋 HRlens Resignation Module — Test Suite Tracker (`resignation_todo.md`)

This tracker organizes all functional workflows, calendar boundary validations, duplicate prevention rules, and role-based restrictions categorized by **P0 (Critical)** and **P1 (High)** priorities.

---

## 🧭 Prioritized Test Matrix

### 🔥 P0 — Critical Test Suite

| # | Priority | Workflow / Validation Scenario | Scope & Verifications | Test File | Status |
|:---:|:---:|---|---|---|:---:|
| **1** | **P0** | **Buyout Date > Last Working Day** | - LWD: `30-11-2026`<br>- Dates after `30-11-2026` disabled in calendar (`max="2026-11-30"`)<br>- Employee cannot select dates past LWD | [`test_resignation.py`](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/tests/hrlense_portal/ui/resignation/test_resignation.py) | `[ ] READY 🧪` |
| **2** | **P0** | **Buyout Date < Present Date** | - Dates before current/present date disabled in calendar (`min="[Present Date]"`)<br>- Employee cannot select past dates | [`test_resignation.py`](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/tests/hrlense_portal/ui/resignation/test_resignation.py) | `[ ] READY 🧪` |
| **3** | **P0** | **Duplicate Resignation Prevention** | - Employee A submits one resignation<br>- Employee A attempts to submit another while existing is active<br>- System prevents duplicate request (`"You already have a resignation in 'Applied' state."`) | [`test_resignation.py`](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/tests/hrlense_portal/ui/resignation/test_resignation.py) | `[ ] READY 🧪` |
| **4** | **P0** | **Buyout Request → HR Revoke Restriction** | - Employee submits Buyout Request<br>- HR opens resignation<br>- HR should NOT have the option to create a Revoke Request (`Revoke Request` button hidden/disabled) | [`test_resignation.py`](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/tests/hrlense_portal/ui/resignation/test_resignation.py) | `[ ] READY 🧪` |

---

### ⚡ P1 — High Test Suite

| # | Priority | Workflow / Validation Scenario | Scope & Verifications | Test File | Status |
|:---:|:---:|---|---|---|:---:|
| **5** | **P1** | **Buyout Date = Last Working Day** | - LWD: `30-11-2026`<br>- Verify `30-11-2026` is selectable and boundary is enforced | [`test_resignation.py`](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/tests/hrlense_portal/ui/resignation/test_resignation.py) | `[ ] READY 🧪` |
| **6** | **P1** | **Revoke without Buyout** | - Employee has NOT submitted a Buyout Request<br>- HR should be able to initiate Revoke Request | [`test_resignation.py`](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/tests/hrlense_portal/ui/resignation/test_resignation.py) | `[ ] READY 🧪` |
| **7** | **P1** | **Released Employee Immutability** | - Resignation reaches `Released` status<br>- Resignation is final; no further changes/modifications possible | [`test_resignation.py`](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/tests/hrlense_portal/ui/resignation/test_resignation.py) | `[ ] READY 🧪` |

---

### 🚀 Commands to Run Priority Suites:
```bash
# Run P0 Critical Suite
pytest tests/hrlense_portal/ui/resignation/test_resignation.py -m p0

# Run P1 High Suite
pytest tests/hrlense_portal/ui/resignation/test_resignation.py -m p1

# Run Full Resignation Suite
pytest tests/hrlense_portal/ui/resignation/test_resignation.py
```
