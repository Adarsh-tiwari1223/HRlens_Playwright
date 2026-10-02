---
description: hat sequence should the agent follow when creating, modifying, debugging, and verifying automation
---

# HRLENS PLAYWRIGHT — QA AUTOMATION WORKFLOW

## PHASE 1 — UNDERSTAND

Identify:

- Portal
- Module
- Scenario
- User role(s)
- UI/API/E2E requirement
- Expected business behavior
- Existing automation involved

If the requirement is ambiguous and affects correctness, clarify before implementation.

---

## PHASE 2 — RECONNAISSANCE

Before writing or changing automation, inspect only the relevant areas:

1. Existing test
2. Related workflow
3. Related Page Object
4. BasePage utilities
5. Relevant fixtures
6. Existing API utilities
7. Test data
8. Configuration/authentication

Goal:

Find what already exists before creating anything new.

---

## PHASE 3 — CHOOSE TEST LEVEL

Determine the appropriate level:

### UI Test
Use when the requirement concerns user-facing behavior.

### API Test
Use when the requirement concerns backend/API behavior.

### UI + API
Use when both layers provide independent verification value.

### E2E Workflow
Use when the scenario represents a meaningful multi-step business journey.

Do not automatically convert every scenario into E2E.

---

## PHASE 4 — DESIGN

Map the scenario to the architecture.

Example:

Test
 ↓
Workflow
 ↓
Page Object
 ↓
BasePage/Core

Decide:

- What belongs in the test?
- What interaction belongs in the Page Object?
- What reusable business process belongs in the Workflow?
- What data must be prepared?
- What should be verified independently?

Keep responsibilities separated.

---

## PHASE 5 — TEST DATA

Prepare required data using existing project mechanisms.

Check:

- Required fields
- Unique constraints
- Role/permission requirements
- Existing records
- Dependencies
- Environment suitability

Prefer controlled API setup when appropriate.

Do not create unnecessary UI setup steps merely to prepare data.

---

## PHASE 6 — IMPLEMENT

Implement the smallest change required.

### Page Object
Add/reuse:
- Locator
- Interaction
- Page-specific helper

### Workflow
Add/reuse:
- Multi-step business orchestration

### Test
Add:
- Scenario
- Setup
- Assertions
- Required markers

Avoid putting logic in the wrong layer.

---

## PHASE 7 — TARGETED EXECUTION

Run the smallest relevant scope first.

Example:

Single test
 ↓
Related test(s)
 ↓
Module regression
 ↓
Broader regression when required

Do not immediately run the entire suite for every small change.

---

## PHASE 8 — FAILURE TRIAGE

If execution fails:

1. Determine whether the assertion is correct.
2. Inspect failure evidence.
3. Determine the failing layer.
4. Check synchronization.
5. Check test data.
6. Check authentication/environment.
7. Check API/backend state.
8. Determine whether application behavior is defective.

Use evidence to decide the next investigation step.

Do not change code merely because the test failed.

---

## PHASE 9 — ROOT-CAUSE FIX

Apply the fix at the layer responsible for the problem.

Examples:

Wrong locator
→ Page Object

Broken reusable business sequence
→ Workflow

Incorrect expected result
→ Test

Invalid test data
→ Test data/setup

Backend state problem
→ API/setup/backend investigation

Framework authentication problem
→ Core/fixture

Application behavior violates requirement
→ Report application defect

---

## PHASE 10 — VERIFICATION

After the fix:

1. Re-run the failed test.
2. Verify the intended behavior.
3. Check relevant dependent tests.
4. Confirm no previously working behavior was broken.
5. Confirm no unnecessary changes remain.

If the same root cause fails twice:

STOP.

Do not continue random modifications.

Report the blocker/evidence or investigate a newly identified root cause separately.

---

## PHASE 11 — CLEANUP

Before completion:

- Remove temporary debugging code.
- Remove temporary test files.
- Remove unnecessary logging.
- Verify only intended source changes remain.
- Preserve useful test artifacts such as failure traces/reports.

---

## PHASE 12 — FINAL REPORT

### Success

STATUS: VERIFIED
ACTION:
RESULT:
VERIFICATION:
OUTCOME:

### Failure

STATUS: FAILED / DEFECT / BLOCKED
WHAT:
WHY:
FIX:
OUTCOME:
EVIDENCE:

Keep the report short and scan-friendly.

Never report an unverified result as successful.