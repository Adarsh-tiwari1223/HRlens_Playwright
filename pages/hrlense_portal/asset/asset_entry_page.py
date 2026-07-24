import logging
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)

class AssetEntryPage(BasePage):
    ADD_ASSET_BTN = "role=button[name='Add Asset']"
    SAVE_BTN = "role=button[name='Save & Generate QR']"
    CANCEL_BTN = "role=button[name='Cancel']"
    TOAST = "#chakra-toast-manager-top-right"

    def navigate_to_asset_entry(self):
        logger.info("Navigating to Asset Entry page")
        self.page.goto(f"{settings.BASE_URL}/asset-entry")
        self.page.wait_for_load_state("domcontentloaded")

    def click_add_asset(self):
        self.page.locator(self.ADD_ASSET_BTN).wait_for(state="visible", timeout=10000)
        self.click(self.ADD_ASSET_BTN)
        self.page.locator("[role='dialog'][aria-modal='true']").wait_for(state="visible", timeout=10000)

    def fill_asset_details(self, name: str, category: str = None, sub_category: str = None, brand: str = None, model: str = None, serial_no: str = None, warranty: str = None, expiry_date: str = None, notes: str = None) -> tuple[str, str]:
        logger.info(f"Filling asset details: Name={name}")
        
        # Asset Name *
        self.page.get_by_placeholder("e.g. Dell Latitude").fill(name)
        
        # Category *
        category_select = self.page.get_by_label("Category*")
        category_select.select_option(index=1)
        self.page.wait_for_timeout(500)
        selected_category = category_select.evaluate("el => el.options[el.selectedIndex].text").strip()
        
        # Sub Category
        sub_select = self.page.get_by_label("Sub Category")
        sub_select.wait_for(state="visible")
        sub_select.select_option(index=1)
        self.page.wait_for_timeout(500)
        selected_sub_category = sub_select.evaluate("el => el.options[el.selectedIndex].text").strip()
            
        # Brand
        if brand:
            self.page.get_by_placeholder("e.g. Dell", exact=True).fill(brand)
            
        # Model No.
        if model:
            self.page.get_by_placeholder("e.g. Latitude").fill(model)
            
        # Serial No.
        if serial_no:
            self.page.get_by_placeholder("Manufacturer serial number").fill(serial_no)
            
        # Warranty / Guarantee
        if warranty:
            self.page.get_by_label("Warranty / Guarantee", exact=False).select_option(label=warranty)
            
        # Expiry Date
        if expiry_date:
            # Expiry date uses a native date input associated with label
            self.page.get_by_label("Expiry Date").fill(expiry_date)
            
        # Notes
        if notes:
            self.page.get_by_placeholder("Any additional notes…").fill(notes)

        return selected_category, selected_sub_category

    def click_save(self):
        self.click(self.SAVE_BTN)

    def click_cancel(self):
        self.click(self.CANCEL_BTN)

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)
