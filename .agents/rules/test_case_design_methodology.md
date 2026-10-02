# Test Case Design Methodology & Standards (HRlens Project)

## 1. Core Philosophy: Atomic Test Case Design
Automation implementation and test-case documentation are strictly separate concerns:
- **Automation Execution**: A Playwright script may execute an end-to-end user journey across several screens.
- **Spreadsheet Test Documentation**: Every independently verifiable behavior must be an **atomic test case** with its own unique `TC_ID` and its own spreadsheet row.

A **Test Scenario** is NOT a Test Case.
- **Test Scenario (High-Level Grouping)**: *"Verify Employee Search & Filter functionality"*
- **Atomic Test Cases (Discrete Rows)**:
  - `TC-EMP-001`: Verify Search input field is visible and enabled with placeholder text.
  - `TC-EMP-002`: Search with exact matching employee code.
  - `TC-EMP-003`: Search with partial employee first name (case-insensitive).
  - `TC-EMP-004`: Search with non-existent query (verify empty-state message/illustration).
  - `TC-EMP-005`: Search with leading and trailing spaces (verify auto-trim).
  - `TC-EMP-006`: Search with special characters (verify no unhandled error).
  - `TC-EMP-007`: Click clear/reset button (verify search input clears and full table reloads).
  - `TC-EMP-008`: Verify pagination resets to Page 1 upon applying a new search filter.

---

## 2. Mandatory Element-Level Decomposition
For every page, module, drawer, or modal under test, inspect and decompose ALL interactive elements:

1. **Input Fields & Text Areas**:
   - Visibility, default placeholder, enabled/disabled states.
   - Valid data entry.
   - Boundary value testing (min/max characters, numeric thresholds).
   - Character restrictions (numeric-only, letters-only, forbidden special characters).
   - Empty submission / Required field validation messages.
   - Auto-formatting or auto-fill behaviors (e.g., ZIP code lookup).

2. **Dropdowns & Multi-Selects**:
   - Default selected option or placeholder.
   - Option list population (dynamic API loading vs static).
   - Single selection & multi-selection behaviors.
   - Search/filter within dropdown options.
   - Dependent dropdown cascading (e.g. selecting Category filters Subcategory).

3. **Buttons & Actions**:
   - Disabled state when mandatory form inputs are missing.
   - Enabled state when preconditions are met.
   - Single-click action (trigger modal, open drawer, fire API).
   - Double-click / rapid-click debouncing (prevent duplicate submission).
   - Loading/spinner state during asynchronous requests.

4. **Date Pickers**:
   - Default date display.
   - Date range boundaries (past dates disabled, future dates restricted).
   - Manual keyboard entry vs calendar picker selection.
   - Invalid date formats or impossible dates (e.g. Feb 30).

5. **Tables, Lists & Grids**:
   - Column header labels and order.
   - Data rendering accuracy against API response.
   - Ascending and descending column sorting.
   - Pagination controls (Next, Previous, First, Last, page size dropdown).
   - Empty state rendering when zero records exist.

6. **Modals, Drawers & Popups**:
   - Open trigger and backdrop overlay rendering.
   - Close via 'X' icon, 'Cancel' button, and outside click / ESC key.
   - Form state reset upon closing and reopening.

7. **Filters & Reset Controls**:
   - Independent filter application.
   - Combined multi-filter application (AND logic).
   - Reset/Clear All filters restoring default dataset.

8. **RBAC & Security**:
   - Element visibility and action permission based on user role (e.g. Admin vs Branch IT vs Employee).

---

## 3. Analysis Process Before Generating Test Cases
Before producing any test cases for a module:
1. **DOM / UI Analysis**: Inspect all rendered components, controls, and states.
2. **Page Object Model Inspection**: Review selectors and existing interactions in `pages/`.
3. **API & HAR Analysis**: Inspect network request payloads, response schemas, and error codes.
4. **Defect & Regression History**: Incorporate known bugs from `Defect Tracker` to ensure regression coverage.
5. **Existing Documentation**: Review project workflows and business rules.

---

## 4. Pre-Save Quality Checklist
Before writing rows to the Google Sheet via MCP, verify:
- [ ] Has every relevant interactive component been decomposed into atomic conditions?
- [ ] Are test scenarios distinguished from atomic test cases?
- [ ] Are positive, negative, validation, and boundary conditions covered?
- [ ] Are RBAC / permission boundaries addressed where applicable?
- [ ] Is every test case independent (not bundling multiple distinct checks)?
- [ ] Does every row have a unique `TC_ID`?
- [ ] Is the column contract (A through N) strictly honored?
