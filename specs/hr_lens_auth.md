# HRlens Authentication Test Plan

## Overview
This test plan covers the authentication flow for the HRlens application, ensuring valid users can log in and invalid attempts are handled correctly.

## Target Application
**URL**: `https://stg-hrlense.jobvritta.com`

## UI Elements Identified
The following locators will be used by Playwright for test automation:
- **Username Field**: `#email` (CSS selector)
- **Password Field**: `#password` (CSS selector)
- **Login Button**: `.login-button` (CSS selector)

---

## Test Cases

### 1. Successful Login (Happy Path)
**Objective**: Verify that a user with valid credentials can successfully log into the HRlens application.

**Steps**:
1. Navigate to the HRlens login page (`https://stg-hrlense.jobvritta.com`).
2. Locate the **Username** field (`#email`) and input a valid username/email (e.g., from `.env` configuration).
3. Locate the **Password** field (`#password`) and input the corresponding valid password.
4. Click the **Login** button (`.login-button`).

**Expected Result**:
- The user is successfully authenticated.
- The application redirects the user to the dashboard or main landing page.
- No error messages are displayed.

---

### 2. Error Handling for Incorrect Passwords (Negative Path)
**Objective**: Verify that the system properly rejects login attempts with incorrect passwords and displays an appropriate error message.

**Steps**:
1. Navigate to the HRlens login page (`https://stg-hrlense.jobvritta.com`).
2. Locate the **Username** field (`#email`) and input a valid username/email.
3. Locate the **Password** field (`#password`) and input an *incorrect* password.
4. Click the **Login** button (`.login-button`).

**Expected Result**:
- The user is **not** authenticated and remains on the login page.
- An appropriate error message is displayed indicating invalid credentials.
- The password field might be cleared, and focus is maintained on the form for a retry.
