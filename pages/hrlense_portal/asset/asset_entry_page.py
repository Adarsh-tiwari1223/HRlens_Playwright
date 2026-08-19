import re
import logging
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)

class AssetEntryPage(BasePage):
    ADD_ASSET_BTN = "role=button[name='Add Asset']"
    GENERATE_ASSETS_BTN = "button:has-text('Generate Assets'), [role='button']:has-text('Generate Assets')"
    SAVE_BTN = "role=button[name='Save & Generate QR']"
    CANCEL_BTN = "role=button[name='Cancel']"
    TOAST = "#chakra-toast-manager-top-right, .chakra-toast, [role='status'], [role='alert']"

    def navigate_to_asset_entry(self):
        """Navigates to Asset Entry page and ensures DOM is fully loaded."""
        logger.info("Navigating to Asset Entry page")
        self.page.goto(f"{settings.BASE_URL}/asset-entry")
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(1000)

    def click_add_asset(self):
        """Opens standard Add Asset manual creation modal."""
        logger.info("Clicking 'Add Asset' / 'Add New Asset' button...")
        btn = self.page.get_by_role("button", name=re.compile(r"Add\s*(New)?\s*Asset", re.I)).first
        if not btn.is_visible(timeout=2000):
            btn = self.page.locator("button").filter(has_text=re.compile(r"Add\s*(New)?\s*Asset", re.I)).first
        if not btn.is_visible(timeout=2000):
            btn = self.page.locator(self.ADD_ASSET_BTN)

        btn.wait_for(state="visible", timeout=10000)
        btn.click()
        self.page.locator("[role='dialog'][aria-modal='true'], .chakra-modal__content").wait_for(state="visible", timeout=10000)
        logger.info("Verified 'Add New Asset' form/modal is visible.")

    def click_generate_assets_button(self):
        """Clicks the 'Generate Assets' button and waits for drawer/modal with header 'Generate Assets' to open."""
        logger.info("Clicking 'Generate Assets' button...")
        btn = self.page.get_by_text("Generate Assets", exact=True).first
        if not btn.is_visible(timeout=2000):
            btn = self.page.locator("button").filter(has_text=re.compile(r"^Generate Assets$", re.I)).first
        if not btn.is_visible(timeout=2000):
            btn = self.page.locator("button:has-text('Generate Assets')").first

        btn.wait_for(state="visible", timeout=10000)
        btn.click()

        # Wait for drawer/modal header 'Generate Assets' to become visible
        header_el = self.page.locator("header:has-text('Generate Assets'), [role='dialog'] header:has-text('Generate Assets'), .chakra-modal__header:has-text('Generate Assets')").first
        header_el.wait_for(state="visible", timeout=10000)
        logger.info("Verified 'Generate Assets' modal/drawer header is visible.")

    def fill_generate_assets_form(self, procurement_code: str = None) -> dict:
        """
        Fills the Generate Assets form:
        1. Selects Procurement from dropdown (by code e.g. 'PROC-...' or by finding one with available items).
        2. Waits for dynamic Procurement Item dropdown to populate and selects the item.
        """
        logger.info("Filling Generate Assets form...")

        # Target the exact Procurement dropdown container
        proc_select = self.page.locator("//div[./label[normalize-space()='Procurement']]//select").first
        if not proc_select.is_visible(timeout=2000):
            proc_select = self.page.locator("label:has-text('Procurement')").locator("..").locator("select").first
        proc_select.wait_for(state="visible", timeout=10000)

        # Target the exact Procurement Item dropdown container
        item_select = self.page.locator("//div[./label[normalize-space()='Procurement Item']]//select").first
        if not item_select.is_visible(timeout=2000):
            item_select = self.page.locator("label:has-text('Procurement Item')").locator("..").locator("select").first
        item_select.wait_for(state="visible", timeout=10000)

        selected_proc = ""
        selected_item = ""

        # If specific procurement code provided:
        if procurement_code:
            try:
                proc_select.select_option(label=procurement_code)
                selected_proc = procurement_code
            except Exception:
                options = proc_select.locator("option").all()
                for opt in options:
                    if procurement_code in opt.inner_text():
                        val = opt.get_attribute("value")
                        proc_select.select_option(value=val)
                        selected_proc = opt.inner_text().strip()
                        break
            self.page.wait_for_timeout(1000)
            item_options = item_select.locator("option").all()
            for opt in item_options[1:]:
                val = opt.get_attribute("value")
                txt = opt.inner_text().strip()
                if val and val.strip() != "" and "select" not in txt.lower():
                    item_select.select_option(value=val)
                    selected_item = txt
                    break

        # If not selected or no items populated yet, iterate through all available procurements:
        if not selected_item:
            proc_options = proc_select.locator("option").all()
            for p_opt in proc_options[1:]:
                p_val = p_opt.get_attribute("value")
                p_txt = p_opt.inner_text().strip()
                if not p_val or "select" in p_txt.lower():
                    continue

                proc_select.select_option(value=p_val)
                selected_proc = p_txt
                logger.info(f"Checking Procurement: '{selected_proc}' (val={p_val})")

                # Wait briefly for items to load via API
                self.page.wait_for_timeout(1200)
                item_options = item_select.locator("option").all()
                valid_items = [
                    opt for opt in item_options[1:]
                    if opt.get_attribute("value") and opt.get_attribute("value").strip() != "" and "select" not in opt.inner_text().lower()
                ]
                if valid_items:
                    target_item = valid_items[0]
                    item_select.select_option(value=target_item.get_attribute("value"))
                    selected_item = target_item.inner_text().strip()
                    logger.info(f"Successfully selected Procurement Item: '{selected_item}' from '{selected_proc}'")
                    break

        logger.info(f"Selected Procurement: '{selected_proc}', Item: '{selected_item}'")
        return {"procurement": selected_proc, "item": selected_item}

    def click_generate_assets_submit(self) -> str:
        """
        Clicks the modal's 'Generate Assets' submit button, waits for any loading spinner to finish,
        and captures the confirmation toast message.
        """
        logger.info("Clicking 'Generate Assets' submit button...")
        modal = self.page.locator("[role='dialog'], .chakra-modal__content").first
        if not modal.is_visible(timeout=500):
            modal = self.page

        btn = modal.locator("button").filter(has_text=re.compile(r"^Generate Assets$", re.I)).first
        if not btn.is_visible(timeout=2000):
            btn = self.page.locator("button").filter(has_text=re.compile(r"Generate Assets", re.I)).first

        btn.scroll_into_view_if_needed()
        self.page.wait_for_timeout(300)
        try:
            btn.click(timeout=5000)
        except Exception:
            btn.click(force=True)

        # 1. Wait for loading spinner to detach
        try:
            spinner = self.page.locator(".chakra-spinner, span:has-text('Loading...'), [data-loading]").first
            if spinner.is_visible(timeout=1000):
                logger.info("Waiting for Generate Assets spinner to complete...")
                spinner.wait_for(state="detached", timeout=30000)
        except Exception:
            pass

        # 2. Wait for confirmation toast to appear
        toast_msg = ""
        try:
            toast_loc = self.page.locator(".chakra-toast, [role='status'], [role='alert'], .chakra-alert").first
            toast_loc.wait_for(state="visible", timeout=10000)
            toast_msg = toast_loc.inner_text().strip()
            logger.info(f"Generate Assets Toast captured: '{toast_msg}'")
        except Exception as e:
            logger.warning(f"Toast capture note: {e}")

        return toast_msg

    def click_add_asset(self):
        """Opens standard Add New Asset manual creation modal."""
        logger.info("Clicking 'Add New Asset' button...")
        btn = self.page.get_by_text("Add New Asset", exact=True).first
        if not btn.is_visible(timeout=2000):
            btn = self.page.locator("button").filter(has_text=re.compile(r"^Add (New )?Asset$", re.I)).first
        if not btn.is_visible(timeout=2000):
            btn = self.page.locator("button:has-text('Add New Asset'), button:has-text('Add Asset')").first

        btn.wait_for(state="visible", timeout=10000)
        btn.click()

        form_indicator = self.page.locator("label:has-text('Asset Name'), header:has-text('Add New Asset'), h2:has-text('Add New Asset'), .chakra-modal__content").first
        form_indicator.wait_for(state="visible", timeout=10000)
        logger.info("Verified 'Add New Asset' form/modal is visible.")

    def fill_asset_details(
        self,
        name: str,
        category: str = None,
        sub_category: str = None,
        brand: str = None,
        model: str = None,
        serial_no: str = None,
        warranty: str = None,
        expiry_date: str = None,
        insured: str = "No",
        insurance_provider: str = "ICICI Lombard",
        policy_number: str = "POL-883920",
        premium_amount: str = "1200",
        premium_frequency: str = "Yearly",
        insurance_start_date: str = "2025-01-01",
        insurance_expiry_date: str = "2026-12-31",
        notes: str = None,
        category_label: str = None,
        sub_category_label: str = None,
        **kwargs
    ) -> dict:
        category = category or category_label
        sub_category = sub_category or sub_category_label
        policy_number = policy_number or f"POL-{random.randint(100000, 999999)}"
        insurance_provider = insurance_provider or "ICICI Lombard"
        """
        Populates all fields on the 'Add New Asset' modal:
        1. Asset Name *
        2. Category *
        3. Sub Category * (wait for enabled)
        4. Brand
        5. Model No.
        6. Serial No.
        7. Warranty / Guarantee
        8. Expiry Date (enabled after step 7)
        9. Insured? (Yes/No)
           If Yes:
           10.1 Insurance Provider *
           10.2 Policy Number *
           10.3 Premium Amount (₹)
           10.4 Premium Frequency *
           10.5 Start Date
           10.6 Expiry Date *
        10. Notes
        """
        logger.info(f"Filling Add Asset modal details: Name='{name}', Brand='{brand}', Serial='{serial_no}', Insured='{insured}'")
        modal = self.page.locator(".chakra-modal__content, [aria-modal='true'], .chakra-drawer__content").first
        if not modal.is_visible(timeout=1000):
            modal = self.page

        # 1. Asset Name *
        name_in = modal.locator("//div[./label[contains(text(), 'Asset Name')]]//input").first
        if not name_in.is_visible(timeout=1000):
            name_in = modal.get_by_placeholder("e.g. Dell Latitude").first
        if not name_in.is_visible(timeout=1000):
            name_in = modal.locator("input[placeholder*='Latitude' i], input[name*='name' i]").first
        name_in.wait_for(state="visible", timeout=5000)
        name_in.fill(name)

        # 2. Category *
        cat_select = modal.locator("//div[./label[contains(text(), 'Category') and not(contains(text(), 'Sub'))]]//select").first
        if not cat_select.is_visible(timeout=1000):
            cat_select = modal.get_by_label("Category*", exact=False).first
        cat_select.wait_for(state="visible", timeout=5000)

        selected_category = ""
        if category:
            try:
                cat_select.select_option(label=category)
                selected_category = category
            except Exception:
                pass
        if not selected_category:
            options = cat_select.locator("option").all()
            for opt in options[1:]:
                val = opt.get_attribute("value")
                txt = opt.inner_text().strip()
                if val and val.strip() != "" and "select" not in txt.lower():
                    cat_select.select_option(value=val)
                    selected_category = txt
                    break

        logger.info(f"Selected Category: '{selected_category}'")
        self.page.wait_for_timeout(800)

        # 3. Sub Category *
        sub_select = modal.locator("//div[./label[contains(text(), 'Sub Category')]]//select").first
        if not sub_select.is_visible(timeout=1000):
            sub_select = modal.get_by_label("Sub Category", exact=False).first
        sub_select.wait_for(state="visible", timeout=5000)

        # Wait for dynamic Sub Category options to attach
        try:
            sub_select.locator("option:not([value=''])").first.wait_for(state="attached", timeout=5000)
        except Exception:
            pass

        selected_sub_category = ""
        if sub_category:
            try:
                sub_select.select_option(label=sub_category)
                selected_sub_category = sub_category
            except Exception:
                pass
        if not selected_sub_category:
            options = sub_select.locator("option").all()
            for opt in options[1:]:
                val = opt.get_attribute("value")
                txt = opt.inner_text().strip()
                if val and val.strip() != "" and "select" not in txt.lower():
                    sub_select.select_option(value=val)
                    selected_sub_category = txt
                    break

        logger.info(f"Selected Sub Category: '{selected_sub_category}'")

        # 4. Brand
        if brand:
            b_in = modal.locator("//div[./label[normalize-space()='Brand']]//input").first
            if not b_in.is_visible(timeout=500):
                b_in = modal.locator("input[placeholder*='Dell' i], input[name*='brand' i]").first
            if b_in.is_visible(timeout=1000):
                b_in.fill(brand)

        # 5. Model No.
        if model:
            m_in = modal.locator("//div[./label[contains(text(), 'Model')]]//input").first
            if not m_in.is_visible(timeout=500):
                m_in = modal.locator("input[placeholder*='Latitude' i], input[name*='model' i]").first
            if m_in.is_visible(timeout=1000):
                m_in.fill(model)

        # 6. Serial No.
        if serial_no:
            s_in = modal.locator("//div[./label[contains(text(), 'Serial')]]//input").first
            if not s_in.is_visible(timeout=500):
                s_in = modal.locator("input[placeholder*='serial' i], input[name*='serial' i]").first
            if s_in.is_visible(timeout=1000):
                s_in.fill(serial_no)

        # 7. Warranty / Guarantee
        if warranty:
            w_select = modal.locator("//div[./label[contains(text(), 'Warranty / Guarantee')]]//select").first
            if not w_select.is_visible(timeout=500):
                w_select = modal.get_by_label("Warranty", exact=False).first
            if w_select.is_visible(timeout=1000):
                try:
                    w_select.select_option(label=warranty)
                except Exception:
                    w_select.select_option(value=warranty)

        # 8. Expiry Date (enabled after step 7)
        if expiry_date:
            exp_in = modal.locator("//div[./label[contains(text(), 'Expiry Date')]]//input").first
            if not exp_in.is_visible(timeout=500):
                exp_in = modal.locator("input[type='date']").first
            if exp_in.is_visible(timeout=1000):
                exp_in.fill(expiry_date)

        # 9. Insured? (Yes/No)
        if insured:
            ins_select = modal.locator("//div[./label[contains(text(), 'Insured')]]//select").first
            if ins_select.is_visible(timeout=1000):
                try:
                    ins_select.select_option(label=insured)
                except Exception:
                    ins_select.select_option(value=insured)

            # If Insured is Yes / True, fill 10.1 to 10.6 fields
            if str(insured).strip().lower() in ["yes", "true"]:
                self.page.wait_for_timeout(600)

                # 10.1 Insurance Provider *
                if insurance_provider:
                    prov_in = modal.locator("//div[./label[contains(text(), 'Insurance Provider')]]//input").first
                    if not prov_in.is_visible(timeout=1000):
                        prov_in = modal.locator("input[placeholder*='ICICI' i]").first
                    if prov_in.is_visible(timeout=2000):
                        prov_in.fill(insurance_provider)

                # 10.2 Policy Number *
                if policy_number:
                    pol_in = modal.locator("//div[./label[contains(text(), 'Policy Number')]]//input").first
                    if not pol_in.is_visible(timeout=1000):
                        pol_in = modal.get_by_label("Policy Number", exact=False).first
                    if pol_in.is_visible(timeout=2000):
                        pol_in.fill(policy_number)

                # 10.3 Premium Amount (₹)
                if premium_amount:
                    prem_in = modal.locator("//div[./label[contains(text(), 'Premium Amount')]]//input").first
                    if not prem_in.is_visible(timeout=1000):
                        prem_in = modal.get_by_label("Premium Amount", exact=False).first
                    if prem_in.is_visible(timeout=2000):
                        prem_in.fill(premium_amount)

                # 10.4 Premium Frequency *
                if premium_frequency:
                    freq_select = modal.locator("//div[./label[contains(text(), 'Premium Frequency')]]//select").first
                    if freq_select.is_visible(timeout=2000):
                        try:
                            freq_select.select_option(label=premium_frequency)
                        except Exception:
                            freq_select.select_option(value=premium_frequency)

                # 10.5 Start Date
                if insurance_start_date:
                    start_in = modal.locator("//div[./label[contains(text(), 'Start Date')]]//input").first
                    if start_in.is_visible(timeout=2000):
                        start_in.fill(insurance_start_date)

                # 10.6 Expiry Date * (Insurance Expiry Date)
                if insurance_expiry_date:
                    ins_exp_in = modal.locator("//div[./label[contains(text(), 'Expiry Date') and contains(text(), '*')]]//input").last
                    if not ins_exp_in.is_visible(timeout=1000):
                        ins_exp_in = modal.locator("//div[./label[contains(text(), 'Insurance') or contains(text(), 'Expiry Date')]]//input").last
                    if ins_exp_in.is_visible(timeout=2000):
                        ins_exp_in.fill(insurance_expiry_date)

        # 10. Notes
        if notes:
            n_in = modal.locator("//div[./label[contains(text(), 'Notes')]]//textarea").first
            if not n_in.is_visible(timeout=500):
                n_in = modal.locator("textarea").first
            if n_in.is_visible(timeout=1000):
                n_in.fill(notes)

        return {
            "name": name,
            "category": selected_category,
            "sub_category": selected_sub_category,
            "brand": brand,
            "model": model,
            "serial_no": serial_no,
            "warranty": warranty,
            "expiry_date": expiry_date,
            "insured": insured,
            "insurance_provider": insurance_provider,
            "policy_number": policy_number,
            "premium_amount": premium_amount,
            "premium_frequency": premium_frequency
        }

    def click_save_and_generate_qr(self) -> str:
        """Clicks 'Save & Generate QR' button, waits for loading spinner, and captures confirmation toast."""
        logger.info("Clicking 'Save & Generate QR' button...")
        modal = self.page.locator("[role='dialog'], .chakra-modal__content").first
        if not modal.is_visible(timeout=500):
            modal = self.page

        btn = modal.locator("button").filter(has_text=re.compile(r"Save.*Generate QR|Save", re.I)).first
        if not btn.is_visible(timeout=2000):
            btn = self.page.locator("button:has-text('Save & Generate QR'), button:has-text('Save')").first

        btn.scroll_into_view_if_needed()
        self.page.wait_for_timeout(300)
        try:
            btn.click(timeout=5000)
        except Exception:
            btn.click(force=True)

        # Wait for loading spinner to detach
        try:
            spinner = self.page.locator(".chakra-spinner, span:has-text('Loading...'), [data-loading]").first
            if spinner.is_visible(timeout=1000):
                spinner.wait_for(state="detached", timeout=30000)
        except Exception:
            pass

        # Capture toast message
        toast_msg = ""
        try:
            toast_loc = self.page.locator(".chakra-toast, [role='status'], [role='alert'], .chakra-alert").first
            toast_loc.wait_for(state="visible", timeout=10000)
            toast_msg = toast_loc.inner_text().strip()
            logger.info(f"Add Asset Toast captured: '{toast_msg}'")
        except Exception as e:
            logger.warning(f"Toast capture note: {e}")

        return toast_msg

    def search_asset(self, query: str):
        """Searches for asset in the search input box."""
        logger.info(f"Searching asset inventory: '{query}'")
        s_box = self.page.locator("input[placeholder*='Search' i]").first
        if s_box.is_visible(timeout=2000):
            s_box.fill("")
            s_box.fill(query)
            self.page.wait_for_timeout(800)

    def click_save(self):
        return self.click_save_and_generate_qr()

    def click_cancel(self):
        self.click(self.CANCEL_BTN)

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast(self.TOAST)
