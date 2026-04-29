# HRlens Detailed Test Plan

This document outlines the detailed test plan for automating the HRlens application, specifically focusing on the Login and Primary Dashboard. It includes specific ARIA roles and accessibility attributes to assist the Playwright Healer in maintaining robust locators.

## 1. Login Page Automation Strategy

The login form is built using modern UI patterns (Chakra UI) and supports standard accessibility locators.

### 1.1 Element Identification (ARIA Roles & Locators)
To ensure tests remain resilient to UI changes, the Healer should prioritize the following accessibility-based locators:

| Field | ID | Accessibility Locator (Playwright) | Note |
| :--- | :--- | :--- | :--- |
| **Email Input** | `email` | `page.get_by_label("Email")` | Explicitly linked via `label#email-label` |
| **Password Input** | `password` | `page.get_by_label("Password")` | Explicitly linked via `label#password-label` |
| **Login Button** | N/A | `page.get_by_role("button", name="Login")` | Transitions to a "Loading..." state (spinner) upon submission. |

### 1.2 Login Test Scenarios
- **Valid Login**: Enter valid credentials and verify redirection to the primary dashboard.
- **Invalid Credentials**: Enter incorrect password and verify the specific "Email or password is incorrect" error message is visible.
- **Empty Fields**: Submit the form without data and verify required field validations.

## 2. Primary Dashboard Automation Strategy

> **Note:** The dashboard strategy is based on verified authentication using a manager profile (`vivek@tekinspirations.com`). Locators below are confirmed against the staging environment's live DOM.

### 2.1 Verified Element Identification (Locators)
The Healer should utilize the following specific locators verified on the dashboard and Employees view:

| Element Type | Verified Locator (Playwright) | Purpose |
| :--- | :--- | :--- |
| **Sidebar Navigation** | `page.get_by_role("link", name="Employees")` | Accessing main modules (e.g., Dashboard, Employees, Increment). |
| **Portal Toggle** | `page.get_by_role("button", name="Hrlense Portal")` | Switching between HR and Recruitment portals. |
| **Search Bar** | `page.get_by_placeholder("Search employee name")` | Searching the data grid. |
| **View Toggles** | `page.locator("button.listView")` / `page.locator("button.cardView")` | Toggling grid presentation styles. |
| **Filter Comboboxes**| `page.get_by_role("combobox")` / `page.locator("button.filterView")` | Opening filter dialogs. |

### 2.2 Dashboard Test Scenarios
- **Module Navigation**: Verify clicking links in the primary navigation successfully loads the targeted modules (e.g., Employees, Increment Setting).
- **Data Loading & Views**: Ensure the primary employee grids load without errors, and verify the toggle functionality between Card View and List View.
- **Search Functionality**: Verify that inputting an employee name into the search bar correctly filters the displayed employee cards or list rows.
