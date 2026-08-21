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

    def complete_maintenance(self, asset_code_or_name: str, resolution: str = "Repaired", cost: str = None, remarks: str = None):
        """
        Marks an in-progress maintenance case as complete (Repaired -> Available, or Unrepairable -> Damaged).
        """
        import re
        logger.info(f"Completing maintenance for asset: {asset_code_or_name}, Resolution: {resolution}")
        
        # Search asset in maintenance list
        search_input = self.page.locator("input[placeholder*='Search']").first
        if search_input.is_visible():
            search_input.fill(asset_code_or_name)
            self.page.wait_for_timeout(2000)
            
        row = self.page.locator("table tbody tr").filter(has_text=asset_code_or_name).first
        if row.is_visible(timeout=5000):
            action_btn = row.get_by_role("button", name=re.compile(r"(Complete|Resolve|Update|Action)", re.I)).first
            if action_btn.is_visible():
                action_btn.click()
                self.page.wait_for_timeout(1000)
                
                # Check dialog
                dialog = self.page.locator("[role='dialog'][aria-modal='true'], .chakra-modal__content").first
                if dialog.is_visible(timeout=5000):
                    # Resolution dropdown / select
                    try:
                        res_select = dialog.get_by_label("Status", exact=False).first
                        if not res_select.is_visible():
                            res_select = dialog.locator("select").first
                        if res_select.is_visible():
                            res_select.select_option(label=resolution)
                    except Exception:
                        pass
                    
                    if remarks:
                        try:
                            dialog.locator("textarea, input[placeholder*='Remarks']").first.fill(remarks)
                        except Exception:
                            pass
                            
                    submit_btn = dialog.get_by_role("button", name=re.compile(r"(Complete|Save|Submit|Update)", re.I)).first
                    if submit_btn.is_visible():
                        submit_btn.click()

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)
