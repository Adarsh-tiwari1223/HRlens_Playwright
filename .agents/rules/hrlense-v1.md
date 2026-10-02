---
trigger: always_on
---

# HRLENS PLAYWRIGHT — PROJECT RULES

## 1. PROJECT STACK
- Language: Python 3.12+
- Automation: Playwright
- Test Runner: pytest
- Applications:
  - HRlens Portal
  - Recruitment Portal
- Testing types:
  - UI functional/regression
  - API contract/validation
  - E2E business workflows

Follow the existing project stack. Do not introduce another framework, language, or client library for convenience.

---

## 2. ARCHITECTURE — MUST PRESERVE

The framework uses:

Tests
  ↓
Workflows
  ↓
Page Objects
  ↓
BasePage / Core Infrastructure

### Page Objects
Own:
- Locators
- UI interactions
- Actionability checks
- Component handling
- Page-specific UI state

Do NOT place business workflows or test assertions here.

### Workflows
Own:
- Multi-step business processes
- Cross-page flows
- Cross-role processes
- Reusable business orchestration

Do NOT duplicate the same multi-step workflow across tests.

### Tests
Own:
- Scenario definition
- Test-specific setup
- Assertions
- Expected business outcome
- Test markers

Keep tests declarative and readable.

### Core
Own:
- Browser lifecycle
- Authentication/session handling
- Configuration
- Environment handling
- Tracing/reporting infrastructure

Do not bypass core infrastructure with ad-hoc implementations.

---

## 3. API RULE

When API interaction is required:

- Use Playwright's built-in API capabilities/request context.
- Reuse the project's existing authentication and environment configuration.
- Validate relevant response status AND response data/payload.
- Use API for:
  - Test-data setup
  - State preparation
  - Independent backend verification
  - API contract testing

Do NOT use API to bypass the behavior being tested.

Do NOT introduce an external HTTP/API client when Playwright's built-in capability is sufficient.

Existing project utilities/API clients may be reused when they are already part of the established framework.

---

## 4. UI/API TEST BOUNDARY

Use UI when validating:
- User interaction
- UI behavior
- Form validation
- Visibility/state
- Navigation
- User-facing messages
- Role-based UI behavior

Use API when validating:
- Backend state
- Response contracts
- Data setup
- Data cleanup
- Backend-side verification

Use UI + API together only when each layer provides independent verification value.

Do not force API usage into UI-only scenarios.

---

## 5. LOCATOR RULES

Prefer, in order:

1. Stable test IDs / dedicated automation attributes
2. Accessible roles/names
3. Stable semantic attributes
4. Existing project locator patterns
5. CSS/XPath only when necessary

Avoid:
- Arbitrary positional selectors
- Fragile DOM chains
- Text selectors dependent on unstable UI wording
- Hardcoded indexes when stable identification exists

Do not change working locators without evidence that they contribute to the failure.

---

## 6. SYNCHRONIZATION

Use Playwright's built-in waiting/actionability mechanisms.

Do NOT:
- Add arbitrary `sleep()` calls
- Increase timeouts blindly
- Hide race conditions with long waits

When synchronization fails, determine whether the cause is:
- Wrong locator
- Element state
- Navigation
- API/backend latency
- Test data
- Authentication/session
- Application behavior

Fix the root cause rather than masking timing problems.

---

## 7. ASSERTIONS

Tests use hard assertions.

Preferred:
- `expect(...)`
- Exact status validation
- Exact/appropriate toast validation
- Explicit business-rule assertions

Do not silently convert failures into warnings.

Do not use soft assertions to hide independent failures.

Assertions must verify the actual requirement, not merely that an action completed.

---

## 8. TEST DATA

Use `testdata/` and existing project data-generation mechanisms.

Test data must be:
- Valid
- Relevant to the scenario
- Deterministic where required
- Unique where uniqueness is required
- Environment-safe

Do not hardcode data that can cause:
- Duplicate-record conflicts
- Cross-test contamination
- Environment-specific failures

For generated data, preserve traceability so failures can be investigated.

Clean up created data when appropriate and safe.

---

## 9. AUTHENTICATION & ROLES

Use existing authentication/session fixtures and managers.

Supported personas include:
- Admin
- HR
- Manager
- Employee
- Director

Do not manually implement authentication inside individual tests when an existing fixture/session mechanism provides it.

For role-based scenarios:
- Authenticate as the required role.
- Verify the role-specific behavior.
- Do not assume permissions based only on UI visibility.

---

## 10. WORKFLOW DESIGN

Create a workflow when a process:
- Spans multiple pages
- Uses multiple roles
- Contains reusable business steps
- Is likely to be used by multiple tests

Do not create workflows for trivial single-page interactions.

Example:

Employee applies leave
→ Manager approves
→ HR verifies balance

belongs in a workflow, while:

Click "Save"
→ Verify toast

normally belongs in the page object + test.

---

## 11. EXISTING CODE FIRST

Before creating new automation:

1. Search for existing Page Objects.
2. Search for existing workflows.
3. Search for existing fixtures/helpers.
4. Search for existing API utilities.
5. Reuse existing patterns where applicable.

Do not create duplicate:
- Pages
- Locators
- Workflows
- Fixtures
- API utilities
- Helper functions

unless the existing implementation cannot satisfy the requirement.

---

## 12. FAILURE INVESTIGATION

When a test fails, investigate using evidence.

Consider:

Test
 ↓
Assertion
 ↓
Workflow
 ↓
Page Object / Locator
 ↓
Synchronization
 ↓
Test Data
 ↓
API / Backend
 ↓
Environment / Authentication
 ↓
Application Defect

This is a diagnostic decision path, not a mandatory blind sequence.

Use traces, logs, screenshots, response data, application state, and reproduction evidence where available.

Do not immediately modify the test simply because the test failed.

---

## 13. REGRESSION SAFETY

When fixing a failure:

- Change only the relevant layer.
- Preserve working behavior.
- Do not refactor unrelated code.
- Do not modify multiple layers unless evidence requires it.
- Run the targeted test first.
- Run relevant regression coverage after the fix.

A fix that makes the target test pass while breaking previously working behavior is not considered successful.

---

## 14. PROJECT ARTIFACTS

Respect existing project artifacts:

- `logs/` → execution logs
- `reports/` → reports and traces
- `testdata/` → test data/assets
- `core/` → framework infrastructure
- `pages/` → page objects
- `workflows/` → business workflows
- `tests/` → test scenarios

Do not place temporary debugging code, generated files, or unrelated artifacts into production directories.

Remove temporary artifacts after investigation.

---

## 15. REPORTING

Keep reports concise and evidence-based.

For a verified result:

STATUS: VERIFIED
ACTION:
RESULT:
VERIFICATION:
OUTCOME:

For a failure/defect:

STATUS: FAILED | DEFECT | BLOCKED
WHAT:
WHY:
FIX:
OUTCOME:
EVIDENCE:

Do not dump complete logs unless specifically requested.

Reference the important evidence instead.

---

## 16. DO NOT

- Do not bypass the application behavior under test.
- Do not fabricate test results.
- Do not claim a test passed without execution/verification.
- Do not replace Playwright with another automation framework.
- Do not introduce external API clients unnecessarily.
- Do not add arbitrary sleeps.
- Do not weaken assertions to make tests pass.
- Do not modify unrelated working code.
- Do not duplicate existing framework functionality.
- Do not guess the root cause when evidence is available.
- Do not treat an infrastructure failure as an application defect without investigation.