# Branch-Scoped RBAC & Persona Isolation Architecture Rule

## Overview
HRlens is an enterprise multi-branch HRMS. All operational workflows—including Asset Management, Requisitions, Returns, Exit Clearances, Buyouts, and FnF Settlements—enforce strict branch-level Role-Based Access Control (RBAC).

## Mandatory Rule: Zero Admin Bypass
**NEVER bypass branch RBAC by substituting generic `admin` credentials when performing role-specific branch actions.**

Every multi-persona test execution MUST strictly utilize the four designated personas belonging to the **same respected employee branch**:

1. **Employee**: The active staff member belonging to Branch X.
2. **IT Person**: The designated IT Administrator responsible for Branch X.
3. **HR Person**: The designated HR Approver / Branch Manager for Branch X.
4. **Accountant / Finance**: The designated Accounts / Finance Officer for Branch X.

---

## Branch Persona Matrix

| Branch | Target Employee (`user_key`) | Respected IT Person (`user_key`) | Respected HR Person (`user_key`) | Respected Accountant (`user_key`) |
| :--- | :--- | :--- | :--- | :--- |
| **Varanasi** | `adarsh_tiwari` / `sanidhy` / `uttam_kumar` | `it_varanasi_ashutosh` / `it_varanasi_tejasav` | `tejaswini` / `shiva` / `ritesh_singh` | `sunil_kumar` / `riya_tripathi` / `shreya_singh` |
| **Agra** | `sanjeev_rohatgi` / `riyan_sharma` | `it_agra_ritesh` / `it_agra_sandeep` | Branch HR (Agra) | Branch Accounts (Agra) |
| **Meerut** | `adarsh_tiwari` / `sanidhy` | `it_meerut_aditya` | Branch HR (Meerut) | Branch Accounts (Meerut) |
| **Noida** | `abhishek_singh` / `uttam_kumar` | `it_noida_puneet` / `it_noida_amarjeet` | Branch HR (Noida) | Branch Accounts (Noida) |

---

## Workflow Enforcement Rules

### 1. Asset Direct Assignment
- **Rule**: An IT Person can only assign assets residing in their own branch stock to employees stationed in that same branch.
- **Negative Gate**: The system must block an IT Person from selecting cross-branch assets or employees outside their branch authority.

### 2. Asset Return & Clearance
- **Rule**: When an employee returns hardware, only the IT Person of that employee's branch can inspect the condition (`Good`, `Repair Required`, `Damaged`, `Lost`) and sign off on clearance.

### 3. Resignation & Buyout Approvals
- **Rule**:
  1. Employee from Branch X submits resignation.
  2. HR Person from Branch X conducts exit interview and reviews buyout requests.
  3. Accountant from Branch X audits leave balances and calculates financial recovery.
  4. IT Person from Branch X clears hardware inventory before FnF is finalized.

---

## Coding Standard in Playwright Test Suites
Always use branch-scoped fixtures or helper resolvers:

```python
# Correct pattern:
branch_bundle = get_branch_persona_bundle("Varanasi")
emp_page, _ = logged_in_page(branch_bundle["employee"])
it_page, _ = logged_in_page(branch_bundle["it_person"])
hr_page, _ = logged_in_page(branch_bundle["hr_person"])
acc_page, _ = logged_in_page(branch_bundle["accountant"])

# Incorrect pattern (PROHIBITED):
admin_page, _ = logged_in_page("admin") # Using admin to bypass IT, HR, or Accountant roles
```
