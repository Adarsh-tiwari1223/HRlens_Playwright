# HRlens Test Automation Plan

## Overview
This document maps out the test automation strategy for the HRlens Increment Module using Playwright and pytest. The tests are designed following the project's core principle: **API = Source of Truth, UI = Representation Layer**.

## Test Suite Categories

Tests are organized using pytest markers: `@pytest.mark.smoke`, `@pytest.mark.regression`, and `@pytest.mark.e2e`.

### 1. Smoke Tests (`tests/test_smoke.py`)
Goal: Ensure critical paths and page loads are functional before deeper testing.

| Test Case | Description | Steps | Expected Result |
| :--- | :--- | :--- | :--- |
| `test_login_page_loads` | Verify login page accessibility. | Navigate to base URL. | Login page renders correctly. |
| `test_increment_page_loads` | Verify Increment page accessibility. | Login -> Click "Increment". | Page loads, Company/Branch/Dept dropdowns visible. |
| `test_negotiation_page_loads` | Verify Negotiation page accessibility. | Login -> Click "Negotiation". | Page loads, Accept/Reject buttons present. |

### 2. Regression Tests
Goal: Feature-level validation of all interactive elements.

#### Increment Setup (`tests/test_increment.py`)
| Test Case | Description | Expected Result |
| :--- | :--- | :--- |
| `test_filter_selections` | Select Company, Branch, Dept. | Dropdowns reflect selected values. |
| `test_date_range_picker` | Select a valid date range. | Selected range is displayed in input. |
| `test_run_assessment` | Trigger "Run Assessment". | Status changes to "Assessments Open". |
| `test_assessment_grid_load` | Navigate to Increment Summary. | Grid renders without error. |
| `test_employee_drilldown` | Select TL -> Select Employee. | Employee assessment form opens. |

#### Negotiation (`tests/test_negotiation.py`)
| Test Case | Description | Expected Result |
| :--- | :--- | :--- |
| `test_accept_offer` | Click Accept. | Success toast appears. |
| `test_reject_offer` | Click Reject. | Status updates accordingly. |
| `test_counter_offer` | Enter valid amount -> Submit. | Success toast appears. |

### 3. End-to-End Workflow (`tests/test_e2e_workflow.py`)
Goal: Validate the complete business cycle for increment assignment.

**Scenario**: Full Increment Cycle
1. **Admin Action**: Login -> Filter -> Run Assessment.
2. **Admin Action**: Go to Summary -> Select Employee -> (Trigger API to assign increment).
3. **Employee Action**: Login as Employee -> Go to Negotiation Tab.
4. **Employee Action**: Submit a Counter-Offer.
5. **Validation**: Verify the counter-offer is recorded via API validation.

## API Validation Strategy
UI tests will occasionally leverage `utils/api_client.py` to:
1. Verify that UI actions (e.g., clicking "Run Assessment") send the correct API request.
2. Validate that the UI accurately displays data returned by the API (no local calculations).
