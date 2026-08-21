import re
import random
import logging
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)

class AssetAssignmentPage(BasePage):
    ASSIGN_ASSET_BTN = "role=button[name='Assign Asset']"
    SUBMIT_ASSIGNMENT_BTN = "role=button[name='Assign Asset']" # Form submit button
    CANCEL_BTN = "role=button[name='Cancel']"
    TOAST = "#chakra-toast-manager-top-right"

    def navigate_to_asset_assignment(self):
        logger.info("Navigating to Asset Assignment page")
        self.page.goto(f"{settings.BASE_URL}/asset-assignment")
        self.page.wait_for_load_state("domcontentloaded")

    def click_assign_asset(self):
        self.page.locator(self.ASSIGN_ASSET_BTN).first.wait_for(state="visible", timeout=10000)
        self.page.locator(self.ASSIGN_ASSET_BTN).first.click()
        self.page.locator("[role='dialog'][aria-modal='true']").wait_for(state="visible", timeout=10000)

    def validate_available_assets_dropdown(self) -> dict:
        """
        Validates whether the Available Asset dropdown populates items for assignment.
        Returns a dict: {"populated": bool, "count": int, "items": list[str]}
        """
        logger.info("Validating Available Asset dropdown population...")
        trigger_btn = self.page.get_by_role("button", name=re.compile(r"Select asset", re.I)).first
        if not trigger_btn.is_visible(timeout=1000):
            trigger_btn = self.page.locator("button").filter(has_text=re.compile(r"Select asset|Select|Assets", re.I)).first

        if not trigger_btn.is_visible(timeout=2000):
            logger.warning("Available Asset dropdown trigger button is not visible.")
            return {"populated": False, "count": 0, "items": []}

        try:
            trigger_btn.click()
            self.page.wait_for_timeout(600)
            items_loc = self.page.locator("[role='menuitem'], [role='menuitemcheckbox'], .chakra-menu__menuitem").all()
            items = [item.inner_text().strip() for item in items_loc if item.inner_text().strip()]
            
            # Press Escape to close popover
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(300)
            
            populated = len(items) > 0
            logger.info(f"Available Asset Dropdown Populated={populated}, Count={len(items)}, Items={items}")
            return {"populated": populated, "count": len(items), "items": items}
        except Exception as ex:
            logger.warning(f"Error checking available asset dropdown: {ex}")
            return {"populated": False, "count": 0, "items": []}

    def fill_assignment_details(self, employee_name: str, category: str, sub_category: str, asset_name_or_code: str = None, expected_return_date: str = None, remarks: str = None) -> dict:
        logger.info(f"Filling assignment details: Employee={employee_name}, Category={category}, SubCategory={sub_category}")
        
        # Employee Search input
        emp_search = self.page.get_by_placeholder("Search employee name…")
        if not emp_search.is_visible(timeout=1000):
            emp_search = self.page.locator("input[placeholder*='Search employee']").first
        emp_search.fill(employee_name)
        self.page.wait_for_timeout(1000)
        
        # Select first matching result from suggestion popover/portal
        try:
            opt = self.page.locator(".chakra-portal, [role='listbox'], [role='option'], .chakra-menu__menu-list").get_by_text(employee_name, exact=False).first
            if not opt.is_visible(timeout=2500):
                opt = self.page.locator(".chakra-portal div, [role='option'], p, li").filter(has_text=re.compile(employee_name.split()[0], re.I)).first
            opt.click(force=True)
        except Exception as ex:
            logger.warning(f"Note selecting employee '{employee_name}': {ex}")
            self.page.keyboard.press("ArrowDown")
            self.page.keyboard.press("Enter")
        
        # Category dropdown
        if category:
            cat_select = self.page.get_by_label("Category*", exact=True)
            if not cat_select.is_visible(timeout=1000):
                cat_select = self.page.locator("select").first
            try:
                cat_select.select_option(label=category)
            except Exception:
                options = cat_select.locator("option").all_inner_texts()
                for idx, opt in enumerate(options):
                    if category.lower() in opt.lower():
                        cat_select.select_option(index=idx)
                        break
            self.page.wait_for_timeout(500)
        
        # Sub Category dropdown
        sub_select = self.page.get_by_label("Sub Category*", exact=True)
        if not sub_select.is_visible(timeout=1000):
            sub_select = self.page.locator("select").nth(1)

        sub_options = [o.strip() for o in sub_select.locator("option").all_inner_texts() if o.strip() and not o.startswith("Select")]
        target_sub = sub_category if sub_category and sub_category in sub_options else (sub_options[0] if sub_options else None)

        def _try_select_asset(sub_name):
            try:
                sub_select.select_option(label=sub_name)
            except Exception:
                for idx, opt in enumerate(sub_select.locator("option").all_inner_texts()):
                    if sub_name.lower() in opt.lower():
                        sub_select.select_option(index=idx)
                        break
            self.page.wait_for_timeout(1500)

            trigger = self.page.get_by_role("button", name=re.compile(r"(Select asset|Select|Available)", re.I)).first
            if not trigger.is_visible(timeout=1000):
                trigger = self.page.locator(".chakra-menu__menubutton, [id*='menu-button']").first

            if trigger.is_visible(timeout=2000):
                trigger.click()
                self.page.wait_for_timeout(800)
                menu = self.page.locator(".chakra-portal div[role='menu'], div.chakra-menu__menu-list").first
                if menu.is_visible(timeout=2000):
                    items = menu.locator("[role='menuitem'], button").all()
                else:
                    items = self.page.locator("[role='menuitem'], .chakra-menu__menuitem").all()

                valid_items = [itm for itm in items if "not uploaded" not in itm.inner_text().lower() and len(itm.inner_text().strip()) > 0]
                if valid_items:
                    target_itm = valid_items[0]
                    text = target_itm.inner_text().strip()
                    m = re.search(r"ASSET-[A-Z0-9-]+", text)
                    code = m.group(0) if m else text
                    target_itm.click(force=True)
                    logger.info(f"[DROPDOWN ASSET SELECTED SUCCESS] SubCategory: '{sub_name}', Item: '{text}' -> Code: '{code}'")
                    return code
                else:
                    self.page.keyboard.press("Escape")
            return None

        selected_code = _try_select_asset(target_sub) if target_sub else None

        # Fallback to other available subcategories if first one had 0 stock
        if not selected_code and sub_options:
            for alt_sub in sub_options:
                if alt_sub != target_sub:
                    logger.info(f"[STOCK LOOKUP] Checking available assets under SubCategory: '{alt_sub}'...")
                    selected_code = _try_select_asset(alt_sub)
                    if selected_code:
                        break

        # STRICT USER RULE: If no asset was selected, mark test failed immediately!
        assert selected_code, f"[ASSIGNMENT FAILED] Could not select an available asset from dropdown for '{employee_name}'! Ensure available stock exists."

        # Expected Return Date
        if expected_return_date:
            date_input = self.page.locator("[role='dialog'] input[type='date'], input[type='date']").first
            if not date_input.is_visible(timeout=1000):
                date_input = self.page.locator("input[placeholder*='date' i], input[name*='date' i]").first
            if date_input.is_visible(timeout=2000):
                date_input.fill(expected_return_date)
                logger.info(f"Filled Expected Return Date: '{expected_return_date}'")

        # Remarks
        if remarks:
            rem_input = self.page.locator("[role='dialog'] textarea, textarea, input[placeholder*='Assigned' i]").first
            if rem_input.is_visible(timeout=1000):
                rem_input.fill(remarks)
                logger.info(f"Filled Remarks: '{remarks}'")

        return selected_code or asset_name_or_code or "ASSET"

    def click_submit_assignment(self):
        dialog = self.page.locator("[role='dialog'], .chakra-modal__content, .chakra-drawer__content").first
        btn = dialog.get_by_role("button", name=re.compile(r"Assign Asset|Assign|Submit|Save", re.I)).first
        if not btn.is_visible(timeout=1000):
            btn = self.page.locator("button:has-text('Assign Asset'), button:has-text('Assign'), button:has-text('Submit')").first
        btn.click(force=True)

    def click_cancel(self):
        self.page.locator(self.CANCEL_BTN).click()

    def assign_requested_asset(self, employee_name: str, asset_code: str = None, assignment_type: str = "Temporary", expected_return_date: str = "2026-12-31", remarks: str = "Asset issued against request") -> dict:
        """
        Fulfills a requested asset assignment:
        1. Clicks 'Requested Assignment' tab.
        2. Searches employee/asset in table search.
        3. Clicks 'Fulfil →' button on the row.
        4. In 'Assign Requested Asset' form, clicks 'Select assets to assign'.
        5. Validates whether available asset dropdown populates records or shows 'No results found'.
        6. Selects an asset.
        7. Selects Assignment Type ('Permanent' vs 'Temporary').
        8. If Temporary, fills Expected Return Date & Remarks.
        9. Clicks 'Assign Asset' button to submit.
        """
        import re
        logger.info(f"Fulfilling requested asset for employee: {employee_name}")
        
        # 1. Click Requested Assignment tab
        req_tab = self.page.get_by_role("tab", name=re.compile(r"Requested Assignment", re.I)).first
        if not req_tab.is_visible(timeout=1000):
            req_tab = self.page.locator("button[role='tab']").filter(has_text=re.compile(r"Requested Assignment", re.I)).first
        req_tab.click()
        self.page.wait_for_timeout(1000)

        # Wait for table rows to attach/render
        try:
            self.page.locator("table tbody tr").first.wait_for(state="visible", timeout=10000)
        except Exception:
            pass

        # 2. Search employee/asset in search box if visible
        search_in = self.page.locator("input[placeholder*='Search assets, employees']").first
        if not search_in.is_visible(timeout=1000):
            search_in = self.page.locator("input[placeholder*='Search']").first
        if search_in.is_visible(timeout=1000):
            search_in.fill(employee_name)
            search_in.press("Enter")
            self.page.wait_for_timeout(800)

        # 3. Locate row and click 'Fulfil →' button
        first_name = employee_name.split()[0] if employee_name else "Sanidhy"
        row = self.page.locator("table tbody tr").filter(has_text=re.compile(first_name, re.I)).first
        if not row.is_visible(timeout=2000):
            row = self.page.locator("table tbody tr").filter(has=self.page.locator("button", has_text=re.compile(r"Fulfil", re.I))).first
        if not row.is_visible(timeout=2000):
            row = self.page.locator("table tbody tr").first

        fulfil_btn = row.locator("button").filter(has_text=re.compile(r"Fulfil", re.I)).first
        if not fulfil_btn.is_visible(timeout=2000):
            fulfil_btn = self.page.locator("button").filter(has_text=re.compile(r"Fulfil", re.I)).first

        if not fulfil_btn.is_visible(timeout=2000):
            logger.warning(f"No 'Fulfil' button found on row for '{employee_name}'.")
            return {"success": False, "reason": "Fulfil button not visible", "dropdown_info": {"populated": False, "count": 0, "items": []}}

        fulfil_btn.click()
        self.page.wait_for_timeout(1000)

        # 4. Form 'Assign Requested Asset' appears. Click 'Select assets to assign'
        form = self.page.locator("[role='dialog'], .chakra-drawer__content, .chakra-modal__content").first
        if not form.is_visible(timeout=1000):
            form = self.page

        dropdown_info = {"populated": False, "count": 0, "items": []}
        asset_select_btn = form.locator("button").filter(has_text=re.compile(r"Select assets to assign|Select asset", re.I)).first
        if asset_select_btn.is_visible(timeout=3000):
            asset_select_btn.click()
            self.page.wait_for_timeout(600)

            # Validate popover contents
            popover = self.page.locator("[role='menu'], .chakra-menu__menu-list").first
            no_results = popover.locator("p").filter(has_text=re.compile(r"No results found", re.I)).first
            
            items_loc = popover.locator("[role='menuitem'], [role='menuitemcheckbox'], .chakra-menu__menuitem").all()
            items = [it.inner_text().strip() for it in items_loc if it.inner_text().strip()]

            if items:
                dropdown_info = {"populated": True, "count": len(items), "items": items}
                logger.info(f"Available Assets Dropdown POPULATED with {len(items)} items: {items}")
                # Select specified asset or first available item
                selected_item = False
                if asset_code:
                    for it in items_loc:
                        if asset_code.lower() in it.inner_text().lower():
                            it.click(force=True)
                            selected_item = True
                            break
                if not selected_item:
                    items_loc[0].click(force=True)
            elif no_results.is_visible(timeout=1000):
                dropdown_info = {"populated": False, "count": 0, "items": ["No results found"]}
                logger.warning("Available Assets Dropdown shows: 'No results found'")
            
            # Press Escape to close popover if still open
            try:
                self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(300)
            except Exception:
                pass

        # 5. Select Assignment Type ('Permanent' or 'Temporary')
        type_select = form.locator("//div[./label[contains(text(), 'Assignment Type')]]//select").first
        if not type_select.is_visible(timeout=1000):
            type_select = form.locator("select").first
        if type_select.is_visible(timeout=1000):
            try:
                type_select.select_option(label=assignment_type)
            except Exception:
                type_select.select_option(value=assignment_type)
            logger.info(f"Selected Assignment Type: '{assignment_type}'")

        # 6. If Temporary, fill Expected Return Date & Remarks
        if assignment_type.lower() == "temporary":
            if expected_return_date:
                date_in = form.locator("//div[./label[contains(text(), 'Expected Return Date')]]//input").first
                if not date_in.is_visible(timeout=500):
                    date_in = form.locator("input[type='date']").first
                if date_in.is_visible(timeout=1000):
                    date_in.fill(expected_return_date)

            if remarks:
                rem_in = form.locator("//div[./label[contains(text(), 'Remarks')]]//textarea").first
                if not rem_in.is_visible(timeout=500):
                    rem_in = form.locator("textarea").first
                if rem_in.is_visible(timeout=1000):
                    rem_in.fill(remarks)

        # 7. Submit Assignment
        submit_btn = form.locator("button").filter(has_text=re.compile(r"^Assign Asset$", re.I)).first
        if not submit_btn.is_visible(timeout=1000):
            submit_btn = form.locator("button").filter(has_text=re.compile(r"Assign Asset|Assign|Submit", re.I)).first
        submit_btn.click(force=True)
        self.page.wait_for_timeout(500)

        return {
            "success": True,
            "dropdown_info": dropdown_info,
            "assignment_type": assignment_type
        }

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)
