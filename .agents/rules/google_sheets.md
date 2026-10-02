# HRlens Playwright - Google Sheets MCP Schema Contract & Rules

## 1. Target Spreadsheet Details
- **Spreadsheet Name**: `Hrlense`
- **Spreadsheet ID**: `1zDKQpcIodSzS9hUC7SC-tiZHyuSUvZaUHPgnDsnISyc`
- **Spreadsheet URL**: `https://docs.google.com/spreadsheets/d/1zDKQpcIodSzS9hUC7SC-tiZHyuSUvZaUHPgnDsnISyc/edit`

---

## 2. Test Execution & Result Schema Contract
Applied to module tabs:
- `Asset Management`
- `Employee Management`
- `Resignation & FnF`
- `Attendance & Leaves`
- `Recruitment Portal`
- `Payroll & Settings`
- `Masters & Admin Control`
- `Meeting Module`
- `Support & Helpdesk`
- `Performance & Appraisal`
- `Reports & Analytics`
- `Awards & Recognition`

### Column Contract (Columns A through N):
| Column | Field Name | Description / Valid Values | Example |
| :--- | :--- | :--- | :--- |
| **A** | `Date` | Execution Date (`YYYY-MM-DD`) | `2026-10-01` |
| **B** | `TC_ID` | Unique Test Case ID | `TC-AST-001`, `TC-RSG-005` |
| **C** | `Module` | Top-level HRlens Module | `Asset Management`, `Resignation & FnF` |
| **D** | `Sub Module` | Functional sub-area | `Asset Stock`, `Clearance Checklist` |
| **E** | `Feature / Component` | UI Component or Feature under test | `Assign Asset Drawer`, `Admin Approval Modal` |
| **F** | `Test Scenario` | High-level scenario title | `Admin Direct Assignment from Stock to Employee` |
| **G** | `Test Type` | Category of test | `Functional UI`, `API / Integration`, `Security / RBAC` |
| **H** | `Test Case Description`| Detailed objective of the test case | `Verify Admin can assign an available hardware asset directly` |
| **I** | `Steps to Execute` | Numbered, step-by-step reproduction instructions | `1. Login as Admin\n2. Navigate to /asset-assignment\n3. Click + Assign` |
| **J** | `Precondition` | Required prerequisites or system state | `Asset exists with status Available and valid Unit Price` |
| **K** | `Expected Result` | Expected system behavior | `Asset status transitions to Assigned and appears in table` |
| **L** | `Actual Result` | Verified outcome observed during execution | `Asset assigned successfully, toast captured, verified on portal` |
| **M** | `Status` | Standard execution verdict | `Pass`, `Fail`, `Blocked`, `Skipped` |
| **N** | `Comments` | Automated spec path, ticket, or failure root cause | `Automated: test_direct_assignment_admin_dynamic_employee_scoping.py` |

---

## 3. Defect Tracker Schema Contract (17 Columns)
Applied strictly to tab: **`Defect Tracker`** (Synced with the 5-minute automated Apps Script)

### Column Contract (Columns A through Q):
| Column | Field Name | Description / Example |
| :---: | :--- | :--- |
| **A** | `Date` | Date bug logged (`2026-10-01`) |
| **B** | `TC_ID` / `Defect_ID` | Unique Defect ID in constant format (`DEF_001`, `DEF_002`, `DEF_009`) |
| **C** | `Module` | Top-level HRlens Module (`Asset Management`) |
| **D** | `Sub Module` | Functional sub-area (`IT Dashboard`) |
| **E** | `Feature / Component` | Component under test (`Pending Requests Card`) |
| **F** | `Test Scenario` | Scenario title (`Clickable KPI Card Deep-Linking`) |
| **G** | `Test Type` | Test category (`Functional UI`) |
| **H** | `Test Case Description`| Description of expected verification |
| **I** | `Steps to Execute` | Step-by-step reproduction instructions |
| **J** | `Precondition` | Prerequisites (`IT dashboard displayed`) |
| **K** | `Expected Result` | Expected correct system behavior |
| **L** | `Actual Result` | Observed error or defect behavior |
| **M** | `Defect Status` | Current state (`Open`, `Fixed`, `Closed`, `Reopened`) |
| **N** | `Assigned To` | Assigned developer (`Sanidhy Tiwari (Senior Full Stack)`) |
| **O** | `Dev Status` | Developer progress state (`Ready for Test`) |
| **P** | `Retest Status` | QA verification state (`Pending`, `Pass`, `Fail`) |
| **Q** | `Comments` | Requirement notes / ticket remarks |

---

## 4. Operational Instructions for the Agent
1. **Module Routing & Failure Handling**:
   - For test results and test matrix syncing, write strictly to the target module tab (e.g. `Asset Management`, `Resignation & FnF`).
   - **DO NOT manually write to the `Defect Tracker` tab.** When a test case fails, mark Column M (`Status`) as `Fail` in its module sheet with clear failure notes in Column L (`Actual Result`). An automated system trigger automatically extracts rows marked `Fail` and logs them into the `Defect Tracker` after 5 minutes.
2. **Data Consistency**:
   - Always preserve column ordering (Columns A through N).
   - Use standard statuses (`Pass`, `Fail`, `Blocked`, `Skipped`) and defect states (`Open`, `Fixed`, `Closed`).
   - Use ISO date format (`YYYY-MM-DD`).
3. **Test Case Granularity**:
   - Strictly adhere to [.agents/rules/test_case_design_methodology.md](file:///c:/Users/User/Desktop/Tekinspirations/HRlens_Playwright/.agents/rules/test_case_design_methodology.md).
   - Never write broad scenario summaries (e.g. "Verify Search") as test cases. Every row must represent an atomic, independently verifiable test condition.
4. **MCP Tool Calls**:
   - Use `google-sheets` MCP tool `sheets_append_values` or `sheets_update_values` with `spreadsheetId: "1zDKQpcIodSzS9hUC7SC-tiZHyuSUvZaUHPgnDsnISyc"`.
