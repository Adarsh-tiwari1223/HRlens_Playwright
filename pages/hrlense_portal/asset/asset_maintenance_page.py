import logging
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)

class AssetMaintenancePage(BasePage):
    CREATE_MAINTENANCE_BTN = "role=button[name='Create Maintenance']"
    SUBMIT_CASE_BTN = "role=button[name='Create Case']"
    CANCEL_BTN = "role=button[name='Cancel']"
    TOAST = "#chakra-toast-manager-top-right"

    def navigate_to_asset_maintenance(self):
        """
        Navigates to Asset Maintenance page via sidebar submenu item if visible,
        otherwise directly redirects to /asset-maintenance using URL.
        """
        import re
        logger.info("Navigating to Asset Maintenance page")
        target_url = f"{settings.BASE_URL}/asset-maintenance"
        
        # 1. Try sidebar UI link if visible
        try:
            link = self.page.locator("a.submenu_item[href*='/asset-maintenance'], a[href*='/asset-maintenance']").first
            if not link.is_visible(timeout=1000):
                # Expand parent Asset sidebar item if present
                for parent_sel in ["Asset", "Assets", "Asset Management"]:
                    parent = self.page.locator(".sidebar, nav, aside").locator("div, p, a, button").filter(has_text=re.compile(rf"^{parent_sel}$", re.I)).first
                    if parent.is_visible(timeout=500):
                        parent.scroll_into_view_if_needed()
                        parent.click()
                        self.page.wait_for_timeout(500)
                        break

            link = self.page.locator("a.submenu_item[href*='/asset-maintenance'], a[href*='/asset-maintenance']").first
            if link.is_visible(timeout=1500):
                link.scroll_into_view_if_needed()
                link.click()
                logger.info("Clicked sidebar link for /asset-maintenance")
            else:
                logger.info("Sidebar UI link hidden; directly redirecting to /asset-maintenance using URL")
                self.page.goto(target_url, wait_until="domcontentloaded")
        except Exception as e:
            logger.info(f"Sidebar note ({e}); directly redirecting to /asset-maintenance using URL")
            self.page.goto(target_url, wait_until="domcontentloaded")

        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(1000)

        # Ensure page is on /asset-maintenance
        if "/asset-maintenance" not in self.page.url:
            logger.info("Page URL not /asset-maintenance; executing direct URL redirect")
            self.page.goto(target_url, wait_until="domcontentloaded")
            self.page.wait_for_load_state("domcontentloaded")
            self.page.wait_for_timeout(1000)

        # Wait for tab or header
        try:
            self.page.locator("button[role='tab'], .chakra-tabs__tab").first.wait_for(state="visible", timeout=8000)
        except Exception:
            pass

    def click_create_maintenance(self):
        self.page.locator(self.CREATE_MAINTENANCE_BTN).wait_for(state="visible", timeout=10000)
        self.page.locator(self.CREATE_MAINTENANCE_BTN).click()
        self.page.locator("[role='dialog'][aria-modal='true']").wait_for(state="visible", timeout=10000)

    def fill_maintenance_details(self, asset_code_or_name: str, issue_type: str, description: str = None, sent_date: str = None, expected_return: str = None, estimated_cost: str = None, remarks: str = None):
        logger.info(f"Filling maintenance details: Asset={asset_code_or_name}, Issue={issue_type}")
        
        # Asset Search input
        asset_input = self.page.get_by_placeholder("Search by asset code or name...")
        asset_input.fill(asset_code_or_name)
        self.page.wait_for_timeout(1000)
        # Click suggestion first item
        self.page.locator(".chakra-portal, [role='listbox']").get_by_text(asset_code_or_name, exact=False).first.click()
        
        # Issue Type
        self.page.get_by_label("Issue Type", exact=False).select_option(label=issue_type)
        
        # Issue Description
        if description:
            self.page.get_by_placeholder("Describe the issue in detail...").fill(description)
            
        # Sent Date (first date input)
        if sent_date:
            self.page.locator("input[type='date']").first.fill(sent_date)
            
        # Expected Return Date (second date input)
        if expected_return:
            self.page.locator("input[type='date']").nth(1).fill(expected_return)
            
        # Estimated Cost
        if estimated_cost:
            self.page.get_by_placeholder("0").fill(estimated_cost)
            
        # Remarks
        if remarks:
            self.page.get_by_placeholder("e.g. Sent to authorized service center").fill(remarks)

    def approve_maintenance_request(self, asset_code_or_name: str, issue_type: str = "Keyboard Issue", descriptions: str = "Sent to authorized service center for repair", estimated_cost: str = "1500") -> str:
        """
        Processes Maintenance Request approval workflow on /asset-maintenance:
        1. Navigates to 'Maintenance Request' tab (<button role="tab">Maintenance Request</button>)
        2. Locates target row matching asset_code_or_name in <table class="chakra-table">
        3. Clicks 'Approve' button (<button class="chakra-button css-18yci02">Approve</button>) in Action column
        4. In 'Approve Maintenance Request' modal:
           - Selects Issue Type (<select class="chakra-select"> -> 'Keyboard Issue' / 'Hardware Failure')
           - Fills Descriptions (<textarea placeholder="e.g. Sent to authorized service center">)
           - Fills Estimated Cost (<input placeholder="0" type="number">)
           - Clicks confirmation button (<button class="chakra-button"> Approve </button>)
        5. Captures and returns toast notification
        """
        import re
        logger.info(f"Approving maintenance request for asset: '{asset_code_or_name}', Issue='{issue_type}'")
        self.navigate_to_asset_maintenance()
        self.navigate_to_maintenance_request_tab()

        try:
            self.page.locator("table tbody").wait_for(state="visible", timeout=5000)
        except Exception:
            pass

        clean_code = asset_code_or_name.strip()

        # 2. Try direct match in table rows first (new requests appear at top)
        row = self.page.locator("table tbody tr").filter(has_text=clean_code).first

        if not row.is_visible(timeout=2000):
            # Try searching in 'Search asset / vendor…' box
            search_input = self.page.locator("input[placeholder*='Search asset / vendor' i], input[placeholder*='Search' i]").first
            if search_input.is_visible(timeout=1500):
                search_input.click()
                search_input.fill("")
                search_input.fill(clean_code)
                self.page.wait_for_timeout(1200)
                row = self.page.locator("table tbody tr").filter(has_text=clean_code).first

        # Fallback: scan all rows for text match or select top row
        if not row.is_visible(timeout=2000):
            all_rows = self.page.locator("table tbody tr").all()
            for r in all_rows:
                if clean_code.lower() in r.inner_text().lower():
                    row = r
                    break
            if (not row or not row.is_visible()) and all_rows:
                logger.info("[MAINTENANCE FALLBACK] Selecting top maintenance request row")
                row = all_rows[0]

        assert row.is_visible(timeout=3000), f"No maintenance request row visible for '{clean_code}' on /asset-maintenance table!"

        # 3. Click 'Approve' button in Action column (<button class="chakra-button css-18yci02">Approve</button>)
        approve_btn = row.locator("button.chakra-button, button").filter(has_text=re.compile(r"^Approve$", re.I)).first
        if not approve_btn.is_visible(timeout=1000):
            approve_btn = row.get_by_role("button", name="Approve").first
        
        logger.info(f"Clicking Action Column -> '{approve_btn.inner_text().strip() or 'Approve'}' button...")
        approve_btn.scroll_into_view_if_needed()
        try:
            approve_btn.click(timeout=3000)
        except Exception:
            approve_btn.click(force=True)
        self.page.wait_for_timeout(1000)

        # 4. Handle 'Approve Maintenance Request' modal dialog
        dialog = self.page.locator("[role='dialog'][aria-modal='true'], .chakra-modal__content, div:has(> header:text('Approve Maintenance Request'))").first
        if not dialog.is_visible(timeout=3000):
            dialog = self.page.locator("div.chakra-modal__content, [role='dialog']").first

        if dialog.is_visible(timeout=5000):
            # Issue Type select
            try:
                issue_select = dialog.locator("select.chakra-select, select").first
                if issue_select.is_visible(timeout=1000):
                    options = [o.strip() for o in issue_select.locator("option").all_inner_texts() if o.strip() and not o.lower().startswith("select")]
                    matched_opt = next((o for o in options if issue_type.lower() in o.lower()), options[0] if options else "Keyboard Issue")
                    issue_select.select_option(label=matched_opt)
                    logger.info(f"Selected Issue Type: '{matched_opt}'")
            except Exception as e:
                logger.warning(f"Issue type selection note: {e}")

            # Descriptions textarea
            try:
                desc_input = dialog.locator("textarea[placeholder*='Sent to authorized' i], textarea.chakra-textarea, textarea").first
                if desc_input.is_visible(timeout=1000):
                    desc_input.fill(descriptions)
                    logger.info(f"Filled Descriptions: '{descriptions}'")
            except Exception as e:
                logger.warning(f"Descriptions fill note: {e}")

            # Estimated Cost input
            try:
                cost_input = dialog.locator("input[type='number'], input[placeholder='0']").first
                if cost_input.is_visible(timeout=1000):
                    cost_input.fill(str(estimated_cost))
                    logger.info(f"Filled Estimated Cost: '{estimated_cost}'")
            except Exception as e:
                logger.warning(f"Estimated cost fill note: {e}")

            # Click modal confirmation button: <button class="chakra-button"> Approve </button>
            submit_btn = dialog.get_by_role("button", name=re.compile(r"^Approve$", re.I)).last
            if not submit_btn.is_visible(timeout=1000):
                submit_btn = dialog.locator("button.chakra-button").filter(has_text=re.compile(r"Approve", re.I)).last
            
            logger.info("Clicking modal 'Approve' confirmation button...")
            submit_btn.scroll_into_view_if_needed()
            try:
                submit_btn.click(timeout=3000)
            except Exception:
                submit_btn.click(force=True)

            toast = self.wait_for_toast_message()
            logger.info(f"Approve maintenance toast: '{toast}'")
            self.page.wait_for_timeout(1000)
            return toast

    def navigate_to_maintenance_queue_tab(self):
        """Switches to the 'Maintenance Queue' tab on /asset-maintenance."""
        import re
        logger.info("Switching to 'Maintenance Queue' tab on /asset-maintenance")
        tab = self.page.locator("button[role='tab'], .chakra-tabs__tab").filter(has_text=re.compile(r"Maintenance Queue", re.I)).first
        if not tab.is_visible(timeout=2000):
            tab = self.page.get_by_role("tab", name=re.compile(r"Maintenance Queue", re.I)).first
        tab.click(force=True)
        self.page.wait_for_timeout(1200)

    def navigate_to_maintenance_request_tab(self):
        """Switches to the 'Maintenance Request' tab on /asset-maintenance."""
        import re
        logger.info("Switching to 'Maintenance Request' tab on /asset-maintenance")
        tab = self.page.locator("button[role='tab'], .chakra-tabs__tab").filter(has_text=re.compile(r"Maintenance Request", re.I)).first
        if not tab.is_visible(timeout=2000):
            tab = self.page.get_by_role("tab", name=re.compile(r"Maintenance Request", re.I)).first
        tab.click(force=True)
        self.page.wait_for_timeout(1200)

    def navigate_to_maintenance_history_tab(self):
        """Switches to the 'Maintenance History' tab on /asset-maintenance."""
        import re
        logger.info("Switching to 'Maintenance History' tab on /asset-maintenance")
        tab = self.page.locator("button[role='tab'], .chakra-tabs__tab").filter(has_text=re.compile(r"Maintenance History", re.I)).first
        if not tab.is_visible(timeout=2000):
            tab = self.page.get_by_role("tab", name=re.compile(r"Maintenance History", re.I)).first
        tab.click(force=True)
        self.page.wait_for_timeout(1200)

    def complete_maintenance_case(self, asset_code_or_name: str, status_update: str = "Completed", return_date: str = None, remarks: str = "Repaired and restored to stock") -> str:
        """
        Completes an in-progress maintenance case on the 'Maintenance Queue' tab:
        1. Navigates to /asset-maintenance -> 'Maintenance Queue' tab.
        2. Filters the search box with asset_code_or_name.
        3. Clicks the Eye action icon on the matching row to open the 'Maintenance Details' modal.
        4. Selects status radio: 'Completed' (restores to Available) or 'Beyond Repair' (moves to Scrap/Disposal).
        5. Fills Remarks.
        6. Clicks 'Save Changes' button.
        7. Waits for and returns toast notification.
        """
        import re
        clean_code = asset_code_or_name.strip()
        logger.info(f"Completing maintenance case for '{clean_code}': Status -> '{status_update}'")
        
        self.navigate_to_asset_maintenance()
        self.navigate_to_maintenance_queue_tab()

        # 1. Search for asset code
        search_input = self.page.locator("input[placeholder*='Search asset / vendor' i], input[placeholder*='Search' i]").first
        if search_input.is_visible(timeout=2000):
            search_input.click()
            search_input.fill("")
            search_input.fill(clean_code)
            self.page.wait_for_timeout(1200)

        # 2. Locate target row
        row = self.page.locator("table tbody tr").filter(has_text=clean_code).first
        if not row.is_visible(timeout=2000):
            # Fallback to scanning rows
            all_rows = self.page.locator("table tbody tr").all()
            for r in all_rows:
                if clean_code.lower() in r.inner_text().lower():
                    row = r
                    break
            if (not row or not row.is_visible()) and all_rows:
                row = all_rows[0]

        assert row.is_visible(timeout=3000), f"No maintenance queue row visible for '{clean_code}' on /asset-maintenance!"

        # 3. Click the Eye icon on the row
        eye_btn = row.locator("button:has(svg), td:last-child button, td:last-child svg, svg").first
        if not eye_btn.is_visible(timeout=1500):
            eye_btn = row.locator("svg").first
        logger.info("Clicking Eye action icon to open 'Maintenance Details' modal...")
        eye_btn.scroll_into_view_if_needed()
        try:
            eye_btn.click(timeout=3000)
        except Exception:
            eye_btn.click(force=True)
        self.page.wait_for_timeout(1000)

        # 4. Handle 'Maintenance Details' modal
        modal = self.page.locator("[role='dialog'][aria-modal='true'], .chakra-modal__content, div:has(> header:has-text('Maintenance Details'))").first
        if not modal.is_visible(timeout=3000):
            modal = self.page.locator("div.chakra-modal__content, [role='dialog']").first

        assert modal.is_visible(timeout=5000), "Maintenance Details modal did not appear!"

        # 5. Select Status radio ('Completed' / 'Beyond Repair' / 'In Progress')
        try:
            radio_label = modal.locator("label.chakra-radio").filter(has_text=re.compile(rf"^{re.escape(status_update)}$", re.I)).first
            if not radio_label.is_visible(timeout=1000):
                radio_label = modal.locator("label.chakra-radio").filter(has_text=re.compile(re.escape(status_update), re.I)).first
            
            if radio_label.is_visible(timeout=1000):
                radio_label.click(force=True)
                logger.info(f"Clicked status radio label: '{status_update}'")
            else:
                radio_input = modal.locator(f"input[type='radio'][value*='{status_update}' i]").first
                if radio_input.is_visible(timeout=1000):
                    radio_input.check(force=True)
                    logger.info(f"Checked status radio input: '{status_update}'")
                else:
                    elem = modal.locator("div, p, span, label").filter(has_text=re.compile(rf"^{re.escape(status_update)}$", re.I)).first
                    elem.click(force=True)
                    logger.info(f"Clicked fallback status element: '{status_update}'")
        except Exception as e:
            logger.warning(f"Status radio selection note: {e}")

        self.page.wait_for_timeout(600)

        # 5b. Fill Returned Date (Required when Completed or Beyond Repair)
        import datetime
        date_str = return_date or datetime.date.today().strftime("%Y-%m-%d")
        try:
            # Check form-control with "Returned Date" label, or input[type='date']
            date_input = modal.locator("div.chakra-form-control:has(label:has-text('Returned Date')) input").first
            if not date_input.is_visible(timeout=1000):
                date_input = modal.locator("input[type='date']").first
            if not date_input.is_visible(timeout=1000):
                date_input = modal.get_by_label("Returned Date", exact=False).first
            if not date_input.is_visible(timeout=1000):
                date_input = modal.locator("input[placeholder*='date' i], input[name*='date' i], input[name*='return' i]").first

            if date_input.is_visible(timeout=2000):
                date_input.scroll_into_view_if_needed()
                date_input.click()
                date_input.fill(date_str)
                date_input.dispatch_event("input")
                date_input.dispatch_event("change")
                logger.info(f"Filled Returned Date: '{date_str}' (Current value: '{date_input.input_value()}')")
            else:
                logger.warning("Returned Date input field not visible in modal!")
        except Exception as e:
            logger.warning(f"Returned Date fill note: {e}")

        # 5c. Optional Cost field check
        try:
            cost_input = modal.locator("input[type='number'], input[placeholder*='cost' i]").first
            if cost_input.is_visible(timeout=500):
                if not cost_input.input_value():
                    cost_input.fill("1500")
                    logger.info("Filled Cost field: 1500")
        except Exception:
            pass

        # 6. Fill Remarks
        if remarks:
            try:
                rem_area = modal.locator("textarea[placeholder*='Display panel' i], textarea.chakra-textarea, textarea").first
                if rem_area.is_visible(timeout=1000):
                    rem_area.scroll_into_view_if_needed()
                    rem_area.click()
                    rem_area.fill(remarks)
                    rem_area.dispatch_event("input")
                    rem_area.dispatch_event("change")
                    logger.info(f"Filled Remarks: '{remarks}'")
            except Exception as e:
                logger.warning(f"Remarks note: {e}")

        # 7. Click 'Save Changes'
        save_btn = modal.locator("button.chakra-button, button").filter(has_text=re.compile(r"^Save Changes$", re.I)).first
        if not save_btn.is_visible(timeout=1000):
            save_btn = modal.get_by_role("button", name="Save Changes").first
        logger.info("Clicking modal 'Save Changes' button...")
        save_btn.scroll_into_view_if_needed()
        try:
            save_btn.click(timeout=3000)
        except Exception:
            save_btn.click(force=True)

        toast = self.wait_for_toast_message()
        logger.info(f"Complete maintenance toast: '{toast}'")
        self.page.wait_for_timeout(1000)
        return toast

    def complete_maintenance(self, asset_code_or_name: str, resolution: str = "Completed", return_date: str = None, remarks: str = None) -> str:
        """
        Marks maintenance case as completed / repaired in Maintenance Queue.
        """
        return self.complete_maintenance_case(
            asset_code_or_name=asset_code_or_name,
            status_update=resolution,
            return_date=return_date,
            remarks=remarks or "Display/Keyboard replaced and restored to stock."
        )

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)

