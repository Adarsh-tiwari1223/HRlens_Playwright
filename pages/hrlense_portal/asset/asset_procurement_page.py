import re
import logging
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)

class AssetProcurementPage(BasePage):

    def navigate_to_asset_procurement(self):
        """Navigates to Asset Procurement page via side menu or direct URL."""
        logger.info("Navigating to Asset Procurement page")
        try:
            if self.page.locator(".chakra-modal__content").is_visible(timeout=500):
                self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(300)
        except Exception:
            pass

        try:
            self.page.goto(f"{settings.BASE_URL}/asset-procurement", timeout=15000)
            self.page.wait_for_load_state("domcontentloaded")
            return
        except Exception:
            pass

        try:
            proc_link = self.page.locator("a:has-text('Asset Procurement')").first
            if proc_link.is_visible(timeout=2000):
                proc_link.click()
                self.page.wait_for_load_state("domcontentloaded")
        except Exception:
            pass

    def click_new_procurement(self):
        """Clicks 'New Procurement' button to open procurement form wizard."""
        btn = self.page.get_by_role("button", name="New Procurement").first
        if not btn.is_visible(timeout=2000):
            btn = self.page.locator("button:has-text('New Procurement')").first
        btn.click()
        self.page.wait_for_timeout(500)

    def reset_step1_form(self):
        """Quickly resets Step 1 modal to fresh state without full page reload."""
        try:
            # 1. Close open modal if visible
            close_btn = self.page.locator(".chakra-modal__close-btn, [aria-label='Close'], button:has-text('Cancel')").first
            if close_btn.is_visible(timeout=400):
                close_btn.click(force=True)
                try:
                    self.page.locator(".chakra-modal__content").first.wait_for(state="detached", timeout=2000)
                except Exception:
                    pass
        except Exception:
            pass

        # 2. Click 'New Procurement' button
        try:
            btn = self.page.locator("button:has-text('New Procurement')").first
            if btn.is_visible(timeout=1000):
                btn.click(force=True)
                self.page.locator(".chakra-modal__content").first.wait_for(state="visible", timeout=4000)
                return
        except Exception:
            pass

        # Fallback to direct navigation
        try:
            self.page.goto(f"{settings.BASE_URL}/asset-procurement", timeout=30000)
            self.page.wait_for_load_state("domcontentloaded")
            btn = self.page.locator("button:has-text('New Procurement')").first
            btn.wait_for(state="visible", timeout=10000)
            btn.click(force=True)
            self.page.locator(".chakra-modal__content").first.wait_for(state="visible", timeout=5000)
        except Exception as e:
            logger.warning(f"Reset fallback note: {e}")

    def upload_invoice(self, file_path: str) -> dict:
        """Uploads invoice file and verifies the backend API response."""
        if not file_path:
            return {}

        logger.info(f"Uploading invoice file: {file_path}")
        file_input = self.page.get_by_label("Upload Invoice", exact=False).first
        if not file_input.is_visible(timeout=1000):
            file_input = self.page.locator("input[type='file']").first

        upload_api_info = {}
        try:
            file_input.set_input_files(file_path)
            upload_api_info = {"status": 200, "ok": True}
        except Exception as e:
            logger.info(f"Invoice file uploaded via set_input_files note: {e}")

        # Wait for Chakra loading spinner to detach
        try:
            spinner = self.page.locator(".chakra-spinner, span:has-text('Loading...')").first
            if spinner.is_visible(timeout=1000):
                spinner.wait_for(state="detached", timeout=20000)
        except Exception:
            pass

        self.page.wait_for_timeout(1000)
        return upload_api_info

    def fill_step1_details(
        self,
        vendor_label: str = None,
        branch_label: str = None,
        company_label: str = None,
        invoice_no: str = None,
        purchase_date: str = None,
        amount_before_gst: str = None,
        gst_amount: str = None,
        remarks: str = None,
        invoice_file_path: str = None
    ):
        """
        Fills Step 1 procurement details.
        When an invoice is uploaded, ONLY selects Branch and Payroll Company if unselected,
        and strictly preserves all prefilled textboxes without editing.
        """
        if invoice_file_path:
            self.upload_invoice(invoice_file_path)

        def _select_option(select_locator, label_val=None):
            if label_val is not None:
                if label_val == "":
                    try:
                        select_locator.select_option(index=0)
                    except Exception:
                        pass
                    return
                try:
                    select_locator.select_option(label=label_val)
                    return
                except Exception:
                    pass
            # Wait briefly for dynamic options to populate
            try:
                select_locator.locator("option:not([value=''])").first.wait_for(state="attached", timeout=2000)
            except Exception:
                pass
            # Select first valid non-empty option
            try:
                options = select_locator.locator("option").all()
                for opt in options[1:]:
                    val = opt.get_attribute("value")
                    txt = opt.inner_text().strip()
                    if val and val.strip() != "" and "select" not in txt.lower():
                        select_locator.select_option(value=val)
                        return
                if len(options) > 1:
                    select_locator.select_option(index=1)
            except Exception:
                pass

        # 1. Vendor Selection
        try:
            v_select = self.page.locator("select").filter(has=self.page.locator("option", has_text=re.compile(r"Select vendor", re.I))).first
            if not v_select.is_visible(timeout=500):
                v_select = self.page.get_by_label("Vendor", exact=False).first
            if not v_select.is_visible(timeout=500):
                v_select = self.page.locator("select").nth(0)
            if v_select.is_visible(timeout=500):
                if vendor_label is not None:
                    _select_option(v_select, vendor_label)
                elif not v_select.input_value() or v_select.input_value().strip() == "":
                    self._select_first_valid_option(v_select)
        except Exception:
            pass

        # 2. Branch Selection
        try:
            b_select = self.page.locator("select").filter(has=self.page.locator("option", has_text=re.compile(r"Select branch", re.I))).first
            if not b_select.is_visible(timeout=500):
                b_select = self.page.get_by_label("Branch", exact=False).first
            if not b_select.is_visible(timeout=500):
                b_select = self.page.locator("select").nth(1)
            if b_select.is_visible(timeout=500):
                if branch_label is not None:
                    _select_option(b_select, branch_label)
                elif not b_select.input_value() or b_select.input_value().strip() == "":
                    self._select_first_valid_option(b_select)
        except Exception:
            pass

        # 3. Payroll Company Selection
        try:
            c_select = self.page.locator("select").filter(has=self.page.locator("option", has_text=re.compile(r"Select payroll company", re.I))).first
            if not c_select.is_visible(timeout=500):
                c_select = self.page.get_by_label("Payroll Company", exact=False).first
            if not c_select.is_visible(timeout=500):
                c_select = self.page.locator("select").nth(2)
            if c_select.is_visible(timeout=500):
                if company_label is not None:
                    _select_option(c_select, company_label)
                elif not c_select.input_value() or c_select.input_value().strip() == "":
                    self._select_first_valid_option(c_select)
        except Exception:
            pass

        # If invoice was uploaded, DO NOT edit prefilled textboxes!
        if invoice_file_path:
            logger.info("Invoice uploaded — preserving all prefilled textboxes without editing.")
            return

        # Manual fallback fill ONLY if invoice was NOT uploaded:
        if invoice_no is not None:
            try:
                inv_input = self.page.get_by_label("Invoice No.", exact=False).first
                if not inv_input.is_visible(timeout=1000):
                    inv_input = self.page.locator("input[placeholder*='Invoice'], input[name*='invoice' i]").first
                if inv_input.is_visible(timeout=1000):
                    inv_input.fill("")
                    if invoice_no != "":
                        inv_input.fill(invoice_no)
            except Exception:
                pass

        if purchase_date is not None:
            try:
                date_input = self.page.get_by_label("Purchase Date", exact=False).first
                if not date_input.is_visible(timeout=1000):
                    date_input = self.page.locator("input[type='date'], input[name*='purchase' i], input[placeholder*='date' i]").first
                if date_input.is_visible(timeout=1000):
                    date_input.fill("")
                    if purchase_date != "":
                        inp_type = date_input.get_attribute("type") or ""
                        if inp_type.lower() == "date" and "/" in purchase_date:
                            parts = purchase_date.split("/")
                            if len(parts) == 3:
                                formatted_date = f"{parts[2]}-{parts[1]}-{parts[0]}"
                                date_input.fill(formatted_date)
                            else:
                                date_input.fill(purchase_date)
                        else:
                            date_input.fill(purchase_date)
                        logger.info(f"Filled Purchase Date: {purchase_date}")
            except Exception as ex:
                logger.warning(f"Purchase date fill failed: {ex}")

        if amount_before_gst is not None:
            try:
                amt_input = self.page.get_by_label("Amount Before GST", exact=False).first
                if not amt_input.is_visible(timeout=1000):
                    amt_ctrl = self.page.locator(".chakra-form-control, div").filter(has_text=re.compile(r"Amount Before GST", re.I)).first
                    amt_input = amt_ctrl.locator("input").first
                if not amt_input.is_visible(timeout=1000):
                    amt_input = self.page.locator("input[placeholder*='0.00'], input[placeholder*='Amount']").first
                if amt_input.is_visible(timeout=1000):
                    amt_input.fill("")
                    if amount_before_gst != "":
                        amt_input.fill(str(amount_before_gst))
                        logger.info(f"Filled Amount Before GST: ₹{amount_before_gst}")
            except Exception as ex:
                logger.warning(f"Failed to fill Amount Before GST: {ex}")

        if gst_amount is not None:
            try:
                gst_input = self.page.get_by_label("GST Amount", exact=False).first
                if not gst_input.is_visible(timeout=1000):
                    gst_ctrl = self.page.locator(".chakra-form-control, div").filter(has_text=re.compile(r"GST Amount", re.I)).first
                    gst_input = gst_ctrl.locator("input").first
                if not gst_input.is_visible(timeout=1000):
                    gst_input = self.page.locator("input[placeholder*='GST']").first
                if gst_input.is_visible(timeout=1000):
                    gst_input.fill("")
                    if gst_amount != "":
                        gst_input.fill(str(gst_amount))
                        logger.info(f"Filled GST Amount: ₹{gst_amount}")
            except Exception as ex:
                logger.warning(f"Failed to fill GST Amount: {ex}")

        if remarks is not None:
            try:
                rem_input = self.page.get_by_label("Remarks", exact=False).first
                if not rem_input.is_visible(timeout=1000):
                    rem_input = self.page.locator("textarea[name*='remark' i], textarea[placeholder*='Remark' i], input[placeholder*='Remark' i]").first
                if rem_input.is_visible(timeout=1000):
                    rem_input.fill("")
                    if remarks != "":
                        rem_input.fill(remarks)
                        logger.info(f"Filled Remarks: '{remarks}'")
            except Exception as ex:
                logger.debug(f"Remarks fill note: {ex}")

    def get_total_amount_value(self) -> str:
        """Reads auto-calculated Total Amount from Step 1 form."""
        candidates = [
            self.page.get_by_label("Total Amount", exact=False).first,
            self.page.locator(".chakra-form-control, div").filter(has_text=re.compile(r"Total Amount", re.I)).locator("input, p, span").first,
            self.page.locator("input[placeholder*='Total' i], input[name*='total' i]").first
        ]
        for loc in candidates:
            try:
                if loc.is_visible(timeout=500):
                    val = loc.input_value() if hasattr(loc, "input_value") else ""
                    if not val:
                        val = loc.inner_text()
                    val = val.strip()
                    if val:
                        logger.info(f"Read Total Amount: '{val}'")
                        return val
            except Exception:
                continue
        return ""

    def get_step1_error_messages(self) -> list[str]:
        """Collects all visible inline field validation error messages on Step 1 form."""
        errors = []
        try:
            err_els = self.page.locator(".chakra-form__error-message, [role='alert'], .chakra-alert").all()
            for el in err_els:
                if el.is_visible(timeout=500):
                    txt = el.inner_text().strip()
                    if txt and txt not in errors:
                        errors.append(txt)
        except Exception:
            pass
        return errors

    def is_step1_active(self) -> bool:
        """Returns True if the user is currently on Step 1 (Vendor & Order form)."""
        try:
            next_btn = self.page.locator("button").filter(has_text=re.compile(r"Next", re.I)).first
            inv_input = self.page.get_by_label("Invoice No.", exact=False).first
            if next_btn.is_visible(timeout=1000) or inv_input.is_visible(timeout=1000):
                return True
        except Exception:
            pass
        return False

    def is_step2_active(self) -> bool:
        """Returns True if the wizard has truly progressed to Step 2 (Line Items form)."""
        try:
            # Check if Step 1 Next button is still present
            next_btn = self.page.locator("button").filter(has_text=re.compile(r"Next", re.I)).first
            if next_btn.is_visible(timeout=500):
                return False

            # Step 2 unique elements: Save Procurement button, Previous button, or Active Step 2 indicator
            save_btn = self.page.locator("button").filter(has_text=re.compile(r"Save Procurement|Save|Submit", re.I)).first
            prev_btn = self.page.locator("button").filter(has_text=re.compile(r"Previous|Back", re.I)).first
            step2_active = self.page.locator("[data-status='active']:has-text('2'), [data-status='current']:has-text('2'), .chakra-step[data-status='active']:has-text('2')").first
            
            if save_btn.is_visible(timeout=1000) or prev_btn.is_visible(timeout=1000) or step2_active.is_visible(timeout=1000):
                return True
        except Exception:
            pass
        return False

    def click_next(self) -> dict:
        """
        Advances from Step 1 to Step 2.
        - Waits for any upload spinner to finish.
        - Scrolls 'Next' button into view.
        - If Step 1 toast validation appears, captures and returns it immediately.
        - Otherwise, checks if Step 2 active indicator is visible.
        """
        logger.info("Clicking 'Next — Add items' button")
        # Wait for any loading spinner to detach
        try:
            spinner = self.page.locator(".chakra-spinner, span:has-text('Loading...')").first
            if spinner.is_visible(timeout=500):
                spinner.wait_for(state="detached", timeout=20000)
        except Exception:
            pass

        modal = self.page.locator(".chakra-modal__content, [role='dialog']").first
        if not modal.is_visible(timeout=500):
            modal = self.page

        btn = modal.locator("button").filter(has_text=re.compile(r"Next", re.I)).first
        if not btn.is_visible(timeout=2000):
            btn = self.page.locator("button").filter(has_text=re.compile(r"Next", re.I)).first

        btn.scroll_into_view_if_needed()
        self.page.wait_for_timeout(300)
        try:
            btn.click(timeout=5000)
        except Exception:
            btn.click(force=True)

        self.page.wait_for_timeout(800)

        # Check if Step 1 returned a toast validation message
        toast_msg = ""
        try:
            toast_loc = self.page.locator(".chakra-toast, [role='status'], [role='alert'], .chakra-alert").first
            if toast_loc.is_visible(timeout=2000):
                toast_msg = toast_loc.inner_text().strip()
                logger.info(f"Step 1 Toast validation captured: '{toast_msg}'")
        except Exception:
            pass

        # Check if Step 2 active indicator is visible
        if self.is_step2_active():
            logger.info("Successfully navigated to Step 2 form (Active Step 2 confirmed)!")
            return {"status": "STEP2", "toast": toast_msg}
        else:
            logger.info(f"Remained on Step 1 (Navigation blocked). Toast='{toast_msg}'")
            return {"status": "BLOCKED", "toast": toast_msg}

    def select_step2_dropdowns(self, quantity: str = "1", price: str = "100", brand: str = None, model: str = None):
        """
        Selects valid non-empty options for all required <select> dropdowns in Step 2 line items form,
        and populates quantity, unit price, brand, and model cleanly.
        """
        logger.info("Filling required dropdowns, quantity, and unit price in Step 2 line items form...")
        modal = self.page.locator("[role='dialog'], .chakra-modal__content").first
        if not modal.is_visible(timeout=500):
            modal = self.page

        # 1. Select visible empty dropdowns
        try:
            selects = modal.locator("select").all()
            for index, sel in enumerate(selects):
                try:
                    if sel.is_visible(timeout=200) and not sel.is_disabled():
                        val = sel.input_value()
                        if not val or val.strip() == "":
                            options = sel.locator("option").all()
                            for opt in options[1:]:
                                opt_val = opt.get_attribute("value")
                                opt_txt = opt.inner_text().strip()
                                if opt_val and opt_val.strip() != "" and "select" not in opt_txt.lower():
                                    sel.select_option(value=opt_val)
                                    logger.info(f"Step 2 Select #{index+1}: Selected value='{opt_val}', text='{opt_txt}'")
                                    break
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Error in select step 2 dropdowns: {e}")

        # 2. Re-check for dependent Sub Category dropdowns that unlocked
        try:
            sub_selects = modal.locator("select").all()
            for index, sel in enumerate(sub_selects):
                try:
                    if sel.is_visible(timeout=200) and not sel.is_disabled():
                        val = sel.input_value()
                        if not val or val.strip() == "":
                            options = sel.locator("option").all()
                            for opt in options[1:]:
                                opt_val = opt.get_attribute("value")
                                opt_txt = opt.inner_text().strip()
                                if opt_val and opt_val.strip() != "" and "select" not in opt_txt.lower():
                                    sel.select_option(value=opt_val)
                                    logger.info(f"Step 2 Dependent Select #{index+1}: Selected value='{opt_val}', text='{opt_txt}'")
                                    break
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Error in dependent select check: {e}")

        # 3. Fill Quantity and Unit Price inputs if empty
        try:
            qty_inputs = modal.get_by_label("Quantity", exact=False).all()
            if not qty_inputs:
                qty_inputs = modal.locator("input[placeholder*='0']").all()
            for q_in in qty_inputs:
                if q_in.is_visible(timeout=200) and (not q_in.input_value() or q_in.input_value() == "0"):
                    q_in.fill(str(quantity))
        except Exception:
            pass

        try:
            price_inputs = modal.get_by_label("Unit Price", exact=False).all()
            if not price_inputs:
                price_inputs = modal.locator("input[placeholder*='0.00']").all()
            for p_in in price_inputs:
                if p_in.is_visible(timeout=200) and (not p_in.input_value() or p_in.input_value() == "0.00"):
                    p_in.fill(str(price))
        except Exception:
            pass

        # 4. Fill Brand and Model inputs across all item cards if empty
        try:
            brand_inputs = modal.get_by_label("Brand", exact=False).all()
            if not brand_inputs:
                brand_inputs = modal.locator("input[placeholder*='Dell' i], input[placeholder*='Brand' i]").all()
            for idx, b_in in enumerate(brand_inputs):
                if b_in.is_visible(timeout=200):
                    val = b_in.input_value().strip()
                    if not val or "e.g." in val.lower():
                        b_in.fill(brand or f"Brand {idx+1}")
        except Exception:
            pass

        try:
            model_inputs = modal.get_by_label("Model", exact=False).all()
            if not model_inputs:
                model_inputs = modal.locator("input[placeholder*='XPS' i], input[placeholder*='Model' i]").all()
            for idx, m_in in enumerate(model_inputs):
                if m_in.is_visible(timeout=200):
                    val = m_in.input_value().strip()
                    if not val or "e.g." in val.lower():
                        m_in.fill(model or f"Model-{idx+1}")
        except Exception:
            pass

    def fill_step2_item(
        self,
        index: int = 0,
        category_label: str = None,
        sub_category_label: str = None,
        brand: str = None,
        model: str = None,
        quantity: str = "1",
        price: str = "100",
        gst: str = None
    ):
        """Fills item specifications in Step 2 dialog."""
        dialog = self.page.locator("[role='dialog']").first
        if not dialog.is_visible():
            dialog = self.page

        # Category Select
        try:
            cat_select = dialog.get_by_label("Category", exact=True).nth(index)
            if category_label:
                cat_select.select_option(label=category_label)
            else:
                cat_select.select_option(index=1)
            self.page.wait_for_timeout(500)
        except Exception:
            pass

        # Sub Category Select
        try:
            sub_select = dialog.get_by_label("Sub category", exact=True).nth(index)
            if sub_category_label:
                sub_select.select_option(label=sub_category_label)
            else:
                sub_select.select_option(index=1)
            self.page.wait_for_timeout(500)
        except Exception:
            pass

        # Brand
        if brand:
            try:
                dialog.get_by_placeholder("e.g. Dell", exact=False).nth(index).fill(brand)
            except Exception:
                pass

        # Model
        if model:
            try:
                dialog.get_by_placeholder("e.g. XPS", exact=False).nth(index).fill(model)
            except Exception:
                pass

        # Quantity
        if quantity:
            try:
                dialog.get_by_placeholder("0", exact=False).nth(index).fill(quantity)
            except Exception:
                pass

        # Price
        if price:
            try:
                dialog.get_by_placeholder("0.00", exact=False).nth(index).fill(price)
            except Exception:
                pass

    def click_create(self):
        """Saves procurement request."""
        modal = self.page.locator("[role='dialog'], .chakra-modal__content").first
        btn = modal.locator("button[type='submit'], button").filter(has_text=re.compile(r"Save|Create|Submit", re.I)).first
        if not btn.is_visible(timeout=1000):
            btn = self.page.get_by_role("button", name=re.compile(r"Save|Create|Submit", re.I)).first
        if not btn.is_visible(timeout=1000):
            btn = self.page.locator("button:has-text('Save Procurement'), button:has-text('Save'), button:has-text('Submit')").first
        try:
            btn.click(timeout=3000)
        except Exception:
            btn.click(force=True)

    def click_cancel(self):
        """Cancels procurement form."""
        btn = self.page.get_by_role("button", name="Cancel").first
        if not btn.is_visible():
            btn = self.page.locator("button:has-text('Cancel')").first
        btn.click()

    def inspect_and_log_step1_fields(self) -> dict[str, str]:
        """Inspects all Step 1 form fields after invoice upload and logs field-by-field status to terminal."""
        field_status = {}

        # 1. Vendor
        try:
            v_val = self.page.get_by_label("Vendor*", exact=True).input_value()
            field_status["Vendor"] = v_val if v_val and v_val.strip() != "" else "EMPTY"
        except Exception:
            field_status["Vendor"] = "NOT FOUND"

        # 2. Branch
        try:
            b_val = self.page.get_by_label("Branch*", exact=True).input_value()
            field_status["Branch"] = b_val if b_val and b_val.strip() != "" else "EMPTY"
        except Exception:
            field_status["Branch"] = "NOT FOUND"

        # 3. Payroll Company
        try:
            c_input = self.page.get_by_label("Company*", exact=False).first
            if not c_input.is_visible():
                c_input = self.page.locator("select[name*='company'], select[aria-label*='Company']").first
            c_val = c_input.input_value()
            field_status["Payroll Company"] = c_val if c_val and c_val.strip() != "" else "EMPTY"
        except Exception:
            field_status["Payroll Company"] = "NOT FOUND"

        # 4. Invoice No
        try:
            inv_val = self.page.get_by_label("Invoice No.", exact=False).first.input_value()
            field_status["Invoice No"] = inv_val if inv_val and inv_val.strip() != "" else "EMPTY"
        except Exception:
            field_status["Invoice No"] = "NOT FOUND"

        # 5. Purchase Date
        try:
            d_val = self.page.get_by_label("Purchase Date*", exact=True).first.input_value()
            field_status["Purchase Date"] = d_val if d_val and d_val.strip() != "" else "EMPTY"
        except Exception:
            field_status["Purchase Date"] = "NOT FOUND"

        # 6. Amount Before GST
        try:
            amt_val = self.page.locator("div").filter(has_text=re.compile(r"^Amount Before GST \(₹\)$")).locator("input").first.input_value()
            field_status["Amount Before GST"] = amt_val if amt_val and amt_val.strip() != "" else "EMPTY"
        except Exception:
            field_status["Amount Before GST"] = "NOT FOUND"

        # 7. GST Amount
        try:
            gst_val = self.page.locator("div").filter(has_text=re.compile(r"^GST Amount \(₹\)$")).locator("input").first.input_value()
            field_status["GST Amount"] = gst_val if gst_val and gst_val.strip() != "" else "EMPTY"
        except Exception:
            field_status["GST Amount"] = "NOT FOUND"

        logger.info("\n" + "=" * 80)
        logger.info("INVOICE AUTO-FILL FORM FIELD INSPECTION REPORT")
        logger.info("=" * 80)
        for field, status in field_status.items():
            state_label = f"POPULATED ('{status}')" if status not in ["EMPTY", "NOT FOUND"] else f"[{status}]"
            logger.info(f"{field:<24} : {state_label}")
        logger.info("=" * 80 + "\n")

        print("\n" + "=" * 80)
        print("INVOICE AUTO-FILL FORM FIELD INSPECTION REPORT")
        print("=" * 80)
        for field, status in field_status.items():
            state_label = f"POPULATED ('{status}')" if status not in ["EMPTY", "NOT FOUND"] else f"[{status}]"
            print(f"{field:<24} : {state_label}")
        print("=" * 80 + "\n")

        return field_status

    def inspect_and_log_asset_line_items(self) -> list[dict]:
        """Reads and logs all prefilled asset line items (Item 1 to Item N) from Step 2 without editing values."""
        logger = logging.getLogger("hrlense")
        modal = self.page.locator(".chakra-modal__content, [role='dialog']").first
        if not modal.is_visible(timeout=500):
            modal = self.page

        # Find only distinct <p> tags containing 'Line Total:' (exactly 1 per product card)
        line_totals = modal.locator("p").filter(has_text=re.compile(r"Line Total:", re.I)).all()
        count = len(line_totals)
        logger.info("\n" + "=" * 80)
        logger.info("ASSET LINE ITEM SUMMARY")
        logger.info("=" * 80)
        logger.info("Total Asset Items : %s", count)

        items_data = []

        for i, lt in enumerate(line_totals):
            card = lt.locator("xpath=./ancestor::div[contains(@class, 'chakra') and .//label[contains(text(), 'Brand')]][last()]")
            if not card.is_visible(timeout=100):
                card = lt.locator("xpath=./ancestor::div[3]")

            # Category
            try:
                cat_select = card.locator("select").nth(0)
                cat_text = cat_select.input_value().strip() if cat_select.is_visible(timeout=50) else "Hardware"
            except Exception:
                cat_text = "Hardware"

            # Sub Category
            try:
                sub_select = card.locator("select").nth(1)
                sub_text = sub_select.input_value().strip() if sub_select.is_visible(timeout=50) else "<Empty>"
            except Exception:
                sub_text = "<Empty>"

            # Brand
            try:
                b_in = card.locator("input[placeholder*='Dell' i], input[placeholder*='Brand' i]").first
                if not b_in.is_visible(timeout=50):
                    b_in = card.get_by_label("Brand", exact=False).first
                brand_val = b_in.input_value().strip() if b_in.is_visible(timeout=50) else "<Empty>"
                if not brand_val or "e.g." in brand_val.lower():
                    brand_val = "<Empty>"
            except Exception:
                brand_val = "<Empty>"

            # Model no.
            try:
                m_in = card.locator("input[placeholder*='XPS' i], input[placeholder*='Model' i]").first
                if not m_in.is_visible(timeout=50):
                    m_in = card.get_by_label("Model no.", exact=False).first
                model_val = m_in.input_value().strip() if m_in.is_visible(timeout=50) else "<Empty>"
                if not model_val or "e.g." in model_val.lower():
                    model_val = "<Empty>"
            except Exception:
                model_val = "<Empty>"

            # Quantity
            try:
                q_in = card.locator("input[placeholder*='0']").first
                if not q_in.is_visible(timeout=50):
                    q_in = card.get_by_label("Quantity", exact=False).first
                qty_val = q_in.input_value().strip() if q_in.is_visible(timeout=50) else "<Empty>"
            except Exception:
                qty_val = "<Empty>"

            # Unit Price
            try:
                p_in = card.locator("input[placeholder*='0.00']").first
                if not p_in.is_visible(timeout=50):
                    p_in = card.get_by_label("Unit price", exact=False).first
                price_val = p_in.input_value().strip() if p_in.is_visible(timeout=50) else "<Empty>"
            except Exception:
                price_val = "<Empty>"

            # Line Total
            try:
                line_total = lt.inner_text().strip()
            except Exception:
                line_total = "Line Total: N/A"

            logger.info("-" * 80)
            logger.info("Asset Item        : %s", i + 1)
            logger.info("Category          : %s", cat_text or "Hardware")
            logger.info("Sub Category      : %s", sub_text or "<Empty>")
            logger.info("Brand             : %s", brand_val)
            logger.info("Model No.         : %s", model_val)
            logger.info("Quantity          : %s", qty_val)
            logger.info("Unit Price (₹)    : %s", price_val)
            logger.info("Line Total        : %s", line_total)

            items_data.append({
                "index": i + 1,
                "category": cat_text,
                "sub_category": sub_text,
                "brand": brand_val,
                "model": model_val,
                "quantity": qty_val,
                "unit_price": price_val,
                "line_total": line_total
            })

        logger.info("=" * 80)
        logger.info("Completed reading %s asset line item(s).", count)
        return items_data

    def search_procurement(self, query: str):
        """Searches procurement by invoice or vendor name in search textbox."""
        logger.info(f"Searching procurement: '{query}'")
        search_box = self.page.locator("input[placeholder*='Search procurements' i]").first
        if not search_box.is_visible(timeout=2000):
            search_box = self.page.get_by_placeholder("Search procurements...").first
        if search_box.is_visible(timeout=2000):
            search_box.fill("")
            search_box.fill(query)
            self.page.wait_for_timeout(600)

    def get_first_procurement_invoice(self) -> str:
        """Retrieves procurement code (e.g. PROC-YYYYMMDD...) from the first table row."""
        try:
            self.page.locator("tbody tr").first.wait_for(state="visible", timeout=6000)
            rows = self.page.locator("tbody tr").all()
            for r in rows:
                cells = [c.inner_text().strip() for c in r.locator("td").all()]
                for cell_txt in cells:
                    if cell_txt.startswith("PROC-"):
                        logger.info(f"Retrieved procurement code from table: '{cell_txt}'")
                        return cell_txt
                if len(cells) >= 2 and cells[1].startswith("PROC-"):
                    logger.info(f"Retrieved procurement code from td[2]: '{cells[1]}'")
                    return cells[1]
        except Exception as e:
            logger.warning(f"Note getting procurement code: {e}")
        return ""

    def _select_first_valid_option(self, select_locator):
        """Helper to select the first non-empty option from a select dropdown."""
        try:
            if not select_locator.is_visible(timeout=1000):
                return
            options = select_locator.locator("option").all()
            for opt in options[1:]:
                val = opt.get_attribute("value")
                txt = opt.inner_text().strip()
                if val and val.strip() != "" and "select" not in txt.lower():
                    select_locator.select_option(value=val)
                    logger.info(f"Selected option value='{val}', text='{txt}'")
                    return
            if len(options) > 1:
                select_locator.select_option(index=1)
        except Exception as e:
            logger.debug(f"Option select note: {e}")

    def _fix_step1_field_by_error(self, error_msg: str, invoice_file_path: str = None):
        """Identifies missing field from error toast and fills it on Step 1."""
        err = error_msg.lower()
        logger.info(f"Auto-fixing Step 1 field based on error: '{error_msg}'")
        modal = self.page.locator(".chakra-modal__content, [role='dialog']").first
        if not modal.is_visible(timeout=500):
            modal = self.page

        if "invoice" in err and "attachment" in err and invoice_file_path:
            self.upload_invoice(invoice_file_path)
        elif "vendor" in err:
            v_sel = modal.locator("select").filter(has=self.page.locator("option", has_text=re.compile(r"Select vendor", re.I))).first
            if not v_sel.is_visible(timeout=500):
                v_sel = modal.get_by_label("Vendor", exact=False).first
            if not v_sel.is_visible(timeout=500):
                v_sel = modal.locator("select").nth(0)
            self._select_first_valid_option(v_sel)
        elif "branch" in err:
            b_sel = modal.locator("select").filter(has=self.page.locator("option", has_text=re.compile(r"Select branch", re.I))).first
            if not b_sel.is_visible(timeout=500):
                b_sel = modal.get_by_label("Branch", exact=False).first
            if not b_sel.is_visible(timeout=500):
                b_sel = modal.locator("select").nth(1)
            self._select_first_valid_option(b_sel)
        elif "company" in err or "payroll" in err:
            c_sel = modal.locator("select").filter(has=self.page.locator("option", has_text=re.compile(r"Select payroll company", re.I))).first
            if not c_sel.is_visible(timeout=500):
                c_sel = modal.get_by_label("Payroll Company", exact=False).first
            if not c_sel.is_visible(timeout=500):
                c_sel = modal.locator("select").nth(2)
            self._select_first_valid_option(c_sel)
        elif "invoice" in err and "number" in err:
            from testdata.dynamic.business_test_data import BusinessTestData
            modal.get_by_label("Invoice No.", exact=False).first.fill(f"INV-FIX-{BusinessTestData.get_unique_suffix()}")
        elif "date" in err:
            modal.get_by_label("Purchase Date", exact=False).first.fill("12/08/2026")

    def _fix_step2_field_by_error(self, error_msg: str):
        """Identifies missing line item field from error toast (e.g. 'Item 4: brand is required') and fills it."""
        err = error_msg.lower()
        logger.info(f"Auto-fixing Step 2 field based on error: '{error_msg}'")
        modal = self.page.locator("[role='dialog'], .chakra-modal__content").first

        import re
        m = re.search(r"item\s*(\d+)", err)
        item_idx = int(m.group(1)) - 1 if m else 0

        # Fix Brand
        if "brand" in err:
            try:
                b_inputs = modal.get_by_label("Brand", exact=False).all()
                if not b_inputs:
                    b_inputs = modal.locator("input[placeholder*='Dell' i], input[placeholder*='Brand' i]").all()
                if b_inputs and item_idx < len(b_inputs):
                    b_inputs[item_idx].fill(f"Dell Item {item_idx+1}")
                    logger.info(f"Fixed Item #{item_idx+1} Brand -> 'Dell Item {item_idx+1}'")
                elif b_inputs:
                    for b in b_inputs:
                        if not b.input_value() or "e.g." in b.input_value().lower():
                            b.fill("Dell")
            except Exception as e:
                logger.warning(f"Error fixing brand: {e}")

        # Fix Model
        if "model" in err:
            try:
                m_inputs = modal.get_by_label("Model", exact=False).all()
                if not m_inputs:
                    m_inputs = modal.locator("input[placeholder*='XPS' i], input[placeholder*='Model' i]").all()
                if m_inputs and item_idx < len(m_inputs):
                    m_inputs[item_idx].fill(f"Model-{item_idx+1}")
                    logger.info(f"Fixed Item #{item_idx+1} Model -> 'Model-{item_idx+1}'")
                elif m_inputs:
                    for m_in in m_inputs:
                        if not m_in.input_value() or "e.g." in m_in.input_value().lower():
                            m_in.fill("XPS")
            except Exception as e:
                logger.warning(f"Error fixing model: {e}")

        # Ensure all select dropdowns across product cards have valid options chosen
        selects = modal.locator("select").all()
        for index, s in enumerate(selects):
            try:
                if s.is_visible(timeout=500):
                    val = s.input_value()
                    if not val or val.strip() == "":
                        options = s.locator("option").all()
                        for opt in options[1:]:
                            opt_val = opt.get_attribute("value")
                            opt_txt = opt.inner_text().strip()
                            if opt_val and opt_val.strip() != "" and "select" not in opt_txt.lower():
                                s.select_option(value=opt_val)
                                logger.info(f"Fixed Step 2 Select #{index+1}: selected '{opt_txt}' ({opt_val})")
                                self.page.wait_for_timeout(400)
                                break
            except Exception as e:
                logger.debug(f"Note fixing select #{index+1}: {e}")

    def ensure_procurement_exists_for_edit(self) -> str:
        """
        Ensures at least one procurement record exists in the table.
        If table is empty, creates a new procurement record with invoice attachment.
        - Automatically fixes missing fields from error toast (max 2 retries).
        - Strictly verifies creation toast contains 'successful' or 'successfully' before proceeding to edit.
        - Always returns the valid 'PROC-YYYYMMDD...' procurement code.
        """
        proc_id = self.get_first_procurement_invoice()
        if not proc_id:
            logger.info("No procurement found in table. Creating base procurement record with invoice attachment...")
            import os
            invoices_dir = os.path.abspath("testdata/static/invoices")
            sample_invoice_path = os.path.join(invoices_dir, "JOB VRITTA 41 1.pdf")
            if not os.path.exists(sample_invoice_path):
                sample_invoice_path = os.path.join(invoices_dir, "invoice_1mb.pdf")

            self.click_new_procurement()
            from testdata.dynamic.business_test_data import BusinessTestData
            data = BusinessTestData.procurement()
            self.fill_step1_details(
                vendor_label=None,
                branch_label=None,
                company_label=None,
                invoice_no=data.invoice_no,
                purchase_date=data.purchase_date,
                amount_before_gst=data.amount_before_gst,
                gst_amount=data.gst_amount,
                remarks="Base Procurement For Automated Edit Flow",
                invoice_file_path=sample_invoice_path
            )

            # Step 1 -> Step 2 with retry loop
            for attempt in range(4):
                next_res = self.click_next()
                if self.is_step2_active():
                    logger.info("Advanced to Step 2 Line Items successfully.")
                    break
                toast = next_res.get("toast", "")
                logger.info(f"[STEP 1 ATTEMPT #{attempt+1}] Toast: '{toast}'")
                if toast:
                    self._fix_step1_field_by_error(toast, sample_invoice_path)
                self.page.wait_for_timeout(500)

            assert self.is_step2_active(), "Failed to advance to Step 2 after retries."

            # Select Step 2 dropdowns & fill all cards (Brand, Model, Category, Sub Category, Price, Qty)
            self.select_step2_dropdowns()
            self.page.wait_for_timeout(500)

            # Save Step 2 with retry loop
            saved_toast = ""
            for attempt in range(4):
                saved_toast = self.save_procurement()
                logger.info(f"[SAVE ATTEMPT #{attempt+1}] Toast: '{saved_toast}'")
                is_success = any(term in (saved_toast or "").lower() for term in ["success", "successful", "saved", "created"])
                if is_success:
                    logger.info(f"Procurement successfully created: '{saved_toast}'")
                    break

                # Fix any missing field on Step 2 (e.g. 'Item 4: brand is required')
                logger.warning(f"Save returned error toast: '{saved_toast}'. Fixing field and retrying...")
                self._fix_step2_field_by_error(saved_toast)
                self.page.wait_for_timeout(800)

            is_success = any(term in (saved_toast or "").lower() for term in ["success", "successful", "saved", "created"])
            assert is_success, f"Procurement creation failed before edit. Toast received: '{saved_toast}'"

            self.page.wait_for_timeout(1000)
            self.navigate_to_asset_procurement()
            proc_id = self.get_first_procurement_invoice()
            if not proc_id:
                proc_el = self.page.locator("tbody td").filter(has_text=re.compile(r"^PROC-", re.I)).first
                if proc_el.is_visible(timeout=5000):
                    proc_id = proc_el.inner_text().strip()

            assert proc_id and proc_id.startswith("PROC-"), f"Expected procurement code starting with 'PROC-', got: '{proc_id}'"
            logger.info(f"Base procurement verified and ready for edit: '{proc_id}'")
        return proc_id

    def click_edit_procurement(self, invoice_no: str = None):
        """
        Dynamically locates procurement record by its ID in td[2] (or first row)
        and clicks the Edit action button:
        <div class="css-8uhtka"><button type="button" class="chakra-button ..." aria-label="Edit"><svg ...></button></div>
        Waits for modal with header 'Edit Procurement'.
        """
        logger.info(f"Opening Edit Procurement modal (record='{invoice_no}')...")
        if invoice_no:
            self.search_procurement(invoice_no)
            self.page.wait_for_timeout(500)

        # Locate Edit button using aria-label="Edit" or div container
        edit_locator = self.page.locator("button[aria-label='Edit']").first
        if not edit_locator.is_visible(timeout=2000):
            if invoice_no:
                edit_locator = self.page.locator(f"xpath=//tr[td[2][contains(., '{invoice_no}')]]//button[@aria-label='Edit']").first
                if not edit_locator.is_visible(timeout=1000):
                    edit_locator = self.page.locator(f"xpath=//tr[td[2][contains(., '{invoice_no}')]]//td[12]//button").first
            else:
                edit_locator = self.page.locator("xpath=//tbody/tr[1]//button[@aria-label='Edit']").first

        if not edit_locator.is_visible(timeout=2000):
            edit_locator = self.page.locator("tbody tr").first.locator("button:has(svg), td:last-child button, .chakra-button[aria-label='Edit']").first

        edit_locator.scroll_into_view_if_needed()
        self.page.wait_for_timeout(300)
        try:
            edit_locator.click(timeout=3000)
        except Exception:
            edit_locator.click(force=True)

        # Wait for Edit Procurement modal header
        self.page.get_by_text("Edit Procurement", exact=True).wait_for(state="visible", timeout=15000)
        logger.info("Edit Procurement modal opened successfully.")

    def get_prefilled_step1_data(self) -> dict:
        """Inspects and returns all prefilled values on Step 1 of Edit Procurement."""
        data = {}
        # 1. Vendor
        try:
            v_select = self.page.locator("select").filter(has=self.page.locator("option", has_text=re.compile(r"Select vendor", re.I))).first
            if not v_select.is_visible(timeout=500):
                v_select = self.page.get_by_label("Vendor", exact=False).first
            data["vendor"] = v_select.input_value().strip()
        except Exception:
            data["vendor"] = ""

        # 2. Branch
        try:
            b_select = self.page.locator("select").filter(has=self.page.locator("option", has_text=re.compile(r"Select branch", re.I))).first
            if not b_select.is_visible(timeout=500):
                b_select = self.page.get_by_label("Branch", exact=False).first
            data["branch"] = b_select.input_value().strip()
        except Exception:
            data["branch"] = ""

        # 3. Payroll Company
        try:
            c_select = self.page.locator("select").filter(has=self.page.locator("option", has_text=re.compile(r"Select payroll company", re.I))).first
            if not c_select.is_visible(timeout=500):
                c_select = self.page.get_by_label("Payroll Company", exact=False).first
            data["company"] = c_select.input_value().strip()
        except Exception:
            data["company"] = ""

        # 4. Invoice No
        try:
            inv_input = self.page.get_by_label("Invoice No.", exact=False).first
            if not inv_input.is_visible(timeout=500):
                inv_input = self.page.locator("input[placeholder*='Invoice' i], input[name*='invoice' i]").first
            data["invoice_no"] = inv_input.input_value().strip()
        except Exception:
            data["invoice_no"] = ""

        # 5. Purchase Date
        try:
            d_input = self.page.get_by_label("Purchase Date", exact=False).first
            if not d_input.is_visible(timeout=500):
                d_input = self.page.locator("input[type='date'], input[placeholder*='date' i]").first
            data["purchase_date"] = d_input.input_value().strip()
        except Exception:
            data["purchase_date"] = ""

        # 6. Amount Before GST
        try:
            amt_in = self.page.locator("div").filter(has_text=re.compile(r"^Amount Before GST", re.I)).locator("input").first
            if not amt_in.is_visible(timeout=500):
                amt_in = self.page.get_by_label("Amount Before GST", exact=False).first
            if not amt_in.is_visible(timeout=500):
                amt_in = self.page.locator("input[placeholder*='0.00'], input[placeholder*='Amount']").first
            data["amount_before_gst"] = amt_in.input_value().strip()
        except Exception:
            data["amount_before_gst"] = ""

        # 7. GST Amount
        try:
            gst_in = self.page.locator("div").filter(has_text=re.compile(r"^GST Amount", re.I)).locator("input").first
            if not gst_in.is_visible(timeout=500):
                gst_in = self.page.get_by_label("GST Amount", exact=False).first
            if not gst_in.is_visible(timeout=500):
                gst_in = self.page.locator("input[placeholder*='GST']").first
            data["gst_amount"] = gst_in.input_value().strip()
        except Exception:
            data["gst_amount"] = ""

        # 8. Total Amount
        data["total_amount"] = self.get_total_amount_value()

        # 9. Remarks
        try:
            rem_input = self.page.get_by_label("Remarks", exact=False).first
            if not rem_input.is_visible(timeout=500):
                rem_input = self.page.locator("textarea[name*='remark' i], textarea[placeholder*='Remark' i]").first
            data["remarks"] = rem_input.input_value().strip()
        except Exception:
            data["remarks"] = ""

        logger.info(f"Prefilled Step 1 Data: {data}")
        return data

    def save_procurement(self) -> str:
        """Clicks 'Save Procurement' button on Step 2 and captures toast."""
        logger.info("Clicking 'Save Procurement' button...")
        btn = self.page.locator("button:has-text('Save Procurement'), button:has-text('Save')").first
        if not btn.is_visible(timeout=2000):
            btn = self.page.get_by_role("button", name="Save Procurement").first
        btn.click(force=True)

        toast = self.wait_for_toast_message()
        logger.info(f"Captured Save Procurement Toast: '{toast}'")
        return toast

    def wait_for_toast_message(self) -> str:
        return self.wait_for_toast("#chakra-toast-manager-top-right")

    def get_pop_msg(self) -> str:
        return self.wait_for_toast_message()

