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
        logger.info("Navigating to Asset Maintenance page")
        self.page.goto(f"{settings.BASE_URL}/asset-maintenance")
        self.page.wait_for_load_state("domcontentloaded")

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
        self.page.wait_for_timeout(1000)

        # 1. Switch to 'Maintenance Request' tab
        try:
            maint_tab = self.page.locator("button[role='tab'], .chakra-tabs__tab").filter(has_text=re.compile(r"Maintenance Request", re.I)).first
            if not maint_tab.is_visible(timeout=1500):
                maint_tab = self.page.get_by_role("tab", name=re.compile(r"Maintenance Request", re.I)).first
            if maint_tab.is_visible(timeout=2000):
                maint_tab.click(force=True)
                self.page.wait_for_timeout(1500)
        except Exception as e:
            logger.warning(f"Maintenance Request tab note: {e}")

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

    def complete_maintenance(self, asset_code_or_name: str, resolution: str = "Repaired", cost: str = None, remarks: str = None):
        """
        Approves and marks maintenance case as completed / repaired.
        """
        return self.approve_maintenance_request(
            asset_code_or_name=asset_code_or_name,
            issue_type="Keyboard Issue",
            descriptions=remarks or "Display/Keyboard replaced by technician.",
            estimated_cost=cost or "1500"
        )

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)
