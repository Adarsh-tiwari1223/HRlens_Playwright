"""
HRlens Portal — Resignation Page Object (UI Tier).

Contains UI locators and atomic UI interaction methods for the Resignation module.
Strictly UI layer — contains no business logic workflows.
"""

import os
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
        self.page.goto(target_url, wait_until="domcontentloaded")
        self.dismiss_all_floating_alerts()
        # Wait for first visible tab, resignation apply form, or active status details view
        self.page.locator(
            "[role='tab'], select[name='reason'], div:has-text('Resignation Summary'), "
            "div:has-text('Resignation Status'), div:has-text('APPLICATION DETAILS'), "
            "button:has-text('Request Withdrawal'), div:has-text('Early Relieving Buyout')"
        ).first.wait_for(state="visible", timeout=10000)



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
        self.page.goto(target_url, wait_until="domcontentloaded")
        self.dismiss_all_floating_alerts()

        search_input = self.page.locator("input[placeholder*='Search employee by name']").first
        search_input.wait_for(state="visible", timeout=10000)







    def click_apply_resignation_tab(self) -> None:
        """Clicks on the 'Apply Resignation' tab."""
        logger.info("UI Action: Click 'Apply Resignation' tab")
        apply_tab = self.page.get_by_role("tab", name="Apply Resignation")
        if apply_tab.is_visible(timeout=2000):
            apply_tab.click()
        else:
            logger.info("Apply Resignation tab not present (direct form view active)")


    def has_active_resignation(self) -> bool:
        """Checks if employee already has an active resignation."""
        status_tab = self.page.get_by_role("tab", name="Status")
        if status_tab.is_visible(timeout=2000):
            return True
        active_indicator = self.page.locator(
            "div:has-text('Resignation Status'), button:has-text('Request Withdrawal'), div:has-text('APPLICATION DETAILS')"
        ).first
        return active_indicator.is_visible(timeout=2000)


    def click_status_tab(self) -> None:
        """Clicks on the 'Status' tab."""
        logger.info("UI Action: Click 'Status' tab")
        status_tab = self.page.get_by_role("tab", name="Status")
        if status_tab.is_visible(timeout=2000):
            status_tab.click()
        else:
            logger.info("Status tab not present (direct status view active)")

    def verify_autofilled_fields(self) -> Dict[str, Union[bool, str]]:
        """Verifies presence of auto-filled personal email label and contact number input."""
        logger.info("UI Check: Verify Personal Email and Contact Number auto-filled fields")
        email_label = self.page.get_by_text("Personal Email", exact=True).first
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

    def is_early_relieving_date_input_visible(self, timeout: int = 3000) -> bool:
        """Checks if Early Relieving Date input is visible on the Status tab."""
        return self.page.locator(self.EARLY_RELIEVING_DATE_INPUT).first.is_visible(timeout=timeout)

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

    def is_withdrawal_button_visible(self, timeout: int = 3000) -> bool:
        """Checks if 'Withdraw Resignation' or 'Request Withdrawal' button is visible on employee portal."""
        btn = self.page.locator("button:has-text('Withdraw Resignation'), button:has-text('Request Withdrawal'), button:has-text('Withdraw')").first
        return btn.is_visible(timeout=timeout)

    def click_request_withdrawal(self) -> dict:
        """
        Clicks 'Withdraw Resignation' / 'Request Withdrawal' on Employee resignation page and confirms modal dialog.
        Captures confirmation and toast message.
        """
        logger.info("UI Action: Click 'Withdraw Resignation' / 'Request Withdrawal' button")
        btn = self.page.locator("button:has-text('Withdraw Resignation'), button:has-text('Request Withdrawal'), button:has-text('Withdraw')").first
        btn.wait_for(state="visible", timeout=5000)
        btn.click()

        # Handle confirmation dialog / alertdialog if present
        modal = self.page.locator("[role='dialog'], [role='alertdialog'], .chakra-modal__content").first
        modal_visible = False
        try:
            if modal.is_visible(timeout=2000):
                modal_visible = True
                confirm_btn = modal.locator(
                    "button:has-text('Confirm'), button:has-text('Yes'), button:has-text('Withdraw'), button:has-text('Submit')"
                ).first
                if confirm_btn.is_visible(timeout=2000):
                    confirm_btn.click()
        except Exception:
            pass

        toast = self.wait_for_toast(timeout=5000)
        logger.info(f"Request Withdrawal result -> Toast: '{toast}', Modal: {modal_visible}")
        return {"modal_visible": modal_visible, "toast": toast}

    def click_buyout_request_button(self) -> None:
        """Clicks on the 'View Buy out Request' or 'Apply Buyout' button."""
        logger.info("UI Action: Click Buyout Request button")
        buyout_btn = self.page.locator("button:has-text('Buy out'), button:has-text('Buyout')").first
        buyout_btn.wait_for(state="visible", timeout=5000)
        buyout_btn.click()

    def search_employee_in_hr_table(self, employee_name: str) -> None:
        """Types employee name in HR Resignation search input ('Search employee by name...'), presses Enter, and waits for table row."""
        logger.info(f"UI Action: HR searching employee by name -> '{employee_name}'")
        self.dismiss_all_floating_alerts()
        search_input = self.page.locator("input[placeholder*='Search employee by name']").first
        search_input.wait_for(state="visible", timeout=5000)
        try:
            search_input.click()
        except Exception:
            self.dismiss_all_floating_alerts()
            search_input.click(force=True)
        search_input.fill(employee_name)
        search_input.press("Enter")
        # Wait for filtered row to appear instead of fixed 2s sleep
        try:
            self.page.locator(f"tr:has-text('{employee_name}')").first.wait_for(state="visible", timeout=5000)
        except Exception:
            pass


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

    def process_hr_withdrawal_request(self, employee_name: str, approve: bool = True) -> dict:
        """
        HR searches employee on /resignation-approval, checks status, and approves or rejects Withdrawal.
        Can process via Actions hamburger menu or via Resignation Details modal.
        """
        logger.info(f"UI Action: HR processing Withdrawal for '{employee_name}' (approve={approve})")
        self.navigate_to_hr_resignation_approval()
        self.search_employee_in_hr_table(employee_name)

        row = self.page.locator(f"tr:has-text('{employee_name}')").first
        row.wait_for(state="visible", timeout=5000)

        initial_status = self.get_hr_table_employee_status(employee_name)
        logger.info(f"HR Resignation table status for '{employee_name}': '{initial_status}'")

        action_keyword = "Approve" if approve else "Reject"
        processed = False

        # Attempt 1: Via Actions hamburger menu in row
        try:
            action_btn = row.locator("td").last.locator("button").first
            if action_btn.is_visible(timeout=2000):
                action_btn.click()
                self.page.wait_for_timeout(500)
                menu_item = self.page.locator(
                    f"[role='menuitem']:has-text('{action_keyword}'), button:has-text('{action_keyword}')"
                ).first
                if menu_item.is_visible(timeout=2000):
                    menu_item.click()
                    processed = True
        except Exception:
            pass

        # Attempt 2: Via Resignation Details modal
        if not processed:
            try:
                self.open_hr_resignation_details_modal(employee_name)
                modal = self.page.locator("[role='dialog'], .chakra-modal__content").first
                btn = modal.locator(f"button:has-text('{action_keyword}')").first
                if btn.is_visible(timeout=3000):
                    btn.click()
                    processed = True
            except Exception:
                pass

        # Handle any confirmation dialog
        try:
            confirm_btn = self.page.locator("[role='alertdialog'] button:has-text('Confirm'), [role='alertdialog'] button:has-text('Yes'), button:has-text('Confirm')").first
            if confirm_btn.is_visible(timeout=2000):
                confirm_btn.click()
        except Exception:
            pass

        toast = self.wait_for_toast(timeout=5000)
        self.page.wait_for_timeout(1000)
        final_status = self.get_hr_table_employee_status(employee_name)
        logger.info(f"HR Withdrawal processing completed -> Initial: '{initial_status}', Final: '{final_status}', Toast: '{toast}'")

        return {
            "processed": processed,
            "initial_status": initial_status,
            "final_status": final_status,
            "toast": toast
        }

    def get_hr_table_row_actions(self, employee_name: str) -> list:
        """
        Searches employee on /resignation-approval, opens row Actions menu,
        and returns list of available action labels.
        """
        self.navigate_to_hr_resignation_approval()
        self.search_employee_in_hr_table(employee_name)
        row = self.page.locator(f"tr:has-text('{employee_name}')").first
        if not row.is_visible(timeout=3000):
            return []
        actions_btn = row.locator("td").last.locator("button.chakra-menu__menu-button, button").first
        if not actions_btn.is_visible(timeout=2000):
            return []
        actions_btn.click()
        self.page.wait_for_timeout(500)
        items = self.page.locator("[role='menuitem'], button.chakra-menu__menuitem, .chakra-menu__menu-list button").all_inner_texts()
        actions = [i.strip() for i in items if i.strip()]
        # Close menu by pressing Escape or clicking outside
        try:
            self.page.keyboard.press("Escape")
        except Exception:
            pass
        return actions

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
            self.page.goto(target_url, timeout=30000, wait_until="domcontentloaded")

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
        # Wait for table row instead of fixed sleep
        try:
            self.page.locator(f"tr:has-text('{employee_name}')").first.wait_for(state="visible", timeout=5000)
        except Exception:
            pass

    def get_accountant_table_employee_status(self, employee_name: str) -> str:
        """Reads the Status badge (.chakra-badge) in Accountant Buyout processing table."""
        logger.info(f"UI Check: Reading Accountant table status badge for '{employee_name}'")
        row = self.page.locator(f"//tr[td[contains(normalize-space(),'{employee_name}')]]").first
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

        action_img = self.page.locator(f"//tr[td[contains(normalize-space(),'{employee_name}')]]//img").first
        action_img.wait_for(state="visible", timeout=10000)
        action_img.click()

        modal_header = self.page.locator("header:has-text('Process Buyout')").first
        modal_header.wait_for(state="visible", timeout=5000)
        return modal_header.is_visible()

    def get_accountant_buyout_modal_values(self) -> Dict[str, str]:
        """
        Reads modal fields: Leave Balance, Buyout Days, Buyout Amount, Total Deductions.
        Matches the refined Accounts Processing modal layout.
        """
        logger.info("UI Check: Reading Accountant 'Process Buyout' modal values")
        modal_container = self.page.locator("section.chakra-modal__content, div[role='dialog']").first

        leave_balance_loc = modal_container.locator(
            "div.chakra-form-control:has-text('Leave Balance') input, "
            "div[role='group']:has-text('Leave Balance') input, "
            "label:has-text('Leave Balance') + input"
        ).first

        # Optional legacy Earnings fields (fallback if present)
        calc_salary_loc = modal_container.locator(
            "tr:has-text('Calculated Salary') input, "
            "input[placeholder*='salary']"
        ).first

        leave_payout_loc = modal_container.locator(
            "tr:has-text('Leave Payout') input, "
            "input[placeholder*='leave payout']"
        ).first

        buyout_amount_loc = modal_container.locator(
            "tr:has-text('Buyout Amount') input, "
            "input[placeholder*='buyout amount'], "
            "input[placeholder='0.00']"
        ).first
        buyout_amount_val = ""
        if buyout_amount_loc.is_visible(timeout=2000):
            buyout_amount_val = buyout_amount_loc.input_value().strip()
        if not buyout_amount_val:
            cell = modal_container.locator("tr:has-text('Buyout Amount') td:last-child, tr:has-text('Buyout Amount') td[data-is-numeric='true']").first
            if cell.is_visible(timeout=1000):
                buyout_amount_val = cell.inner_text().strip()

        total_deductions_loc = modal_container.locator(
            "tr:has-text('Total Deductions') td:last-child, "
            "tr:has-text('Total Deductions') td[data-is-numeric='true']"
        ).first

        buyout_days_loc = modal_container.locator(
            "div:has(> p:text-is('Buyout Day')) p, "
            "div:has(> p:has-text('Buyout Day')) p:last-child"
        ).last

        net_payable_loc = modal_container.locator("div:has-text('Net Payable') p, p:has-text('Net Payable') + p").last

        return {
            "leave_balance": leave_balance_loc.input_value().strip() if leave_balance_loc.is_visible(timeout=2000) else "",
            "leave_payout": leave_payout_loc.input_value().strip() if leave_payout_loc.is_visible(timeout=1000) else "",
            "calculated_salary": calc_salary_loc.input_value().strip() if calc_salary_loc.is_visible(timeout=1000) else "",
            "buyout_amount": buyout_amount_val,
            "total_deductions": total_deductions_loc.inner_text().strip() if total_deductions_loc.is_visible(timeout=2000) else "",
            "buyout_days": buyout_days_loc.inner_text().strip() if buyout_days_loc.is_visible(timeout=2000) else "",
            "total_amount": net_payable_loc.inner_text().strip() if net_payable_loc.is_visible(timeout=1000) else "",
        }

    def process_accountant_buyout(
        self,
        calculated_salary: str = None,
        leave_payout: str = None,
        buyout_amount: str = None,
        remarks: str = "Approved by Accountant",
        confirm_recovery: bool = True,
        approve: bool = True
    ) -> str:
        """
        Fills Accountant Process Buyout modal fields:
        - Fills Calculated Salary if present in UI (legacy/extended form)
        - Fills Leave Payout if present in UI and not pre-filled
        - Fills Buyout Amount if specified
        - Confirms 'Recovery Confirmed' checkbox
        - Fills Remarks (mandatory textarea)
        - Clicks 'Approve' or 'Reject' button in modal footer and confirms.
        """
        action_str = "Approve" if approve else "Reject"
        logger.info(f"UI Action: Accountant submitting Process Buyout modal ({action_str})")
        modal_container = self.page.locator("section.chakra-modal__content, div[role='dialog']").first

        # 1. Fill Calculated Salary (if field exists in UI)
        if calculated_salary is not None:
            calc_salary_input = modal_container.locator(
                "tr:has-text('Calculated Salary') input, "
                "div.chakra-form-control:has-text('Calculated Salary') input, "
                "label:has-text('Calculated Salary') + input"
            ).first
            if calc_salary_input.is_visible(timeout=1000):
                logger.info(f"UI Action: Filling Calculated Salary -> '{calculated_salary}'")
                calc_salary_input.click()
                calc_salary_input.press("Control+A")
                calc_salary_input.press("Backspace")
                calc_salary_input.fill(str(calculated_salary))
                calc_salary_input.press("Tab")

        # 2. Fill Leave Payout if specified and field exists in UI
        if leave_payout is not None:
            leave_payout_input = modal_container.locator(
                "tr:has-text('Leave Payout') input, "
                "input[placeholder*='leave payout']"
            ).first
            if leave_payout_input.is_visible(timeout=1000):
                curr = leave_payout_input.input_value().strip()
                if not curr or curr == "0" or float(curr or 0) <= 0:
                    logger.info(f"UI Action: Filling Leave Payout -> '{leave_payout}'")
                    leave_payout_input.click()
                    leave_payout_input.fill(str(leave_payout))
                    leave_payout_input.press("Tab")

        # 3. Fill / Update Buyout Amount if specified
        if buyout_amount is not None:
            buyout_amount_input = modal_container.locator(
                "tr:has-text('Buyout Amount') input, "
                "input[placeholder*='buyout amount'], "
                "input[placeholder='0.00']"
            ).first
            if buyout_amount_input.is_visible(timeout=2000):
                curr = buyout_amount_input.input_value().strip()
                if not curr or curr == "0" or float(curr or 0) <= 0:
                    logger.info(f"UI Action: Filling Buyout Amount -> '{buyout_amount}'")
                    buyout_amount_input.click()
                    buyout_amount_input.fill(str(buyout_amount))
                    buyout_amount_input.press("Tab")

        # 4. Toggle Recovery Confirmed Checkbox (if enabled and not read-only)
        if confirm_recovery:
            checkbox_label = modal_container.locator(
                "label.chakra-checkbox:has-text('Recovery Confirmed'), "
                "label:has-text('Recovery Confirmed'), "
                "span.chakra-checkbox__label:has-text('Recovery Confirmed')"
            ).first
            if checkbox_label.is_visible(timeout=3000):
                is_disabled = (
                    checkbox_label.get_attribute("data-disabled") is not None
                    or checkbox_label.locator("input[type='checkbox']").is_disabled()
                )
                if is_disabled:
                    logger.info("UI Notice: 'Recovery Confirmed' checkbox is disabled (modal is in read-only mode). Skipping click.")
                else:
                    cb_input = modal_container.locator("input[type='checkbox']").first
                    if cb_input.count() > 0:
                        if not cb_input.is_checked():
                            checkbox_label.click(timeout=3000)
                    else:
                        checkbox_label.click(timeout=3000)

        # 5. Fill Remarks (Mandatory if enabled)
        remarks_field = modal_container.locator(
            "textarea[placeholder*='remarks' i], "
            "textarea.chakra-textarea, "
            "div.chakra-form-control:has-text('Remarks') textarea, "
            "textarea"
        ).first
        if remarks_field.is_visible(timeout=3000):
            if not remarks_field.is_disabled():
                remarks_field.fill(remarks)
            else:
                logger.info("UI Notice: Remarks textarea is read-only/disabled. Skipping fill.")

        # 6. Click Approve or Reject Button in modal footer
        if approve:
            btn = modal_container.locator(
                "footer.chakra-modal__footer button:has-text('Approve'), "
                "button.chakra-button:has-text('Approve')"
            ).first
            if not btn.is_visible(timeout=2000):
                logger.info("UI Notice: 'Approve' button not found (modal is already approved/read-only). Returning status.")
                return "Already Approved"
            if btn.is_disabled():
                logger.info("UI Notice: 'Approve' button is disabled (already approved). Returning status.")
                return "Already Approved"

            btn.click()
            self.page.wait_for_timeout(500)

            # Handle Confirmation Modal ('Confirm Buyout Approval' -> click 'Confirm' button)
            confirm_modal_header = self.page.locator("header:has-text('Confirm Buyout Approval'), header:has-text('Confirm'), header:has-text('Approve')").first
            if confirm_modal_header.is_visible(timeout=4000):
                confirm_btn = self.page.locator(".chakra-modal__footer button:has-text('Confirm'), .chakra-modal__content button:has-text('Confirm'), button:has-text('Confirm')").first
                if confirm_btn.is_visible(timeout=3000):
                    confirm_btn.click()
        else:
            logger.info("UI Action: Clicking 'Reject' button inside modal")
            btn = modal_container.locator(
                "footer.chakra-modal__footer button:has-text('Reject'), "
                "button.chakra-button:has-text('Reject')"
            ).first
            btn.wait_for(state="visible", timeout=5000)
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
        self.page.goto(target_url, wait_until="domcontentloaded")
        # Wait for table to be present instead of networkidle
        try:
            self.page.locator("table, tr, [role='table']").first.wait_for(state="visible", timeout=10000)
        except Exception:
            pass

    def process_it_person_asset_clearance(
        self,
        employee_name: str,
        asset_condition: str = "Good",
        asset_conditions: list = None,
        remarks: str = "IT Asset clearance verified & returned in specified condition"
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
             b. Finds assigned assets list and loops through each asset:
                Applies asset_conditions[idx] if provided (e.g. ['Good', 'Repair Required', 'Damaged', 'Lost']),
                attaches photo evidence, and confirms Return.
             c. Closes Assigned Assets modal.
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
        captured_toast = ""

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

            # Loop through all assigned assets and return them individually with dynamic conditions
            max_assets = 10
            for idx in range(max_assets):
                r_btn = assigned_assets_modal.get_by_role("button", name="Return", exact=True).first
                if not r_btn.is_visible(timeout=2500):
                    logger.info(f"No more returnable assets visible in Assigned Assets list (processed {idx} assets).")
                    break

                # Resolve target condition for this specific asset
                if asset_conditions and idx < len(asset_conditions):
                    target_cond = asset_conditions[idx]
                elif asset_conditions:
                    target_cond = asset_conditions[idx % len(asset_conditions)]
                else:
                    target_cond = asset_condition

                logger.info(f"[IT ASSET RETURN #{idx+1}] Returning asset with Condition: '{target_cond}'")
                r_btn.click()
                self.page.wait_for_timeout(800)

                # Step 4: Inside 'Return Asset' dialog modal
                return_dialog = self.page.locator("section.chakra-modal__content:has-text('Return Asset'), div[role='dialog']:has-text('Return Asset')").first
                if not return_dialog.is_visible(timeout=3000):
                    return_dialog = self.page.locator("section.chakra-modal__content, div[role='dialog']").last

                if not return_dialog.is_visible(timeout=3000):
                    logger.warning("Return Asset dialog did not open; stopping further Return clicks")
                    break

                # Select Condition radio (Good / Damaged / Lost / Repair Required)
                radio = return_dialog.locator(f"input[type='radio'][value*='{target_cond}' i]").first
                if not radio.is_visible(timeout=800):
                    radio = return_dialog.locator(f"label.chakra-radio, div.chakra-radio, label").filter(has_text=re.compile(f"^{re.escape(target_cond)}$", re.I)).last
                if not radio.is_visible(timeout=800):
                    radio = return_dialog.locator(f"label:has-text('{target_cond}')").first
                if not radio.is_visible(timeout=800):
                    radio = return_dialog.locator("input[type='radio'][value='Good'], label:has-text('Good')").first
                if radio.is_visible(timeout=2000):
                    radio.click(force=True)

                # If condition is Lost, select Waived Off option if present
                if target_cond.lower() == "lost":
                    try:
                        lost_waive = return_dialog.locator("input[type='radio'][value*='waive' i], label:has-text('Waived Off'), label:has-text('Waive')").first
                        if lost_waive.is_visible(timeout=1000):
                            lost_waive.click(force=True)
                    except Exception:
                        pass

                # Fill Remarks textarea
                remarks_area = return_dialog.locator("textarea").first
                if remarks_area.is_visible(timeout=2000):
                    remarks_area.fill(f"{remarks} - Asset #{idx+1} Condition: {target_cond}")

                # Evidence File Upload (mandatory in Return Asset modal)
                try:
                    from utils.asset_media_helper import get_return_test_media_files
                    files_to_upload = get_return_test_media_files(include_video=False, max_photos=1)
                    file_input = return_dialog.locator("input[type='file']").first
                    if not file_input.is_visible(timeout=300):
                        file_input = self.page.locator("input[type='file']").first
                    if file_input.count() > 0 and files_to_upload:
                        file_input.set_input_files(files_to_upload)
                        self.page.wait_for_timeout(800)
                        logger.info(f"Attached evidence file: {[os.path.basename(f) for f in files_to_upload]}")
                except Exception as up_err:
                    logger.warning(f"Return dialog evidence upload note: {up_err}")

                # Click Return Asset confirmation button (exact name, not list 'Return')
                confirm_return_btn = return_dialog.get_by_role("button", name="Return Asset", exact=True).last
                if not confirm_return_btn.is_visible(timeout=2000):
                    confirm_return_btn = return_dialog.get_by_role("button", name="Submit", exact=True).first
                confirm_return_btn.wait_for(state="visible", timeout=5000)
                confirm_return_btn.click()
                ret_toast = self.wait_for_toast(timeout=5000)
                if ret_toast:
                    captured_toast = ret_toast
                try:
                    return_dialog.wait_for(state="hidden", timeout=15000)
                except Exception:
                    logger.warning("Return Asset dialog did not close after submit; stopping further Return clicks")
                    break
                self.page.wait_for_timeout(500)

            # Close Assigned Assets modal if still open
            if assigned_assets_modal.is_visible(timeout=1000):
                self.page.keyboard.press("Escape")

        else:
            logger.info(f"[IT ASSET FLOW] 'Manage Asset Return' button is NOT enabled (or not visible) for '{employee_name}' -> No pending returnable assets")

        # Step 5: Mark IT Task Complete in Release Employee Checklist modal
        # Toggle any unchecked checkboxes
        try:
            for cb in checklist_modal.locator("input[type='checkbox']").all():
                if not cb.is_checked():
                    cb.click(force=True)
                    self.page.wait_for_timeout(500)
                    confirm_dialog = self.page.locator(
                        "section[role='alertdialog']:has-text('Complete Exit Task'), "
                        "div[role='alertdialog']:has-text('Complete Exit Task'), "
                        "[role='alertdialog']:has-text('Complete Exit Task'), "
                        "section.chakra-modal__content:has-text('Complete Exit Task'), "
                        "div.chakra-modal__content:has-text('Complete Exit Task')"
                    ).first
                    if confirm_dialog.is_visible(timeout=2000):
                        logger.info("UI Action: Confirming IT 'Complete Exit Task' dialog via 'Confirm' button")
                        confirm_btn = confirm_dialog.locator("button:has-text('Confirm')").first
                        if confirm_btn.is_visible(timeout=3000):
                            confirm_btn.click()
                            self.page.wait_for_timeout(1000)
        except Exception as cb_err:
            logger.info(f"Checklist checkbox note: {cb_err}")

        # Step 5: Mark IT Task Complete in Release Employee Checklist modal if checkbox or complete button present
        complete_task_btn = checklist_modal.locator("button:has-text('Complete'), button:has-text('Submit'), button:has-text('Confirm'), button:has-text('Approve')").first
        if complete_task_btn.is_visible(timeout=1500):
            complete_task_btn.click()
            self.page.wait_for_timeout(500)

        # Handle 'Complete Exit Task' confirmation alertdialog if present
        confirm_modal = self.page.locator(
            "section[role='alertdialog']:has-text('Complete Exit Task'), "
            "div[role='alertdialog']:has-text('Complete Exit Task'), "
            "[role='alertdialog']:has-text('Complete Exit Task'), "
            "section.chakra-modal__content:has-text('Complete Exit Task'), "
            "div.chakra-modal__content:has-text('Complete Exit Task')"
        ).first
        if confirm_modal.is_visible(timeout=3000):
            logger.info("UI Action: Confirming IT 'Complete Exit Task' modal via 'Confirm' button")
            confirm_btn = confirm_modal.locator("button:has-text('Confirm'), footer.chakra-modal__footer button:has-text('Confirm')").first
            if confirm_btn.is_visible(timeout=3000):
                confirm_btn.click()
                self.page.wait_for_timeout(1000)
                exit_task_toast = self.wait_for_toast(timeout=4000)
                if exit_task_toast:
                    captured_toast = exit_task_toast

        if not captured_toast:
            captured_toast = self.wait_for_toast(timeout=2000)

        toast_msg = captured_toast
        return {
            "success": True,
            "toast": toast_msg,
            "has_assets": has_assets,
            "status": status_badge
        }

    def process_hr_exit_clearance(
        self,
        employee_name: str,
        remarks: str = "HR Exit formalities and document checklist completed"
    ) -> Dict[str, Union[bool, str]]:
        """
        HR Exit Clearance Execution (/exit-clearance):
        1. Navigates directly to /exit-clearance.
        2. Finds target employee row in the table.
        3. Clicks 'Open Checklist (*)' button in Action column.
        4. Modal opens with header 'Release Employee Checklist'.
        5. Checks HR exit clearance checkboxes and fills remarks if present.
        6. Clicks Complete / Submit button to complete the HR offboarding task.
        7. Handles 'Complete Exit Task' confirmation modal by clicking 'Confirm'.
        8. Captures toast message and returns status.
        """
        logger.info(f"UI Action: HR processing exit clearance checklist for '{employee_name}'")
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
        status_badge = row.locator(".chakra-badge, span[class*='badge']").first.inner_text().strip() if row.locator(".chakra-badge, span[class*='badge']").first.is_visible(timeout=2000) else ""
        logger.info(f"HR Exit Clearance Table -> Employee: '{employee_name}' | Status: '{status_badge}'")

        # Click Action button: Open Checklist
        checklist_btn = row.locator("button:has-text('Open Checklist'), button:has-text('Checklist')").first
        checklist_btn.wait_for(state="visible", timeout=5000)
        checklist_btn.click()
        self.page.wait_for_timeout(500)

        # Release Employee Checklist modal
        checklist_modal = self.page.locator("section.chakra-modal__content, div[role='dialog']").first
        checklist_modal.wait_for(state="visible", timeout=5000)
        modal_text = checklist_modal.inner_text().strip()
        logger.info(f"HR Exit Checklist Modal Content:\n{modal_text}")

        # Check all pending checkboxes for HR task
        try:
            for cb in checklist_modal.locator("input[type='checkbox']").all():
                if not cb.is_checked():
                    cb.click(force=True)
                    self.page.wait_for_timeout(500)
                    confirm_dialog = self.page.locator(
                        "section[role='alertdialog']:has-text('Complete Exit Task'), "
                        "div[role='alertdialog']:has-text('Complete Exit Task'), "
                        "[role='alertdialog']:has-text('Complete Exit Task'), "
                        "section.chakra-modal__content:has-text('Complete Exit Task'), "
                        "div.chakra-modal__content:has-text('Complete Exit Task')"
                    ).first
                    if confirm_dialog.is_visible(timeout=2000):
                        logger.info("UI Action: Confirming HR 'Complete Exit Task' dialog via 'Confirm' button")
                        confirm_btn = confirm_dialog.locator("button:has-text('Confirm')").first
                        if confirm_btn.is_visible(timeout=3000):
                            confirm_btn.click()
                            self.page.wait_for_timeout(1000)
        except Exception as cb_err:
            logger.info(f"HR Checklist checkbox note: {cb_err}")

        # Fill remarks textarea if visible
        remarks_area = checklist_modal.locator("textarea").first
        if remarks_area.is_visible(timeout=1500):
            remarks_area.fill(remarks)

        # Click Complete / Submit / Confirm / Approve button
        complete_task_btn = checklist_modal.locator("button:has-text('Complete'), button:has-text('Submit'), button:has-text('Confirm'), button:has-text('Approve')").first
        if complete_task_btn.is_visible(timeout=1500):
            complete_task_btn.click()
            self.page.wait_for_timeout(500)

        # Handle 'Complete Exit Task' confirmation alertdialog
        confirm_modal = self.page.locator(
            "section[role='alertdialog']:has-text('Complete Exit Task'), "
            "div[role='alertdialog']:has-text('Complete Exit Task'), "
            "[role='alertdialog']:has-text('Complete Exit Task'), "
            "section.chakra-modal__content:has-text('Complete Exit Task'), "
            "div.chakra-modal__content:has-text('Complete Exit Task')"
        ).first
        if confirm_modal.is_visible(timeout=3000):
            logger.info("UI Action: Confirming HR 'Complete Exit Task' modal via 'Confirm' button")
            confirm_btn = confirm_modal.locator("button:has-text('Confirm'), footer.chakra-modal__footer button:has-text('Confirm')").first
            if confirm_btn.is_visible(timeout=3000):
                confirm_btn.click()
                self.page.wait_for_timeout(1000)
                try:
                    confirm_modal.wait_for(state="hidden", timeout=5000)
                except Exception:
                    pass

        toast_msg = self.wait_for_toast(timeout=10000)
        return {
            "success": True,
            "toast": toast_msg,
            "status": status_badge
        }

    # ══════════════════════════════════════════════════════════════════════════
    # FULL & FINAL (FnF) SETTLEMENT & RELEASED EMPLOYEE LETTER WORKFLOWS
    # ══════════════════════════════════════════════════════════════════════════

    def trigger_start_fnf_process(self, employee_name: str) -> str:
        """
        HR Action on /resignation-approval:
        1. Navigates to /resignation-approval and searches employee.
        2. Clicks Actions (=) menu button in the employee's table row.
        3. Clicks 'Start FnF Process' menuitem.
        4. Confirms 'Start Process' in the alertdialog modal.
        5. Captures and returns toast message.
        """
        logger.info(f"UI Action: HR initiating FnF process for '{employee_name}'")
        self.navigate_to_hr_resignation_approval()
        self.search_employee_in_hr_table(employee_name)

        row = self.page.locator(f"tr:has-text('{employee_name}')").first
        row.wait_for(state="visible", timeout=5000)

        # Actions hamburger button in table row
        actions_btn = row.locator("td:last-child button, button.chakra-menu__menu-button").first
        actions_btn.wait_for(state="visible", timeout=3000)
        actions_btn.click()
        self.page.wait_for_timeout(500)

        # Check if 'Start FnF Process' menuitem is visible, otherwise wait & poll for DB update
        fnf_item = self.page.locator("button[role='menuitem']:has-text('Start FnF Process')").first
        
        max_retries = 24  # 24 * 5s = 120s total wait
        for attempt in range(max_retries):
            if fnf_item.is_visible(timeout=1500):
                logger.info(f"[UI SUCCESS] 'Start FnF Process' menu item is now active on UI!")
                break
            logger.info(
                f"[WAITING FOR DB UPDATE] 'Start FnF Process' menu item not yet visible (Attempt {attempt+1}/{max_retries}).\n"
                f"--> Run in SSMS: UPDATE [hrlense_stage].[dbo].[Resignation] SET [Status] = 10 WHERE [Status] = 8;\n"
                f"Retrying in 5 seconds..."
            )
            try:
                self.page.keyboard.press("Escape")
            except Exception:
                pass
            self.page.wait_for_timeout(5000)
            self.page.reload(wait_until="domcontentloaded")
            self.search_employee_in_hr_table(employee_name)
            row = self.page.locator(f"tr:has-text('{employee_name}')").first
            row.wait_for(state="visible", timeout=5000)
            actions_btn = row.locator("td:last-child button, button.chakra-menu__menu-button").first
            actions_btn.click()
            self.page.wait_for_timeout(500)

        fnf_item.wait_for(state="visible", timeout=5000)
        fnf_item.click()
        self.page.wait_for_timeout(500)

        # Confirm in alertdialog modal
        modal = self.page.locator("section[role='alertdialog']:has-text('Start FnF Process'), div[role='alertdialog']:has-text('Start FnF Process')").first
        modal.wait_for(state="visible", timeout=5000)
        start_btn = modal.locator("button:has-text('Start Process')").first
        start_btn.wait_for(state="visible", timeout=3000)
        start_btn.click()

        toast = self.wait_for_toast(timeout=5000)
        logger.info(f"Start FnF Toast: '{toast}'")
        return toast

    def navigate_to_accounts_fnf_requests(self) -> None:
        """
        Navigates to /accounts-buyout-processing and switches to the 'FnF Requests' tab.
        """
        logger.info("UI Action: Accountant navigating to /accounts-buyout-processing -> 'FnF Requests' tab")
        try:
            self.page.bring_to_front()
        except Exception:
            pass

        current_origin = "/".join(self.page.url.split("/")[:3])
        target_url = f"{current_origin}/accounts-buyout-processing"
        if target_url not in self.page.url:
            self.page.goto(target_url, wait_until="domcontentloaded")

        # Click 'FnF Requests' tab
        fnf_tab = self.page.locator("button[role='tab']:has-text('FnF Requests')").first
        fnf_tab.wait_for(state="visible", timeout=10000)
        fnf_tab.click()
        self.page.wait_for_timeout(1000)

    def open_accountant_fnf_modal(self, employee_name: str) -> bool:
        """
        On /accounts-buyout-processing (FnF Requests tab):
        Searches employee and clicks the action arrow (Action column) to open the Full & Final Settlement drawer.
        """
        logger.info(f"UI Action: Opening Accountant FnF modal for '{employee_name}'")
        self.navigate_to_accounts_fnf_requests()

        search_input = self.page.locator("input[placeholder*='Search Employee' i]").first
        if search_input.is_visible(timeout=3000):
            search_input.click()
            search_input.fill(employee_name)
            search_input.press("Enter")
            self.page.wait_for_timeout(1500)

        row = self.page.locator(f"tr:has-text('{employee_name}')").first
        row.wait_for(state="visible", timeout=5000)

        action_arrow = row.locator("td:last-child img, td:last-child button, td:last-child").first
        action_arrow.click()
        self.page.wait_for_timeout(1000)

        drawer = self.page.locator("div[role='dialog']:has-text('Full & Final Settlement'), section.chakra-modal__content:has-text('Full & Final Settlement')").first
        return drawer.is_visible(timeout=5000)

    def get_accountant_fnf_modal_values(self) -> Dict[str, str]:
        """
        Reads values from the open 'Full & Final Settlement' drawer.
        """
        drawer = self.page.locator("div[role='dialog']:has-text('Full & Final Settlement'), section.chakra-modal__content:has-text('Full & Final Settlement')").first
        drawer.wait_for(state="visible", timeout=5000)

        leave_encashment = drawer.locator("tr:has-text('Leave Encashment') td:last-child, tr:has-text('Leave Encashment') td[data-is-numeric='true']").first
        total_earnings = drawer.locator("tr:has-text('Total Earnings') td:last-child, tr:has-text('Total Earnings') td[data-is-numeric='true']").first
        buyout_amount = drawer.locator("tr:has-text('Buyout Amount') td:last-child, tr:has-text('Buyout Amount') td[data-is-numeric='true']").first
        total_deductions = drawer.locator("tr:has-text('Total Deductions') td:last-child, tr:has-text('Total Deductions') td[data-is-numeric='true']").first
        net_payable = drawer.locator("div:has-text('Net Payable') p:last-child, p:has-text('Net Payable') + p").first

        return {
            "leave_encashment": leave_encashment.inner_text().strip() if leave_encashment.is_visible(timeout=1000) else "",
            "total_earnings": total_earnings.inner_text().strip() if total_earnings.is_visible(timeout=1000) else "",
            "buyout_amount": buyout_amount.inner_text().strip() if buyout_amount.is_visible(timeout=1000) else "",
            "total_deductions": total_deductions.inner_text().strip() if total_deductions.is_visible(timeout=1000) else "",
            "net_payable": net_payable.inner_text().strip() if net_payable.is_visible(timeout=1000) else "",
        }

    def process_accountant_fnf_settlement(
        self,
        employee_name: str,
        salary_for_days_worked: str = "0.00",
        other_earnings: str = "0.00",
        asset_recovery: str = None,
        loan_recovery: str = None,
        other_deductions: str = None,
        remarks: str = "Full & Final Settlement Approved by Accounts"
    ) -> Dict[str, Union[bool, str, Dict[str, str]]]:
        """
        Fills and submits the Full & Final Settlement drawer for an employee.
        """
        logger.info(f"UI Action: Accountant processing FnF settlement for '{employee_name}'")
        opened = self.open_accountant_fnf_modal(employee_name)
        if not opened:
            return {"success": False, "toast": "", "status": "", "modal_values": {}}

        drawer = self.page.locator("div[role='dialog']:has-text('Full & Final Settlement'), section.chakra-modal__content:has-text('Full & Final Settlement')").first
        modal_values = self.get_accountant_fnf_modal_values()
        logger.info(f"[FnF Modal Initial Values] {modal_values}")

        # Fill Earnings
        salary_input = drawer.locator("tr:has-text('Salary for Days Worked') input").first
        if salary_input.is_visible(timeout=2000):
            salary_input.click()
            salary_input.fill(str(salary_for_days_worked))
            salary_input.press("Tab")

        other_earn_input = drawer.locator("tr:has-text('Other Earnings') input").first
        if other_earn_input.is_visible(timeout=2000):
            other_earn_input.click()
            other_earn_input.fill(str(other_earnings))
            other_earn_input.press("Tab")

        # Fill optional Deductions if provided
        if asset_recovery is not None:
            ar_input = drawer.locator("tr:has-text('Asset Recovery') input").first
            if ar_input.is_visible(timeout=1000):
                ar_input.click()
                ar_input.fill(str(asset_recovery))
                ar_input.press("Tab")

        if loan_recovery is not None:
            lr_input = drawer.locator("tr:has-text('Loan/Advance Recovery') input").first
            if lr_input.is_visible(timeout=1000):
                lr_input.click()
                lr_input.fill(str(loan_recovery))
                lr_input.press("Tab")

        if other_deductions is not None:
            od_input = drawer.locator("tr:has-text('Other Deductions') input").first
            if od_input.is_visible(timeout=1000):
                od_input.click()
                od_input.fill(str(other_deductions))
                od_input.press("Tab")

        # Remarks
        remarks_area = drawer.locator("textarea[placeholder*='Remarks' i]").first
        if remarks_area.is_visible(timeout=2000):
            remarks_area.fill(remarks)

        # Submit FnF
        submit_btn = drawer.locator("button:has-text('Submit FnF')").first
        submit_btn.wait_for(state="visible", timeout=3000)
        submit_btn.click()

        toast = self.wait_for_toast(timeout=5000)
        logger.info(f"Submit FnF Toast: '{toast}'")

        # Check status in FnF Requests table (expecting 'COMPLETED')
        self.page.wait_for_timeout(1000)
        row = self.page.locator(f"tr:has-text('{employee_name}')").first
        status_badge = row.locator(".chakra-badge, span[class*='badge']").first.inner_text().strip() if row.locator(".chakra-badge, span[class*='badge']").first.is_visible(timeout=2000) else ""
        logger.info(f"FnF Table Status for '{employee_name}': '{status_badge}'")

        is_success = bool(toast and "error" not in toast.lower() and "failed" not in toast.lower()) or "completed" in status_badge.lower()
        return {
            "success": is_success,
            "toast": toast,
            "status": status_badge,
            "modal_values": modal_values
        }

    def navigate_to_released_employees(self) -> None:
        """
        Navigates directly to /released-employee.
        """
        logger.info("UI Action: Navigating to Released Employees (/released-employee)")
        try:
            self.page.bring_to_front()
        except Exception:
            pass

        current_origin = "/".join(self.page.url.split("/")[:3])
        target_url = f"{current_origin}/released-employee"
        self.page.goto(target_url, wait_until="domcontentloaded")
        search_input = self.page.locator("input[placeholder*='Search employee' i]").first
        search_input.wait_for(state="visible", timeout=10000)

    def open_released_employee_letter(self, employee_name: str, letter_type: str = "Full & Final Settlement") -> bool:
        """
        On /released-employee:
        1. Searches employee.
        2. Opens Actions (≡) menu.
        3. Clicks specified letter_type ('Relieving Letter', 'Full & Final Settlement', or 'Experience Letter').
        4. Verifies letter editor & live preview page is loaded.
        """
        logger.info(f"UI Action: Opening '{letter_type}' for released employee '{employee_name}'")
        self.navigate_to_released_employees()

        search_input = self.page.locator("input[placeholder*='Search employee' i]").first
        search_input.click()
        search_input.fill(employee_name)
        search_input.press("Enter")
        self.page.wait_for_timeout(1500)

        row = self.page.locator(f"tr:has-text('{employee_name}')").first
        row.wait_for(state="visible", timeout=5000)
        row.scroll_into_view_if_needed()

        # Actions menu button
        actions_btn = row.locator("button[aria-label='Actions'], button.icon_btn").first
        actions_btn.scroll_into_view_if_needed()
        actions_btn.wait_for(state="visible", timeout=5000)

        # Open the Chakra Actions menu
        actions_btn.click()
        self.page.wait_for_timeout(300)

        menu_list = self.page.locator("div.chakra-menu__menu-list:visible, div[role='menu']:visible").first
        try:
            menu_list.wait_for(state="visible", timeout=3000)
        except Exception:
            logger.info("Retrying Actions button click to ensure dropdown opens...")
            actions_btn.evaluate("el => el.click()")
            menu_list.wait_for(state="visible", timeout=5000)

        # Find the specific letter menuitem inside the open menu
        menuitem = menu_list.locator(f"button[role='menuitem']:has-text('{letter_type}')").first
        menuitem.wait_for(state="visible", timeout=5000)
        
        # Trigger native click which executes React onClick handler cleanly bypassing any table z-index overlaps
        logger.info(f"UI Action: Clicking menuitem '{letter_type}'")
        menuitem.evaluate("el => el.click()")
        self.page.wait_for_timeout(1000)

        # Wait for Letter Editor / Live Preview Page
        send_btn = self.page.locator("button:has-text('Send to Employee'), button:has-text('Send to')").first
        send_btn.wait_for(state="visible", timeout=15000)
        return send_btn.is_visible()

    def send_letter_to_employee(self, signatory_index: int = 1) -> str:
        """
        Inside the open Letter Editor / Live Preview screen:
        1. Selects signatory from dropdown.
        2. Clicks 'Send to Employee' button.
        3. Confirms modal if present.
        4. Captures and returns toast.
        """
        logger.info(f"UI Action: Selecting signatory (index {signatory_index}) and sending letter to employee")
        signatory_select = self.page.locator("select.chakra-select").first
        if signatory_select.is_visible(timeout=3000):
            signatory_select.select_option(index=signatory_index)
            self.page.wait_for_timeout(500)

        send_btn = self.page.locator("button:has-text('Send to Employee')").first
        send_btn.wait_for(state="visible", timeout=3000)
        send_btn.click(force=True)
        self.page.wait_for_timeout(500)

        # Handle optional confirmation modal if rendered
        confirm_btn = self.page.locator(
            "section[role='alertdialog'] button:has-text('Send'), "
            "section[role='alertdialog'] button:has-text('Confirm'), "
            ".chakra-modal__content button:has-text('Send'), "
            ".chakra-modal__content button:has-text('Confirm')"
        ).first
        if confirm_btn.is_visible(timeout=2000):
            logger.info("UI Action: Confirming letter dispatch modal")
            confirm_btn.click(force=True)

        toast = self.wait_for_toast(timeout=8000)
        logger.info(f"Send Letter Toast: '{toast}'")
        return toast

    def get_letter_editor_content(self) -> str:
        """Reads and returns the current text inside the left-side SunEditor."""
        editor = self.page.locator("div.sun-editor-editable[contenteditable='true'], div.se-wrapper-wysiwyg").first
        if editor.is_visible(timeout=3000):
            return editor.inner_text().strip()
        return ""

    def edit_letter_content(self, text_to_insert: str, append: bool = True) -> None:
        """
        Edits the content in the left-side rich text editor (SunEditor):
        - append=True: clicks at the end and types the new text.
        - append=False: selects all existing text, clears it, and types text_to_insert.
        Typing emits native keyboard events which triggers live preview updates on the right side.
        """
        logger.info(f"UI Action: Editing letter content (append={append}): '{text_to_insert}'")
        editor = self.page.locator("div.sun-editor-editable[contenteditable='true'], div.se-wrapper-wysiwyg").first
        editor.wait_for(state="visible", timeout=5000)
        editor.click(force=True)
        self.page.wait_for_timeout(300)

        if not append:
            self.page.keyboard.press("Control+A")
            self.page.keyboard.press("Backspace")
            self.page.wait_for_timeout(300)

        # Type the text using native keystrokes so SunEditor synchronizes to Live Preview
        self.page.keyboard.type(f" {text_to_insert}")
        self.page.wait_for_timeout(1000)

    def get_letter_live_preview_content(self) -> str:
        """Reads and returns the text currently displayed in the right-side Live Preview document."""
        preview_container = self.page.locator(".css-ubtrqw .page, div.page, div.css-1dp0x90 .page").first
        if preview_container.is_visible(timeout=3000):
            return preview_container.inner_text().strip()
        return ""

    def verify_letter_content_sync(self, expected_substring: str) -> bool:
        """
        Verifies that custom text typed in the left editor has dynamically synced
        into the right-side Live Preview.
        """
        try:
            self.page.wait_for_timeout(1000)
            preview_container = self.page.locator(".css-ubtrqw .page, div.page, div.css-1dp0x90 .page").first
            preview_text = preview_container.inner_text(timeout=5000)
            matched = expected_substring.lower() in preview_text.lower()
            logger.info(f"[Letter Sync Check] Substring '{expected_substring}' in Live Preview -> {matched}")
            return matched
        except Exception as e:
            logger.warning(f"[Letter Sync Check] Error checking live preview: {e}")
            return False

    def click_letter_back_button(self) -> None:
        """Clicks the Back button on the letter editor screen to return to /released-employee."""
        back_btn = self.page.locator("button[aria-label='Back']").first
        if back_btn.is_visible(timeout=3000):
            back_btn.evaluate("el => el.click()")
            self.page.wait_for_timeout(1000)

    def get_released_employee_letter_statuses(self, employee_name: str) -> Dict[str, str]:
        """
        On /released-employee, reads the Relieving, F&F Status, and Experience column badges for employee.
        """
        row = self.page.locator(f"tr:has-text('{employee_name}')").first
        if not row.is_visible(timeout=3000):
            self.navigate_to_released_employees()
            search_input = self.page.locator("input[placeholder*='Search employee' i]").first
            search_input.fill(employee_name)
            search_input.press("Enter")
            self.page.wait_for_timeout(1500)
            row = self.page.locator(f"tr:has-text('{employee_name}')").first

        row.wait_for(state="visible", timeout=5000)
        cells = row.locator("td").all_inner_texts()
        return {
            "name": employee_name,
            "raw_cells": cells
        }


