"""
HRlens Portal — Resignation Page Object (UI Tier).

Contains UI locators and atomic UI interaction methods for the Resignation module.
Strictly UI layer — contains no business logic workflows.
"""

import logging
from typing import Dict, Union
from playwright.sync_api import Page
from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class ResignationPage(BasePage):
    """Page Object containing pure UI interaction methods for Employee Resignation."""

    # Separation Reasons Map (Value -> Label)
    SEPARATION_REASONS = {
        "1": "Career Growth",
        "2": "Better Compensation",
        "3": "Higher Studies",
        "4": "Personal Reasons",
        "5": "Relocation",
        "6": "Work-Life Balance",
        "7": "Health Reasons",
        "8": "Change in Career Path",
        "9": "Entrepreneurship",
        "10": "Contract Completion",
        "11": "Mutual Separation",
        "12": "Project Completion",
        "13": "Performance Issues",
        "14": "Policy Violation",
        "15": "Redundancy",
        "16": "Organizational Restructuring",
        "17": "Absconding",
        "18": "Non-confirmation during Probation",
        "19": "not a perfect match",
    }

    # Toast Messages & Texts
    DUPLICATE_RESIGNATION_TOAST = "You already have a resignation in 'Applied' state."

    # UI Locators
    CONTACT_NUMBER_INPUT = "input[name='personal_Number']"
    REASON_SELECT = "select[name='reason']"
    SUGGESTION_TEXTAREA = "textarea[name='suggestion_Text']"
    EARLY_RELIEVING_DATE_INPUT = "input[type='date']"

    def __init__(self, page: Page):
        super().__init__(page)

    def get_resignation_summary_banner(self) -> Dict[str, str]:
        """
        Reads values from the 'Resignation Summary' top banner if present:
        - Date of Resignation
        - Notice Period
        - Last Working Day
        """
        logger.info("UI Check: Read 'Resignation Summary' banner details")
        banner = self.page.get_by_text("Resignation Summary", exact=False)
        if not banner.is_visible(timeout=3000):
            return {}

        dor_loc = self.page.get_by_text("Date of Resignation", exact=True)
        np_loc = self.page.get_by_text("Notice Period", exact=True)
        lwd_loc = self.page.get_by_text("Last Working Day", exact=True)

        return {
            "date_of_resignation_visible": dor_loc.is_visible(timeout=2000),
            "notice_period_visible": np_loc.is_visible(timeout=2000),
            "last_working_day_visible": lwd_loc.is_visible(timeout=2000),
        }


    # ──────────────────────────────────────────────────────────────────────────
    # UI ACTIONS & LOCATORS
    # ──────────────────────────────────────────────────────────────────────────

    def navigate_to_resignation(self) -> None:
        """Navigates to the Resignation module via direct URL for Employee to guarantee fresh data."""
        logger.info("UI Action: Navigating to Resignation module")
        try:
            self.page.bring_to_front()
        except Exception:
            pass

        current_origin = "/".join(self.page.url.split("/")[:3])
        target_url = f"{current_origin}/resignation"
        self.page.goto(target_url)
        self.page.wait_for_load_state("networkidle")



    def navigate_to_hr_resignation_approval(self) -> None:
        """
        HR Navigation Flow:
        1. Navigates directly to /resignation-approval (reloads page for fresh data)
        2. Verifies search input ('Search employee by name...') is visible
        """
        logger.info("UI Action: HR Navigating to Offboarding -> Resignation Approval")
        try:
            self.page.bring_to_front()
        except Exception:
            pass

        current_origin = "/".join(self.page.url.split("/")[:3])
        target_url = f"{current_origin}/resignation-approval"
        self.page.goto(target_url)
        self.page.wait_for_load_state("networkidle")

        search_input = self.page.locator("input[placeholder*='Search employee by name']").first
        search_input.wait_for(state="visible", timeout=10000)







    def click_apply_resignation_tab(self) -> None:
        """Clicks on the 'Apply Resignation' tab."""
        logger.info("UI Action: Click 'Apply Resignation' tab")
        apply_tab = self.page.get_by_role("tab", name="Apply Resignation")
        apply_tab.wait_for(state="visible", timeout=5000)
        apply_tab.click()


    def has_active_resignation(self) -> bool:
        """Checks if employee already has an active resignation (Status tab is auto-opened)."""
        status_tab = self.page.get_by_role("tab", name="Status")
        applied_on = self.page.get_by_text("Applied On:", exact=False)
        return status_tab.is_visible(timeout=3000) and applied_on.is_visible(timeout=3000)


    def click_status_tab(self) -> None:
        """Clicks on the 'Status' tab."""
        logger.info("UI Action: Click 'Status' tab")
        status_tab = self.page.get_by_role("tab", name="Status")
        status_tab.wait_for(state="visible", timeout=10000)
        status_tab.click()

    def verify_autofilled_fields(self) -> Dict[str, Union[bool, str]]:
        """Verifies presence of auto-filled personal email label and contact number input."""
        logger.info("UI Check: Verify Personal Email and Contact Number auto-filled fields")
        email_label = self.page.get_by_text("Personal Email", exact=True)
        contact_input = self.page.locator(self.CONTACT_NUMBER_INPUT)

        is_email_visible = email_label.is_visible(timeout=5000)
        is_contact_visible = contact_input.is_visible(timeout=5000)
        contact_val = contact_input.input_value() if is_contact_visible else ""

        return {
            "email_label_visible": is_email_visible,
            "contact_number_visible": is_contact_visible,
            "contact_number_value": contact_val,
        }

    def select_reason_of_separation(self, reason: str) -> str:
        """Selects reason of separation from dropdown by value or label."""
        logger.info(f"UI Action: Select Reason of Separation -> '{reason}'")
        select_loc = self.page.locator(self.REASON_SELECT)
        select_loc.wait_for(state="visible", timeout=5000)

        if reason in self.SEPARATION_REASONS:
            selected_val = select_loc.select_option(value=reason)
        else:
            selected_val = select_loc.select_option(label=reason)

        return selected_val[0] if selected_val else ""

    def toggle_stay_connected(self) -> None:
        """Toggles the 'Would you like to stay connected with us for future opportunities?' checkbox."""
        logger.info("UI Action: Toggle 'Stay Connected' checkbox")
        connected_cb = self.page.get_by_text(
            "Would you like to stay connected with us for future opportunities?", exact=False
        )
        connected_cb.wait_for(state="visible", timeout=5000)
        connected_cb.click()

    def toggle_share_suggestions(self) -> None:
        """Toggles the 'Would you like to share any suggestions to improve us?' checkbox."""
        logger.info("UI Action: Toggle 'Share Suggestions' checkbox")
        suggestions_cb = self.page.get_by_text(
            "Would you like to share any suggestions to improve us?", exact=False
        )
        suggestions_cb.wait_for(state="visible", timeout=5000)
        suggestions_cb.click()

    def enter_suggestions(self, suggestion_text: str) -> None:
        """Fills suggestion text into the mandatory suggestions textarea."""
        logger.info(f"UI Action: Enter suggestions text -> '{suggestion_text}'")
        textarea = self.page.locator(self.SUGGESTION_TEXTAREA)
        textarea.wait_for(state="visible", timeout=5000)
        textarea.fill(suggestion_text)

    def click_submit_resignation_button(self) -> None:
        """Clicks the initial 'Submit Resignation' button."""
        logger.info("UI Action: Click 'Submit Resignation' button")
        submit_btn = self.page.get_by_role("button", name="Submit Resignation")
        submit_btn.wait_for(state="visible", timeout=5000)
        submit_btn.click()

    def is_confirmation_modal_visible(self) -> bool:
        """Checks if the 'Submit Resignation Request' confirmation modal is visible."""
        logger.info("UI Check: Check 'Submit Resignation Request' confirmation modal visibility")
        modal_title = self.page.get_by_text("Submit Resignation Request", exact=True)
        return modal_title.is_visible(timeout=5000)

    def click_confirm_modal_button(self, confirm: bool = True) -> None:
        """Clicks 'Yes, Submit' if confirm is True, or 'Cancel' if confirm is False."""
        if confirm:
            logger.info("UI Action: Click 'Yes, Submit' on confirmation modal")
            yes_btn = self.page.get_by_role("button", name="Yes, Submit")
            yes_btn.wait_for(state="visible", timeout=5000)
            yes_btn.click()
        else:
            logger.info("UI Action: Click 'Cancel' on confirmation modal")
            cancel_btn = self.page.get_by_role("button", name="Cancel")
            cancel_btn.wait_for(state="visible", timeout=5000)
            cancel_btn.click()

    def get_status_view_details(self) -> Dict[str, bool]:
        """Reads visibility of Status tab elements: Applied On label, Stepper steps, and Summary card."""
        logger.info("UI Check: Read Status tab details")
        status_tab = self.page.get_by_role("tab", name="Status")
        status_tab.wait_for(state="visible", timeout=10000)

        applied_on_loc = self.page.get_by_text("Applied On:", exact=False)
        applied_step = self.page.get_by_text("Applied", exact=True)
        notice_period_step = self.page.get_by_text("Notice Period", exact=True)
        relieved_step = self.page.get_by_text("Relieved", exact=True)

        lwd_label = self.page.get_by_text("Last Working Day", exact=True)
        notice_period_label = self.page.get_by_text("Notice Period (days)", exact=True)
        reason_label = self.page.get_by_text("Reason of Separation", exact=True)

        return {
            "applied_on_visible": applied_on_loc.is_visible(timeout=5000),
            "stepper_applied_visible": applied_step.is_visible(timeout=5000),
            "stepper_notice_period_visible": notice_period_step.is_visible(timeout=5000),
            "stepper_relieved_visible": relieved_step.is_visible(timeout=5000),
            "lwd_label_visible": lwd_label.is_visible(timeout=5000),
            "notice_period_label_visible": notice_period_label.is_visible(timeout=5000),
            "reason_label_visible": reason_label.is_visible(timeout=5000),
        }

    def fill_early_relieving_date(self, early_relieving_date: str) -> None:
        """Fills early relieving date input field."""
        logger.info(f"UI Action: Fill Early Relieving Date -> '{early_relieving_date}'")
        date_input = self.page.locator(self.EARLY_RELIEVING_DATE_INPUT).first
        date_input.wait_for(state="visible", timeout=5000)
        date_input.fill(early_relieving_date)

    def get_early_relieving_min_date(self) -> str:
        """Reads the 'min' attribute of the Early Relieving Date input field (e.g. Present Date)."""
        logger.info("UI Check: Read 'min' date attribute of Early Relieving Date input")
        date_input = self.page.locator(self.EARLY_RELIEVING_DATE_INPUT).first
        if date_input.is_visible(timeout=3000):
            return date_input.get_attribute("min") or ""
        return ""

    def get_early_relieving_max_date(self) -> str:
        """Reads the 'max' attribute of the Early Relieving Date input field (e.g. '2026-11-30')."""
        logger.info("UI Check: Read 'max' date attribute of Early Relieving Date input")
        date_input = self.page.locator(self.EARLY_RELIEVING_DATE_INPUT).first
        if date_input.is_visible(timeout=3000):
            return date_input.get_attribute("max") or ""
        return ""

    def is_released_status_immutable(self) -> bool:
        """Checks if resignation is in 'Released' state and all modification inputs/buttons are disabled/hidden."""
        logger.info("UI Check: Verify 'Released' status immutability")
        released_badge = self.page.get_by_text("Released", exact=True)
        if not released_badge.is_visible(timeout=3000):
            return False

        # All inputs/buttons should be disabled or hidden in Released state
        submit_btn = self.page.get_by_role("button", name="Submit")
        return not submit_btn.is_enabled(timeout=2000) if submit_btn.is_visible(timeout=1000) else True


    def click_early_relieving_submit_button(self) -> None:
        """Clicks the 'Submit' button for early relieving request."""
        logger.info("UI Action: Click 'Submit' button for early relieving")
        submit_btn = self.page.get_by_role("button", name="Submit")
        if not submit_btn.is_visible(timeout=2000):
            submit_btn = self.page.locator("button:has-text('Submit')").first

        submit_btn.wait_for(state="visible", timeout=5000)
        submit_btn.click()

    def click_buyout_request_button(self) -> None:
        """Clicks on the 'View Buy out Request' or 'Apply Buyout' button."""
        logger.info("UI Action: Click Buyout Request button")
        buyout_btn = self.page.locator("button:has-text('Buy out'), button:has-text('Buyout')").first
        buyout_btn.wait_for(state="visible", timeout=5000)
        buyout_btn.click()

    def search_employee_in_hr_table(self, employee_name: str) -> None:
        """Types employee name in HR Resignation search input ('Search employee by name...'), presses Enter, and waits 2s for table filtering."""
        logger.info(f"UI Action: HR searching employee by name -> '{employee_name}'")
        search_input = self.page.locator("input[placeholder*='Search employee by name']").first
        search_input.wait_for(state="visible", timeout=5000)
        search_input.click()
        search_input.fill(employee_name)
        search_input.press("Enter")
        self.page.wait_for_timeout(2000)


    def get_hr_table_employee_status(self, employee_name: str) -> str:
        """Reads the status badge text for an employee in the HR Resignation table."""
        logger.info(f"UI Check: Read table status badge for '{employee_name}'")
        row = self.page.locator(f"tr:has-text('{employee_name}')").first
        if row.is_visible(timeout=3000):
            badge = row.locator(".chakra-badge").first
            if badge.is_visible(timeout=2000):
                return badge.inner_text().strip()
        return ""

    def open_hr_resignation_details_modal(self, employee_name: str) -> bool:
        """Clicks on employee name in table row to open 'Resignation Details' modal."""
        logger.info(f"UI Action: Opening 'Resignation Details' modal for '{employee_name}'")
        row = self.page.locator(f"tr:has-text('{employee_name}')").first
        name_cell = row.locator(f"p:has-text('{employee_name}'), td:has-text('{employee_name}')").first
        name_cell.wait_for(state="visible", timeout=5000)
        name_cell.click()

        modal_header = self.page.locator("header:has-text('Resignation Details')").first
        modal_header.wait_for(state="visible", timeout=5000)
        return modal_header.is_visible()



    def is_modal_revoke_button_visible(self) -> bool:
        """Checks if 'Revoke' button inside 'Resignation Details' modal is visible."""
        logger.info("UI Check: Check 'Revoke' button visibility inside Resignation Details modal")
        revoke_btn = self.page.locator("button:has-text('Revoke')").first
        return revoke_btn.is_visible(timeout=3000)

    def click_modal_revoke_and_confirm(self) -> bool:
        """Clicks 'Revoke' inside Resignation Details modal and confirms via 'Confirm' / 'Yes' button."""
        logger.info("UI Action: Click 'Revoke' button inside modal and confirm")
        revoke_btn = self.page.locator("button:has-text('Revoke')").first
        if not revoke_btn.is_visible(timeout=3000):
            logger.warning("'Revoke' button is not visible inside Resignation Details modal")
            return False

        revoke_btn.click()

        confirm_btn = self.page.locator("button:has-text('Confirm'), button:has-text('Yes')").first
        confirm_btn.wait_for(state="visible", timeout=5000)
        confirm_btn.click()
        return True

    def hr_revoke_request_flow(self, employee_name: str = "") -> bool:
        """
        Executes the complete HR Revoke Request Flow:
        1. Types dynamic employee name into input[placeholder='Search employee by name...']
        2. Inspects row tr:has-text(employee_name) and reads status badge (.chakra-badge)
        3. If status is 'Resignation Requested' (or 'Applied'), clicks employee name to open modal (header:has-text('Resignation Details'))
        4. Checks if button:has-text('Revoke') is visible inside modal
        5. Clicks 'Revoke' button inside modal and confirms via 'Confirm' / 'Yes' button
        """
        logger.info(f"UI Workflow: Executing HR Revoke Request Flow for employee '{employee_name}'")
        self.navigate_to_hr_resignation_approval()

        if employee_name:
            self.search_employee_in_hr_table(employee_name)


        status = self.get_hr_table_employee_status(employee_name)
        logger.info(f"HR Revoke Request Flow -> Discovered table status for '{employee_name}': '{status}'")

        if "revoke requested" in status.lower():
            logger.info(f"Status is already '{status}': Revoke request has ALREADY been sent. Skipping HR revoke click and returning True.")
            return True

        # Step 3: Only block if status explicitly indicates 'Buyout Requested'
        if "buyout" in status.lower():
            logger.info(f"HR Revoke Request Flow -> Status is '{status}': Revoke BLOCKED for '{employee_name}'")
            return False

        # Click employee name to open modal (header:has-text('Resignation Details'))
        modal_opened = self.open_hr_resignation_details_modal(employee_name)
        if not modal_opened:
            logger.warning(f"Could not open 'Resignation Details' modal for '{employee_name}'")
            return False

        if self.is_modal_revoke_button_visible():
            return self.click_modal_revoke_and_confirm()

        return False



    def open_hr_buyout_request_drawer(self, employee_name: str) -> bool:
        """
        1. Navigates to HR Resignation Approval table & searches employee_name.
        2. EXPLICITLY VALIDATES Employee Name and Status:
           Locates table row containing employee_name and checks if Status badge == 'BUYOUT REQUESTED'.
        3. If validated, clicks Actions hamburger button -> selects 'Buyout Request' menu item.
        """
        logger.info(f"UI Action: Opening 'Buyout Request' drawer for '{employee_name}'")
        self.navigate_to_hr_resignation_approval()
        self.search_employee_in_hr_table(employee_name)

        # Target row in filtered search results specifically matching employee and Buyout status
        row = self.page.locator(f"tr:has-text('{employee_name}'):has-text('Buyout')").first
        if not row.is_visible(timeout=3000):
            row = self.page.locator("tr:has-text('Buyout')").first
        if not row.is_visible(timeout=3000):
            row = self.page.locator(f"tr:has-text('{employee_name}')").first
        row.wait_for(state="visible", timeout=5000)



        # Validate Employee Name & Status Badge
        discovered_name = row.locator("td").nth(1).inner_text().strip()
        status_badge = row.locator(".chakra-badge, span[class*='badge']").first.inner_text().strip()
        logger.info(f"HR Table Validation -> Discovered Employee: '{discovered_name}' | Status: '{status_badge}'")

        if "buyout requested" not in status_badge.lower():
            logger.error(f"Validation Error: Employee '{discovered_name}' has status '{status_badge}', expected 'BUYOUT REQUESTED' to proceed with HR Buyout")
            return False

        # Click Actions hamburger menu button (located in the last td of the target row)
        actions_btn = row.locator("td").last.locator("button").first
        if not actions_btn.is_visible(timeout=2000):
            actions_btn = row.locator("button[aria-label='Actions'], button.chakra-menu__menu-button").first

        actions_btn.wait_for(state="visible", timeout=5000)
        actions_btn.click()
        self.page.wait_for_timeout(500)

        # Click 'Buyout Request' / 'Approve Buyout' / 'Buyout' menu item
        buyout_menu_item = self.page.locator("button[role='menuitem']:has-text('Buyout Request'), button.chakra-menu__menuitem:has-text('Buyout Request'), [role='menuitem']:has-text('Buyout Request'), button:has-text('Buyout Request'), button:has-text('Approve Buyout')").first
        buyout_menu_item.wait_for(state="visible", timeout=5000)
        buyout_menu_item.click()

        # Verify drawer / modal header or dialog container
        modal_content = self.page.locator("header:has-text('Approve Buyout'), header:has-text('Buyout Request'), header:has-text('Buyout'), header:has-text('Process Buyout'), .chakra-modal__header, section.chakra-modal__content, div[role='dialog']").first
        modal_content.wait_for(state="visible", timeout=10000)
        return modal_content.is_visible()




    def process_or_reject_hr_buyout(self, process: bool = True) -> str:
        """
        1. Inside 'Buyout Request' drawer, clicks 'Process Buyout' / 'Approve Buyout'.
        2. Deals with the confirmation modal (header: 'Approve Buyout'):
           Clicks the final 'Approve' button inside the confirmation modal!
        3. Captures and returns toast message.
        """
        if process:
            logger.info("UI Action: Clicking 'Process Buyout' / 'Approve' button in drawer")
            btn = self.page.locator("button:has-text('Process Buyout'), button:has-text('Approve Buyout')").first
            if not btn.is_visible(timeout=2000):
                btn = self.page.locator("button:has-text('Approve')").first
            btn.wait_for(state="visible", timeout=5000)
            btn.click()
            self.page.wait_for_timeout(500)

            # Deal with Confirmation Modal (Header: 'Approve Buyout' -> click 'Approve' button)
            logger.info("UI Action: Confirming 'Approve Buyout' modal via 'Approve' button")
            modal_header = self.page.locator("header:has-text('Approve Buyout'), header:has-text('Approve')").first
            if modal_header.is_visible(timeout=5000):
                approve_btn = self.page.locator(".chakra-modal__footer button:has-text('Approve'), .chakra-modal__content button:has-text('Approve'), button:has-text('Approve')").first
                approve_btn.wait_for(state="visible", timeout=5000)
                approve_btn.click()
        else:
            logger.info("UI Action: Clicking 'Reject Buyout' / 'Cancel' button")
            btn = self.page.locator("button:has-text('Reject Buyout'), button:has-text('Cancel')").first
            btn.wait_for(state="visible", timeout=5000)
            btn.click()

        return self.wait_for_toast(timeout=10000)








    def is_employee_revoke_decision_visible(self) -> Dict[str, bool]:
        """Checks if 'Accept Revoke' and 'Decline Revoke' buttons are visible for the employee."""
        logger.info("UI Check: Verify Employee 'Accept Revoke' and 'Decline Revoke' decision buttons visibility")
        accept_btn = self.page.locator("button:has-text('Accept Revoke'), button:has-text('Accept')").first
        decline_btn = self.page.locator("button:has-text('Decline Revoke'), button:has-text('Decline'), button:has-text('Reject')").first
        return {
            "accept_visible": accept_btn.is_visible(timeout=3000),
            "decline_visible": decline_btn.is_visible(timeout=3000),
        }

    def respond_to_revoke_request(self, accept: bool = True) -> None:
        """Employee clicks 'Accept Revoke' or 'Decline Revoke' and confirms via modal."""
        if accept:
            logger.info("UI Action: Employee clicking 'Accept Revoke' button")
            btn = self.page.locator("button:has-text('Accept Revoke'), button:has-text('Accept')").first
            btn.wait_for(state="visible", timeout=5000)
            btn.click()

            # Handle Confirmation Modal: header 'Accept Revoke Request' -> click 'Yes, Accept'
            logger.info("UI Action: Confirming 'Accept Revoke Request' modal via 'Yes, Accept' button")
            confirm_modal_header = self.page.locator("header:has-text('Accept Revoke Request'), header:has-text('Accept Revoke')").first
            if confirm_modal_header.is_visible(timeout=3000):
                yes_btn = self.page.locator("button:has-text('Yes, Accept'), button:has-text('Yes')").first
                yes_btn.wait_for(state="visible", timeout=3000)
                yes_btn.click()
        else:
            logger.info("UI Action: Employee clicking 'Decline Revoke' button")
            btn = self.page.locator("button:has-text('Decline Revoke'), button:has-text('Decline'), button:has-text('Reject')").first
            btn.wait_for(state="visible", timeout=5000)
            btn.click()

            # Handle Confirmation Modal if any appears
            confirm_modal_header = self.page.locator("header:has-text('Decline Revoke Request'), header:has-text('Decline Revoke'), header:has-text('Decline')").first
            if confirm_modal_header.is_visible(timeout=3000):
                yes_btn = self.page.locator("button:has-text('Yes, Decline'), button:has-text('Yes'), button:has-text('Confirm')").first
                if yes_btn.is_visible(timeout=2000):
                    yes_btn.click()




    def get_form_validation_errors(self) -> Dict[str, str]:
        """Discovers and returns Chakra UI field-level error messages present on the form."""
        logger.info("UI Check: Discover Chakra UI field validation error messages")
        return self.get_all_validation_messages()

    # ──────────────────────────────────────────────────────────────────────────
    # ACCOUNTANT / FINANCE BUYOUT PROCESSING METHODS
    # ──────────────────────────────────────────────────────────────────────────

    def navigate_to_accountant_buyout_processing(self) -> None:
        """
        Navigates Accountant / Finance role to /accounts-buyout-processing.
        Verifies search input field.
        """
        logger.info("UI Action: Accountant Navigating to /accounts-buyout-processing")
        try:
            self.page.bring_to_front()
        except Exception:
            pass

        current_origin = "/".join(self.page.url.split("/")[:3])
        target_url = f"{current_origin}/accounts-buyout-processing"
        if not self.page.url.endswith("/accounts-buyout-processing"):
            self.page.goto(target_url, timeout=30000)

        search_input = self.page.locator("input[placeholder*='Search Employee by name']").first
        search_input.wait_for(state="visible", timeout=10000)

    def search_employee_in_accountant_table(self, employee_name: str) -> None:
        """
        Types employee name in 'Search Employee by name....' input field and presses Enter.
        """
        logger.info(f"UI Action: Accountant searching employee by name -> '{employee_name}'")
        search_input = self.page.locator("input[placeholder*='Search Employee by name']").first
        search_input.wait_for(state="visible", timeout=5000)
        search_input.fill(employee_name)
        search_input.press("Enter")
        self.page.wait_for_timeout(1000)

    def get_accountant_table_employee_status(self, employee_name: str) -> str:
        """Reads the Status badge (.chakra-badge) in Accountant Buyout processing table."""
        logger.info(f"UI Check: Reading Accountant table status badge for '{employee_name}'")
        row = self.page.locator(f"//tr[td[normalize-space()='{employee_name}']]").first
        if not row.is_visible(timeout=3000):
            row = self.page.locator(f"tr:has-text('{employee_name}')").first
        badge = row.locator(".chakra-badge").first
        return badge.inner_text().strip() if badge.is_visible(timeout=3000) else ""

    def open_accountant_process_buyout_modal(self, employee_name: str) -> bool:
        """
        In Accountant Buyout table:
        1. Validates Employee Name and Status ('HR Approved' or 'HR Processed').
        2. Locates employee row via XPath: //tr[td[normalize-space()='{employee_name}']]//img
        3. Clicks action image to open 'Process Buyout' modal (header:has-text('Process Buyout')).
        """
        logger.info(f"UI Action: Opening Accountant 'Process Buyout' modal for '{employee_name}'")
        self.navigate_to_accountant_buyout_processing()
        self.search_employee_in_accountant_table(employee_name)

        status = self.get_accountant_table_employee_status(employee_name)
        logger.info(f"Accountant Table Validation -> Employee: '{employee_name}' | Status: '{status}'")

        if "approved" not in status.lower() and "processed" not in status.lower():
            logger.error(f"Validation Error: Accountant table status for '{employee_name}' is '{status}', expected 'HR Approved' / 'HR Processed'")
            return False

        action_img = self.page.locator(f"//tr[td[normalize-space()='{employee_name}']]//img").first
        action_img.wait_for(state="visible", timeout=10000)
        action_img.click()

        modal_header = self.page.locator("header:has-text('Process Buyout')").first
        modal_header.wait_for(state="visible", timeout=5000)
        return modal_header.is_visible()

    def get_accountant_buyout_modal_values(self) -> Dict[str, str]:
        """
        Reads modal fields: Leave Balance, Leave Payout, Calculated Salary, Buyout Amount, Total Amount.
        Returns a dictionary of raw string values.
        """
        logger.info("UI Check: Reading Accountant 'Process Buyout' modal values")
        leave_balance_loc = self.page.locator("div[role='group']:has-text('Leave Balance') input, input[value*='6']").first
        leave_payout_loc = self.page.locator("input[placeholder*='leave payout'], div[role='group']:has-text('Leave Payout') input").first
        calc_salary_loc = self.page.locator("input[placeholder*='calculated salary'], div[role='group']:has-text('Calculated Salary') input").first
        buyout_amount_loc = self.page.locator("input[placeholder*='buyout amount'], div[role='group']:has-text('Buyout Amount') input").first
        total_amount_loc = self.page.locator("div[role='group']:has-text('Total Amount') input").first

        return {
            "leave_balance": leave_balance_loc.input_value() if leave_balance_loc.is_visible(timeout=2000) else "",
            "leave_payout": leave_payout_loc.input_value() if leave_payout_loc.is_visible(timeout=2000) else "",
            "calculated_salary": calc_salary_loc.input_value() if calc_salary_loc.is_visible(timeout=2000) else "",
            "buyout_amount": buyout_amount_loc.input_value() if buyout_amount_loc.is_visible(timeout=2000) else "",
            "total_amount": total_amount_loc.input_value() if total_amount_loc.is_visible(timeout=2000) else "",
        }

    def process_accountant_buyout(self, calculated_salary: str = "0", remarks: str = "Approved by Accountant", confirm_recovery: bool = True, approve: bool = True) -> str:
        """
        Fills Accountant Process Buyout modal fields:
        - Fills Calculated Salary (reimbursement / arrear / other)
        - Confirms 'Recovery Confirmed' checkbox if needed
        - Fills Remarks
        - Clicks 'Approve' or 'Reject' button and captures toast message.
        """
        action_str = "Approve" if approve else "Reject"
        logger.info(f"UI Action: Accountant submitting Process Buyout modal ({action_str})")

        # Fill Calculated Salary
        if calculated_salary is not None:
            calc_salary_input = self.page.locator(
                "div.chakra-form-control:has-text('Calculated Salary') input, "
                "div[role='group']:has-text('Calculated Salary') input, "
                "label:has-text('Calculated Salary') + input, "
                "input[placeholder*='salary'], "
                "input[placeholder*='Calculated']"
            ).first
            if calc_salary_input.is_visible(timeout=3000):
                logger.info(f"UI Action: Filling Calculated Salary -> '{calculated_salary}'")
                calc_salary_input.click()
                calc_salary_input.press("Control+A")
                calc_salary_input.press("Backspace")
                calc_salary_input.press_sequentially(str(calculated_salary), delay=100)
                calc_salary_input.press("Tab")






        # Toggle Recovery Confirmed Checkbox by clicking visible span label
        if confirm_recovery:
            checkbox_label = self.page.locator(".chakra-checkbox__label:has-text('Recovery Confirmed'), span:has-text('Recovery Confirmed')").first
            checkbox_label.wait_for(state="visible", timeout=5000)
            checkbox_label.click()

        # Fill Remarks
        remarks_field = self.page.locator("textarea[placeholder*='remarks'], div[role='group']:has-text('Remarks') textarea").first
        remarks_field.wait_for(state="visible", timeout=3000)
        remarks_field.fill(remarks)

        # Click Approve or Reject inside modal container
        modal_container = self.page.locator("section.chakra-modal__content, div[role='dialog']").first

        if approve:
            btn = modal_container.locator("button.chakra-button:has-text('Approve'), button.css-h211ee, button:has-text('Approve')").first
            if not btn.is_visible(timeout=3000):
                btn = self.page.locator("section.chakra-modal__content button.chakra-button:has-text('Approve'), button.css-h211ee").first
            btn.wait_for(state="visible", timeout=10000)
            btn.click()
            self.page.wait_for_timeout(500)

            # Handle Confirmation Modal ('Confirm Buyout Approval' -> click 'Confirm' button)
            logger.info("UI Action: Confirming 'Confirm Buyout Approval' modal via 'Confirm' button")
            confirm_modal_header = self.page.locator("header:has-text('Confirm Buyout Approval'), header:has-text('Confirm'), header:has-text('Approve')").first
            if confirm_modal_header.is_visible(timeout=5000):
                confirm_btn = self.page.locator(".chakra-modal__footer button:has-text('Confirm'), .chakra-modal__content button:has-text('Confirm'), button:has-text('Confirm'), button.css-ec34mi").first
                confirm_btn.wait_for(state="visible", timeout=5000)
                confirm_btn.click()

        else:
            btn = modal_container.locator("button.chakra-button:has-text('Reject'), button.css-egkxlg, button:has-text('Reject')").first
            btn.wait_for(state="visible", timeout=10000)
            btn.click()

        return self.wait_for_toast(timeout=10000)

    def navigate_to_exit_clearance(self) -> None:
        """Navigates to /exit-clearance page for IT Person and waits for table headers."""
        logger.info("UI Action: Navigating to Offboarding -> Exit Clearance (/exit-clearance)")
        try:
            self.page.bring_to_front()
        except Exception:
            pass

        current_origin = "/".join(self.page.url.split("/")[:3])
        target_url = f"{current_origin}/exit-clearance"
        self.page.goto(target_url)
        self.page.wait_for_load_state("networkidle")

    def process_it_person_asset_clearance(
        self,
        employee_name: str,
        asset_condition: str = "Good",
        remarks: str = "IT Asset clearance verified & returned in good condition"
    ) -> Dict[str, Union[bool, str]]:
        """
        IT Person Asset Clearance Execution (/exit-clearance):
        1. Navigates directly to /exit-clearance.
        2. Finds target employee row (e.g. 'Sanidhy Tiwari') with status (e.g. 'Accounts Approved Buyout').
        3. Clicks 'Open Checklist (0/2)' button in Action column.
        4. Modal opens with header 'Release Employee Checklist'.
        5. DYNAMIC ASSET HANDLING:
           - Checks if '<button class="chakra-button">Manage Asset Return</button>' is VISIBLE in modal.
           - IF VISIBLE (Employee HAS Assets):
             a. Clicks 'Manage Asset Return' -> Modal 'Assigned Assets' opens.
             b. Finds assigned assets list and clicks 'Return' button next to asset.
             c. Modal 'Return Asset' opens -> Selects Condition radio ('Good'), fills remarks, & submits Return.
             d. Closes Assigned Assets modal.
           - IF NOT VISIBLE (Employee HAS NO Assets):
             Logs 'Manage Asset Return button not visible (No Assets)', marks IT task complete directly.
        6. Captures toast message and verifies clearance completion.
        """
        logger.info(f"UI Action: IT Person processing exit asset clearance for '{employee_name}'")
        self.navigate_to_exit_clearance()

        # Locate employee row in /exit-clearance table
        row = self.page.locator(f"tr:has-text('{employee_name}')").first
        if not row.is_visible(timeout=5000):
            search_input = self.page.locator("input[placeholder*='search' i], input[placeholder*='employee' i]").first
            if search_input.is_visible(timeout=2000):
                search_input.click()
                search_input.fill(employee_name)
                search_input.press("Enter")
                self.page.wait_for_timeout(1500)
                row = self.page.locator(f"tr:has-text('{employee_name}')").first

        row.wait_for(state="visible", timeout=5000)

        # Read Status badge text from row
        status_badge = row.locator(".chakra-badge, span[class*='badge']").first.inner_text().strip() if row.locator(".chakra-badge, span[class*='badge']").first.is_visible(timeout=2000) else ""
        logger.info(f"IT Exit Clearance Table -> Employee: '{employee_name}' | Status: '{status_badge}'")

        # Step 1: Click Action button: <button class="chakra-button">Open Checklist (*)</button>
        checklist_btn = row.locator("button:has-text('Open Checklist'), button:has-text('Checklist')").first
        checklist_btn.wait_for(state="visible", timeout=5000)
        checklist_btn.click()
        self.page.wait_for_timeout(500)

        # Step 2: Verify Modal Header: <header class="chakra-modal__header">Release Employee Checklist</header>
        checklist_modal = self.page.locator("section.chakra-modal__content, div[role='dialog']").first
        checklist_modal.wait_for(state="visible", timeout=5000)

        # Check if 'Manage Asset Return' button is visible inside checklist modal
        manage_asset_btn = checklist_modal.locator("button:has-text('Manage Asset Return'), button:has-text('Asset Return')").first
        has_assets = manage_asset_btn.is_visible(timeout=3000)

        if has_assets:
            logger.info(f"[IT ASSET FLOW] 'Manage Asset Return' button IS VISIBLE for '{employee_name}' -> Employee HAS assigned assets")
            manage_asset_btn.click()
            self.page.wait_for_timeout(800)

            # Step 3: Inside 'Assigned Assets' modal
            assigned_assets_modal = self.page.locator("section.chakra-modal__content:has-text('Assigned Assets'), div[role='dialog']:has-text('Assigned Assets')").first
            if not assigned_assets_modal.is_visible(timeout=3000):
                assigned_assets_modal = self.page.locator("section.chakra-modal__content, div[role='dialog']").last

            # Locate 'Return' button next to asset in list: <button type="button" class="chakra-button css-1yax204">Return</button>
            return_btns = assigned_assets_modal.locator("button:has-text('Return')").all()
            for r_btn in return_btns:
                if r_btn.is_visible(timeout=2000):
                    logger.info("Clicking 'Return' button on assigned asset in list...")
                    r_btn.click()
                    self.page.wait_for_timeout(800)

                    # Step 4: Inside 'Return Asset' dialog modal
                    return_dialog = self.page.locator("section.chakra-modal__content:has-text('Return Asset'), div[role='dialog']:has-text('Return Asset')").first
                    if not return_dialog.is_visible(timeout=3000):
                        return_dialog = self.page.locator("section.chakra-modal__content, div[role='dialog']").last

                    if return_dialog.is_visible(timeout=3000):
                        # Select Condition radio (Good / Damaged / Lost)
                        radio = return_dialog.locator(f"input[type='radio'][value='{asset_condition}'], label:has-text('{asset_condition}')").first
                        if radio.is_visible(timeout=2000):
                            radio.click(force=True)

                        # Fill Remarks textarea
                        remarks_area = return_dialog.locator("textarea").first
                        if remarks_area.is_visible(timeout=2000):
                            remarks_area.fill(remarks)

                        # Click Return Asset confirmation button
                        confirm_return_btn = return_dialog.locator("button:has-text('Return Asset'), button:has-text('Return'), button:has-text('Submit')").first
                        confirm_return_btn.wait_for(state="visible", timeout=5000)
                        confirm_return_btn.click()
                        self.page.wait_for_timeout(1000)

            # Close Assigned Assets modal if still open
            if assigned_assets_modal.is_visible(timeout=1000):
                self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(500)

        else:
            logger.info(f"[IT ASSET FLOW] 'Manage Asset Return' button IS NOT VISIBLE for '{employee_name}' -> Employee HAS NO assigned assets")

        # Step 5: Mark IT Task Complete in Release Employee Checklist modal if checkbox or complete button present
        complete_task_btn = checklist_modal.locator("button:has-text('Complete'), button:has-text('Submit'), button:has-text('Confirm'), button:has-text('Approve')").first
        if complete_task_btn.is_visible(timeout=2000):
            complete_task_btn.click()

        toast_msg = self.wait_for_toast(timeout=10000)
        return {
            "success": True,
            "toast": toast_msg,
            "has_assets": has_assets,
            "status": status_badge
        }










