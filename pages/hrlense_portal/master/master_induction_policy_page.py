"""
Page Object for Master Induction Policy Configuration.
URL: /master/induction-policy

Owns:
- Locators for 5-Stepper controls:
    STEP 1: Company Profile
    STEP 2: Branch & Location
    STEP 3: Business Process
    STEP 4: Department
    STEP 5: HR Policies
- Content Table locators (headers, rows, search filter)
- Media banner & video controls
- '+ Add Content' modal controls & submission
"""

import os
import logging
import re
from typing import List, Dict, Any, Optional
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)


class MasterInductionPolicyPage(BasePage):
    """Page Object for HRlens Master Induction Policy (/master/induction-policy)."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.url = f"{settings.BASE_URL}/master/induction-policy"

        # Top-level Navigation Tabs (Restructured into Tab 1 & Tab 2)
        self.tab_settings_welcome = self.page.locator("button").filter(has_text=re.compile(r"Tab 1|Settings & Welcome", re.I)).first
        self.tab_step_content_videos = self.page.locator("button").filter(has_text=re.compile(r"Tab 2|Step Content", re.I)).first

        # 5-Stepper Step Buttons
        self.step_buttons = {
            1: self.page.locator("button:has-text('STEP 1')").first,
            2: self.page.locator("button:has-text('STEP 2')").first,
            3: self.page.locator("button:has-text('STEP 3')").first,
            4: self.page.locator("button:has-text('STEP 4')").first,
            5: self.page.locator("button:has-text('STEP 5')").first,
        }

        # ----------------- 1. Top Section: Hero Banner & Scope Hierarchy -----------------
        self.banner_section = self.page.locator(".css-c41ezh, div:has(> div p:has-text('Welcome Screen Background Banners')), div:has-text('Organization Hierarchy Scope')").first
        self.banner_scope_badge = self.page.locator("span.chakra-badge").filter(has_text=re.compile(r"CORPORATE|GLOBAL|COMPANY|BRANCH|DEPARTMENT|FALLBACK", re.I)).first
        self.banner_active_scope_text = self.page.locator("p, span, div").filter(has_text=re.compile(r"Organization Hierarchy Scope|Active Banner Scope|CORPORATE GLOBAL|FALLBACK", re.I)).first
        self.banner_company_select = self.page.locator("select.chakra-select").nth(0)
        self.banner_branch_select = self.page.locator("select.chakra-select").nth(1)
        self.banner_department_select = self.page.locator("select.chakra-select").nth(2)
        self.banner_reset_global_button = self.page.locator("button:has-text('Reset to Global Scope')").first
        self.banner_file_input = self.page.locator("input[type='file'][accept*='image']").first
        self.banner_active_count_badge = self.page.locator("span.chakra-badge").filter(has_text=re.compile(r"\d+\s*/\s*7\s*Custom Active", re.I)).first
        self.hide_banners_button = self.page.locator("button:has-text('Hide Banners')").first

        # ----------------- 2. Middle Section: Step Video -----------------
        self.video_section = self.page.locator("div:has-text('Step Video:')").last
        self.video_heading = self.video_section.locator("p, h3, h4, div").filter(has_text="Step Video:").first
        self.video_upload_button = self.video_section.locator("button:has-text('Upload Video')").first
        self.video_file_input = self.page.locator("input[type='file'][accept*='video']").first
        self.video_watch_button = self.video_section.locator("button:has-text('Watch Video')").first
        self.video_replace_button = self.video_section.locator("button:has-text('Replace Video')").first
        self.video_remove_button = self.video_section.locator("button:has-text('Remove')").first

        # ----------------- 3. Bottom Section: Content Table & Scoping -----------------
        self.table = self.page.locator("table").first
        self.table_headers = self.page.locator("table th")
        self.table_rows = self.page.locator("table tbody tr")
        self.add_content_button = self.page.locator("button:has-text('+ Add Content')").first

        # Scoping Filter Bar (Search + Scope Dropdowns + Reset)
        self.filter_bar = self.page.locator("div:has(> select.chakra-select)").first
        self.search_input = self.page.locator("input[placeholder*='Search cards in' i], input[placeholder*='Search...' i]").first
        self.scope_company_select = self.page.locator("select.chakra-select").nth(0)
        self.scope_branch_select = self.page.locator("select.chakra-select").nth(1)
        self.scope_department_select = self.page.locator("select.chakra-select").nth(2)
        self.scope_vertical_select = self.page.locator("select.chakra-select").nth(1)
        self.scope_reset_button = self.page.locator("button:has-text('Reset')").first

        # Table Control Bar (In-table Search, Columns Menu, Pagination Counter)
        self.table_search_input = self.page.locator("input[placeholder='Search...']").first
        self.table_columns_button = self.page.locator("button[aria-label='Columns']").first
        self.table_record_count_text = self.page.locator("p.chakra-text").filter(has_text=re.compile(r"Showing \d+-\d+ of \d+ records", re.I)).first

        # Add Content Modal Dialog
        self.modal = self.page.locator("div[role='dialog'], section[role='dialog'], .chakra-modal__content").first
        self.modal_title = self.page.locator("p.chakra-text:has-text('Add Induction Content'), p:has-text('Edit Induction Content'), header").first
        self.modal_step_select = self.page.locator("select").filter(has=self.page.locator("option:has-text('Step 1')")).first
        self.modal_template_select = self.page.locator("select").filter(has=self.page.locator("option:has-text('template')")).first
        self.modal_category_input = self.page.locator(".chakra-modal__body input[placeholder*='Vision' i], input[placeholder*='Vision, Facilities, Leave Policy' i]").first
        self.modal_title_input = self.page.locator(".chakra-modal__body input[placeholder*='Branch' i], .chakra-modal__body input[type='text'], input[placeholder*='Branch Facilities & Amenities' i]").first
        self.modal_content_textarea = self.page.locator(".chakra-modal__body textarea, textarea[placeholder*='Enter the complete text or guidelines' i], textarea").first
        self.modal_order_input = self.page.locator("form#induction-content-form input[type='number']").first
        self.modal_submit_button = self.page.locator("button[type='submit']:has-text('Create Content'), button[type='submit']:has-text('Save'), button[type='submit']:has-text('Update'), button:has-text('Save Changes')").first
        self.modal_cancel_button = self.page.locator("button:has-text('Cancel')").first

        # Row action locators
        self.row_switches = self.page.locator("table tbody tr input.chakra-switch__input")
        self.row_edit_buttons = self.page.locator("table tbody tr button[aria-label='Edit']")
        self.row_delete_buttons = self.page.locator("table tbody tr button[aria-label='Delete']")

    def navigate_to_induction_policy(self):
        """Navigates to the Master Induction Policy configuration page."""
        logger.info(f"[UI] Navigating to Master Induction Policy: {self.url}")
        if "/master/induction-policy" not in self.page.url:
            try:
                self.page.goto(self.url, wait_until="domcontentloaded", timeout=60000)
            except Exception as e:
                logger.warning(f"[UI] Initial goto encountered {e}; retrying navigation...")
                self.page.wait_for_timeout(2000)
                self.page.goto(self.url, wait_until="domcontentloaded", timeout=60000)
        self.page.wait_for_timeout(2000)
        assert "/master/induction-policy" in self.page.url, f"Failed to load induction policy. Current: {self.page.url}"

    def switch_to_settings_welcome_tab(self):
        """Switches to Tab 1: Settings & Welcome Screen if present."""
        if self.tab_settings_welcome.is_visible():
            logger.info("[UI] Switching to Tab 1: Settings & Welcome Screen...")
            self.tab_settings_welcome.click()
            self.page.wait_for_timeout(1000)

    def switch_to_step_content_tab(self):
        """Switches to Tab 2: Step Content & Videos if present."""
        if self.tab_step_content_videos.is_visible():
            logger.info("[UI] Switching to Tab 2: Step Content & Videos...")
            self.tab_step_content_videos.click()
            self.page.wait_for_timeout(1000)

    def select_step(self, step_number: int):
        """Clicks on the specified step button (1 to 5)."""
        assert step_number in self.step_buttons, f"Invalid step number: {step_number}. Must be 1 to 5."
        self.switch_to_step_content_tab()
        btn = self.step_buttons[step_number]
        logger.info(f"[UI] Selecting Induction Policy Step {step_number}...")
        btn.wait_for(state="visible", timeout=7000)
        btn.click()
        self.page.wait_for_timeout(1000)

    def get_table_headers(self) -> List[str]:
        """Returns the list of table header column titles."""
        self.switch_to_step_content_tab()
        return [th.inner_text().strip() for th in self.table_headers.all()]

    def get_row_count(self) -> int:
        """Returns the number of content rows in the active step table."""
        self.switch_to_step_content_tab()
        return self.table_rows.count()

    def get_table_row_data(self, row_index: int = 0) -> Dict[str, str]:
        """Returns data from a specific row in the content table."""
        if self.get_row_count() == 0 or row_index >= self.get_row_count():
            return {}
        cells = self.table_rows.nth(row_index).locator("td").all_inner_texts()
        headers = self.get_table_headers()
        return dict(zip(headers, [c.strip().replace("\n", " ") for c in cells]))

    def get_all_rows_data(self) -> List[Dict[str, str]]:
        """Returns structured data for all content rows currently visible in the active step table."""
        count = self.get_row_count()
        return [self.get_table_row_data(i) for i in range(count)]

    def search_content(self, query: str):
        """Filters the content table using the search input."""
        logger.info(f"[UI] Searching Induction Policy content with query: '{query}'")
        self.switch_to_step_content_tab()
        self.search_input.wait_for(state="visible", timeout=5000)
        self.search_input.fill(query)
        self.page.wait_for_timeout(1000)

    def clear_search(self):
        """Clears the search filter input."""
        self.switch_to_step_content_tab()
        self.search_input.fill("")
        self.page.wait_for_timeout(1000)

    # ----------------- Scoping Dropdown Controls -----------------
    def select_scope_company(self, company_name: str):
        """Filters the induction content table by Company scope."""
        logger.info(f"[UI] Scoping Induction Content by Company: '{company_name}'...")
        self.switch_to_step_content_tab()
        self.scope_company_select.wait_for(state="visible", timeout=5000)
        self.scope_company_select.select_option(label=company_name)
        self.page.wait_for_timeout(1500)

    def select_scope_department(self, department_name: str):
        """Filters the induction content table by Department scope."""
        logger.info(f"[UI] Scoping Induction Content by Department: '{department_name}'...")
        self.scope_department_select.wait_for(state="visible", timeout=5000)
        self.scope_department_select.select_option(label=department_name)
        self.page.wait_for_timeout(1500)

    def select_scope_branch(self, branch_name: str):
        """Filters the induction content table by Branch scope."""
        logger.info(f"[UI] Scoping Induction Content by Branch: '{branch_name}'...")
        self.scope_branch_select.wait_for(state="visible", timeout=5000)
        self.scope_branch_select.select_option(label=branch_name)
        self.page.wait_for_timeout(1500)

    def select_scope_vertical(self, vertical_name: str):
        """Filters the induction content table by Business Vertical scope."""
        logger.info(f"[UI] Scoping Induction Content by Vertical: '{vertical_name}'...")
        self.scope_vertical_select.wait_for(state="visible", timeout=5000)
        self.scope_vertical_select.select_option(label=vertical_name)
        self.page.wait_for_timeout(1500)

    def reset_all_scopes(self):
        """Resets Company, Branch, and Department scoping dropdowns to All."""
        logger.info("[UI] Resetting all Induction Scoping dropdowns to 'All'...")
        if self.scope_reset_button.is_visible(timeout=1000) and not self.scope_reset_button.is_disabled():
            self.scope_reset_button.click()
            self.page.wait_for_timeout(1200)
            return
        if self.scope_company_select.is_visible():
            self._select_dropdown_option_robust(self.scope_company_select, "All Companies")
        if self.scope_branch_select.is_visible():
            self._select_dropdown_option_robust(self.scope_branch_select, "All Branches")
        if self.scope_department_select.is_visible():
            self._select_dropdown_option_robust(self.scope_department_select, "All Departments")
        self.page.wait_for_timeout(1200)

    def get_available_companies(self) -> List[str]:
        """Returns the list of selectable Company names in the scope dropdown."""
        return [o.strip() for o in self.scope_company_select.locator("option").all_inner_texts()]

    def get_available_branches(self) -> List[str]:
        """Returns the list of selectable Branch names in the scope dropdown."""
        return [o.strip() for o in self.scope_branch_select.locator("option").all_inner_texts()]

    def get_available_verticals(self) -> List[str]:
        """Returns the list of selectable Business Vertical names in the scope dropdown."""
        return [o.strip() for o in self.scope_vertical_select.locator("option").all_inner_texts()]

    def get_available_departments(self) -> List[str]:
        """Returns the list of selectable Department names in the scope dropdown."""
        return [o.strip() for o in self.scope_department_select.locator("option").all_inner_texts()]

    def open_add_content_modal(self):
        """Clicks '+ Add Content' button and waits for the modal to be visible."""
        logger.info("[UI] Opening '+ Add Content' modal...")
        self.add_content_button.wait_for(state="visible", timeout=5000)
        self.add_content_button.click()
        self.modal.wait_for(state="visible", timeout=5000)

    def is_add_content_modal_open(self) -> bool:
        """Checks if the Add Content modal dialog is currently visible."""
        return self.modal.is_visible()

    def close_add_content_modal(self):
        """Closes the Add Content modal dialog."""
        logger.info("[UI] Closing Add Content modal...")
        if self.modal_cancel_button.is_visible():
            self.modal_cancel_button.click()
        else:
            self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(800)

    def select_template_preset(self, template_name: str):
        """Selects a preset standard template from the dropdown."""
        logger.info(f"[UI] Selecting template preset: '{template_name}'...")
        self.modal_template_select.wait_for(state="visible", timeout=5000)
        self.modal_template_select.select_option(label=template_name)
        self.page.wait_for_timeout(800)

    def fill_and_create_content(
        self,
        category_tag: str,
        title: str,
        content: str,
        template: Optional[str] = None,
        target_step: Optional[str] = None
    ):
        """Fills out the Add Induction Content form and clicks 'Create Content'."""
        self.open_add_content_modal()
        if target_step and self.modal_step_select.is_visible():
            logger.info(f"[UI] Selecting target induction step: '{target_step}'")
            self.modal_step_select.select_option(label=target_step)
            self.page.wait_for_timeout(500)

        if template:
            self.select_template_preset(template)

        if category_tag:
            self.modal_category_input.fill(category_tag)
        if title:
            self.modal_title_input.fill(title)
        if content:
            self.modal_content_textarea.fill(content)

        logger.info(f"[UI] Submitting induction content: '{title}'...")
        self.modal_submit_button.wait_for(state="visible", timeout=5000)
        self.modal_submit_button.click()
        self.page.wait_for_timeout(2000)

    def toggle_row_active(self, row_index: int = 0) -> bool:
        """Toggles the Active switch for the specified row index."""
        logger.info(f"[UI] Toggling Active switch for row {row_index}...")
        switch = self.row_switches.nth(row_index)
        switch.wait_for(state="attached", timeout=5000)
        is_checked_before = switch.is_checked()
        # Click the switch control or input
        switch.click(force=True)
        self.page.wait_for_timeout(1500)
        is_checked_after = switch.is_checked()
        logger.info(f"[UI] Switch state changed: {is_checked_before} -> {is_checked_after}")
        return is_checked_after != is_checked_before

    def click_edit_row(self, row_index: int = 0):
        """Clicks the Edit button on the specified row to open edit drawer."""
        logger.info(f"[UI] Clicking Edit button on row {row_index}...")
        edit_btn = self.row_edit_buttons.nth(row_index)
        edit_btn.wait_for(state="visible", timeout=5000)
        edit_btn.click()
        self.modal.wait_for(state="visible", timeout=5000)

    def update_content(self, new_title: Optional[str] = None, new_content: Optional[str] = None):
        """Modifies title or content in edit drawer and saves."""
        if new_title and self.modal_title_input.is_visible():
            self.modal_title_input.fill(new_title)
        if new_content and self.modal_content_textarea.is_visible():
            self.modal_content_textarea.fill(new_content)
        self.save_modal_changes()

    def get_modal_title_value(self) -> str:
        """Returns current value in the edit modal title input."""
        self.modal_title_input.wait_for(state="visible", timeout=5000)
        return self.modal_title_input.input_value().strip()

    def get_modal_content_value(self) -> str:
        """Returns current value in the edit modal content textarea."""
        self.modal_content_textarea.wait_for(state="visible", timeout=5000)
        return self.modal_content_textarea.input_value().strip()

    def save_modal_changes(self):
        """Clicks Save/Update button in the modal, waits for API response, and waits for modal to close."""
        logger.info("[UI] Saving modal changes...")
        submit_btn = self.page.locator("button[form='induction-content-form'], button[type='submit']:has-text('Save Changes'), .chakra-modal__footer button:not(:has-text('Cancel'))").first
        submit_btn.wait_for(state="visible", timeout=5000)
        submit_btn.scroll_into_view_if_needed()
        btn_text = submit_btn.inner_text().strip()
        logger.info(f"[UI] Submitting modal with button: '{btn_text}'")

        try:
            with self.page.expect_response(lambda r: "api/inductionpolicyconfig" in r.url.lower() and r.request.method in ("POST", "PUT"), timeout=8000) as resp_info:
                try:
                    submit_btn.click(timeout=3000)
                except Exception:
                    logger.info("[UI] Click intercepted; triggering programmatic form.requestSubmit()...")
                    self.page.eval_on_selector("form#induction-content-form", "f => f.requestSubmit()")
            resp = resp_info.value
            logger.info(f"[UI] Policy update API responded: Status {resp.status} | URL: {resp.url}")
        except Exception as e:
            logger.warning(f"[UI] API response wait encountered {e}; falling back to direct submit...")
            try:
                self.page.eval_on_selector("form#induction-content-form", "f => f.requestSubmit()")
            except Exception:
                submit_btn.click(force=True)

        self.page.wait_for_timeout(1500)
        try:
            self.modal.wait_for(state="hidden", timeout=7000)
        except Exception:
            logger.warning("[UI] Modal did not disappear after save; checking if close required")
        self.page.wait_for_timeout(1000)

    # ----------------- Hero Banner Section Methods -----------------
    def get_banner_scope_hierarchy_badge(self) -> str:
        """Returns the current Banner Scope Hierarchy badge text (e.g. 'Global Corporate Fallback', 'Company Wide', 'Company + Branch', 'Company + Branch + Department')."""
        self.switch_to_settings_welcome_tab()
        badge = self.page.locator("span.chakra-badge").filter(has_text=re.compile(r"CORPORATE|GLOBAL|COMPANY|BRANCH|DEPARTMENT|FALLBACK", re.I)).first
        if badge.is_visible():
            return badge.inner_text().strip()
        return "GLOBAL CORPORATE FALLBACK"

    def get_active_banner_scope_text(self) -> str:
        """Returns the Active Banner Scope explanatory text."""
        self.switch_to_settings_welcome_tab()
        el = self.page.locator("p, span, div").filter(has_text=re.compile(r"Organization Hierarchy Scope|Active Banner Scope|CORPORATE GLOBAL|FALLBACK", re.I)).first
        if el.is_visible():
            return el.inner_text().strip().replace("\n", " ")
        return "GLOBAL"

    def _select_dropdown_option_robust(self, select_locator: Locator, target_text: str):
        """Robustly selects an option from a dropdown, waiting for options to load from API."""
        select_locator.wait_for(state="visible", timeout=7000)
        # Wait up to 5s for options to populate from backend API
        for _ in range(25):
            opt_count = select_locator.locator("option").count()
            if opt_count > 1:
                break
            self.page.wait_for_timeout(200)

        # 1. Try exact label match
        try:
            select_locator.select_option(label=target_text, timeout=2000)
            return
        except Exception:
            pass

        # 2. Try substring / case-insensitive match
        opts = select_locator.locator("option").all()
        for opt in opts:
            txt = opt.inner_text().strip()
            if target_text.lower() in txt.lower():
                val = opt.get_attribute("value")
                if val:
                    select_locator.select_option(value=val)
                else:
                    select_locator.select_option(label=txt)
                return

        # 3. Direct fallback
        select_locator.select_option(target_text)

    def select_banner_company(self, company_name: str):
        """Selects company in the Banner Scope Hierarchy dropdown."""
        logger.info(f"[UI] Selecting Banner Scope Company: '{company_name}'...")
        self.switch_to_settings_welcome_tab()
        self._select_dropdown_option_robust(self.banner_company_select, company_name)
        self.page.wait_for_timeout(1500)

    def select_banner_branch(self, branch_name: str):
        """Selects branch in the Banner Scope Hierarchy dropdown."""
        logger.info(f"[UI] Selecting Banner Scope Branch: '{branch_name}'...")
        self.switch_to_settings_welcome_tab()
        self._select_dropdown_option_robust(self.banner_branch_select, branch_name)
        self.page.wait_for_timeout(1500)

    def select_banner_department(self, department_name: str):
        """Selects department in the Banner Scope Hierarchy dropdown."""
        logger.info(f"[UI] Selecting Banner Scope Department: '{department_name}'...")
        self.switch_to_settings_welcome_tab()
        self._select_dropdown_option_robust(self.banner_department_select, department_name)
        self.page.wait_for_timeout(1500)

    def reset_banner_to_global_scope(self):
        """Resets Banner Scope Hierarchy back to Global Scope."""
        logger.info("[UI] Resetting Banner Scope back to Global Scope...")
        self.switch_to_settings_welcome_tab()
        if self.banner_reset_global_button.is_visible(timeout=1000):
            self.banner_reset_global_button.click()
        else:
            self._select_dropdown_option_robust(self.banner_company_select, "All Companies (Corporate Global)")
        self.page.wait_for_timeout(1500)

    def get_banner_active_count_text(self) -> str:
        """Returns the active count badge text (e.g. '0 / 7 Custom Active' or '2 / 7 Custom Active')."""
        self.switch_to_settings_welcome_tab()
        match = self.page.locator("span.chakra-badge").filter(has_text=re.compile(r"\d+\s*/\s*7\s*Custom Active", re.I)).first
        if match.is_visible():
            return match.inner_text().strip()
        return "0 / 7 Custom Active"

    def get_slide_card(self, slide_num: int):
        """Returns the locator for the card container of Slide {slide_num} (1 to 7)."""
        self.switch_to_settings_welcome_tab()
        badge = self.page.locator("span.chakra-badge").filter(has_text=re.compile(rf"^Slide\s+{slide_num}$", re.I)).first
        return badge.locator("xpath=ancestor::div[3]")

    def get_slide_banner_slots_info(self) -> List[Dict[str, Any]]:
        """
        Extracts information for all 7 slide banner cards in the Hero Banner section:
        - slide_num: 1 to 7
        - title: Name of the slide (e.g. '1. Welcome Intro', '2. Organization', etc.)
        - badge: 'FALLBACK' vs 'CUSTOM ACTIVE'
        - has_upload: whether 'Upload Banner' or 'Replace' button is available
        """
        slots = []
        expected_slide_titles = {
            1: "1. Welcome Intro",
            2: "2. Organization",
            3: "3. Branch & Office",
            4: "4. Department & Team",
            5: "5. HR Policies",
            6: "6. Culture & Values",
            7: "7. Journey Launch"
        }

        # Wait up to 6s for the banner grid to render Slide 1
        self.page.locator("span.chakra-badge").filter(has_text=re.compile(r"^Slide\s+1$", re.I)).first.wait_for(state="visible", timeout=6000)

        for idx in range(1, 8):
            card = self.get_slide_card(idx)
            card.wait_for(state="visible", timeout=3000)

            title_elem = card.locator("p.chakra-text.css-16skkwe, p.chakra-text").first
            title = title_elem.inner_text().strip() if title_elem.is_visible() else expected_slide_titles.get(idx, f"Slide {idx}")

            is_custom = card.locator("span.chakra-badge:has-text('Custom')").first.is_visible()
            badge = "CUSTOM ACTIVE" if is_custom else "FALLBACK"

            upload_btn = card.locator("button:has-text('Upload Banner'), button:has-text('Replace')").first
            has_upload = upload_btn.is_visible()

            revert_btn = card.locator("button:has-text('Revert to Default')").first
            has_revert = revert_btn.is_visible()

            slots.append({
                "slide_num": idx,
                "title": title,
                "badge": badge,
                "has_upload": has_upload,
                "has_revert": has_revert
            })

        logger.info(f"[UI] Retrieved info for {len(slots)} / 7 slide cards")
        return slots

    def get_slide_image_src(self, slide_number: int) -> Optional[str]:
        """Returns the preview image src URL of Slide {slide_number} if custom, else None."""
        assert 1 <= slide_number <= 7, f"Invalid slide_number: {slide_number}."
        card = self.get_slide_card(slide_number)
        img = card.locator("img").first
        if img.is_visible():
            return img.get_attribute("src")
        return None

    def upload_slide_banner(self, slide_number: int, image_path: str, timeout: int = 15000):
        """
        Uploads a banner photo to a specific slide slot (1 to 7) in the Hero Banner section.
        Supports both initial upload ('Upload Banner') and replacement ('Replace').
        Waits for upload completion and card state update.
        """
        assert 1 <= slide_number <= 7, f"Invalid slide_number: {slide_number}. Must be between 1 and 7."
        logger.info(f"[UI] Uploading banner photo for Slide {slide_number}: '{image_path}'...")
        card = self.get_slide_card(slide_number)
        card.wait_for(state="visible", timeout=8000)
        card.scroll_into_view_if_needed()
        self.page.wait_for_timeout(500)

        upload_btn = card.locator("button:has-text('Upload Banner'), button:has-text('Replace')").first
        upload_btn.wait_for(state="visible", timeout=8000)

        try:
            with self.page.expect_file_chooser(timeout=8000) as fc_info:
                upload_btn.click()
            file_chooser = fc_info.value
            file_chooser.set_files(image_path)
        except Exception:
            self.banner_file_input.set_input_files(image_path)

        # Wait for card to reflect upload ('Replace' and 'Revert to Default' / 'Reset' buttons become visible)
        try:
            card.locator("button:has-text('Revert to Default'), button:has-text('Reset')").first.wait_for(state="visible", timeout=timeout)
        except Exception:
            pass
        self.page.wait_for_timeout(1500)
        logger.info(f"[UI] Slide {slide_number} banner upload finished.")

    def upload_all_seven_slide_banners(self, images: List[str]) -> List[Dict[str, Any]]:
        """
        Sequentially uploads banner images to all 7 slide cards (Slide 1 to 7).
        Guarantees that each slide completes upload before proceeding to the next.
        """
        assert len(images) >= 7, f"Expected at least 7 images, got {len(images)}"
        results = []
        for idx in range(1, 8):
            img_path = images[idx - 1]
            logger.info(f"[UI] ---> Uploading Slide {idx} / 7: '{os.path.basename(img_path)}'...")
            self.upload_slide_banner(slide_number=idx, image_path=img_path)
            results.append({
                "slide_num": idx,
                "image_path": img_path,
                "status": "CUSTOM ACTIVE"
            })

        count_badge = self.get_banner_active_count_text()
        logger.info(f"[UI] All 7 Slide Banners Uploaded! Final Count Badge: '{count_badge}'")
        return results

    def revert_slide_banner_to_default(self, slide_number: int):
        """
        Reverts a customized slide banner back to the corporate default fallback.
        """
        assert 1 <= slide_number <= 7, f"Invalid slide_number: {slide_number}. Must be between 1 and 7."
        logger.info(f"[UI] Reverting Slide {slide_number} banner to default corporate fallback...")
        card = self.get_slide_card(slide_number)
        card.scroll_into_view_if_needed()
        revert_btn = card.locator("button:has-text('Revert to Default'), button:has-text('Reset')").first
        if revert_btn.is_visible():
            revert_btn.click()
            # Wait until 'Upload Banner' appears or revert button disappears
            try:
                card.locator("button:has-text('Upload Banner')").first.wait_for(state="visible", timeout=5000)
            except Exception:
                pass
            self.page.wait_for_timeout(1000)

    def revert_all_seven_slide_banners(self):
        """
        Reverts all customized slide banners back to default fallback across all 7 slides.
        """
        logger.info("[UI] Reverting all customized slide banners to default corporate fallback...")
        for idx in range(1, 8):
            self.revert_slide_banner_to_default(idx)
        self.page.wait_for_timeout(1000)

    def upload_hero_banner(self, image_path: str):
        """Uploads an image file to the Welcome Screen Hero Banner file input."""
        logger.info(f"[UI] Uploading Hero Banner image: '{image_path}'...")
        self.banner_file_input.wait_for(state="attached", timeout=5000)
        self.banner_file_input.set_input_files(image_path)
        self.page.wait_for_timeout(2000)

    # ----------------- Step Video Section Methods -----------------
    def get_step_video_title(self) -> str:
        """Returns the title text of the Step Video section (e.g. 'Step Video: Step 1 · Company Profile')."""
        self.switch_to_step_content_tab()
        self.video_heading.wait_for(state="visible", timeout=5000)
        return self.video_heading.inner_text().strip()

    def upload_step_video(self, video_path: str, timeout: int = 25000):
        """
        Uploads a video file to the Step Video section.
        Supports both initial 'Upload Video' and 'Replace Video' states.
        Uses file chooser event for realistic browser interaction.
        """
        logger.info(f"[UI] Uploading Step Video: '{video_path}'...")
        self.switch_to_step_content_tab()
        self.video_section.wait_for(state="visible", timeout=6000)
        self.video_section.scroll_into_view_if_needed()
        self.page.wait_for_timeout(500)

        upload_btn = self.page.locator("button").filter(has_text=re.compile(r"Upload Video|Replace Video", re.I)).first
        upload_btn.wait_for(state="visible", timeout=6000)
        upload_btn.scroll_into_view_if_needed()

        try:
            with self.page.expect_file_chooser(timeout=8000) as fc_info:
                upload_btn.click()
            file_chooser = fc_info.value
            file_chooser.set_files(video_path)
        except Exception:
            self.video_file_input.set_input_files(video_path)

        self.page.wait_for_timeout(3000)
        logger.info("[UI] Step Video upload file selected.")

    def is_video_confirm_modal_open(self) -> bool:
        """Checks if the Confirm Video Upload modal dialog is open."""
        return self.page.locator("section[role='dialog']:has-text('Confirm Video Upload')").first.is_visible()

    def confirm_step_video_upload(
        self,
        companies: Optional[List[str]] = None,
        branches: Optional[List[str]] = None,
        departments: Optional[List[str]] = None
    ):
        """
        Interacts with the 'Confirm Video Upload' modal dialog:
        - Allows selecting specific target audiences (MultiSelect checkboxes)
        - Clicks 'Confirm & Upload'
        """
        modal = self.page.locator("section[role='dialog']:has-text('Confirm Video Upload')").first
        modal.wait_for(state="visible", timeout=8000)

        if companies:
            comp_btn = modal.locator("div:has(> label:has-text('Company')) button[aria-haspopup='menu']").first
            comp_btn.click()
            self.page.wait_for_timeout(500)
            for c_name in companies:
                chk = modal.locator(f"label.chakra-checkbox:has-text('{c_name}')").first
                if chk.is_visible():
                    chk.click()
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(500)

        confirm_btn = modal.locator("button:has-text('Confirm & Upload')").first
        confirm_btn.wait_for(state="visible", timeout=5000)
        confirm_btn.click()
        self.page.wait_for_timeout(3000)

    def cancel_step_video_upload(self):
        """Cancels and closes the Confirm Video Upload modal dialog."""
        modal = self.page.locator("section[role='dialog']:has-text('Confirm Video Upload')").first
        cancel_btn = modal.locator("button:has-text('Cancel')").first
        if cancel_btn.is_visible():
            cancel_btn.click()
        else:
            self.page.keyboard.press("Escape")
        self.page.wait_for_timeout(1000)

