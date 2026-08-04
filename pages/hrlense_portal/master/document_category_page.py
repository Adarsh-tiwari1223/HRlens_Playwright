"""
Document Category Master Page Object (HR Lens Portal).
Handles CRUD management for Document Categories (Company Document, Director Document, Employee Document).
URL Route: /master/documentCategory
"""

import logging
from pages.base_page import BasePage
from core.config import settings

logger = logging.getLogger(__name__)


class DocumentCategoryPage(BasePage):
    # Route URL
    ROUTE_URL = f"{settings.BASE_URL}/master/documentCategory"

    TOAST = (
        "[role='region'][aria-live='polite'] [role='status'], "
        "[role='region'][aria-live='polite'] [role='alert'], "
        ".chakra-toast, .chakra-toast__title, div[id^='toast-']"
    )

    def navigate_to_document_category_master(self):
        """Navigates to Document Category Master page (Admin Only)."""
        logger.info(f"Navigating to Document Category Master: {self.ROUTE_URL}")
        if "/master/documentCategory" not in self.page.url:
            self.page.goto(self.ROUTE_URL, timeout=60000)
            self.page.wait_for_load_state("domcontentloaded")

    def is_access_denied_visible(self) -> bool:
        """Checks if non-admin user is restricted from performing Master admin actions."""
        try:
            denied_msg = self.page.locator("text=Access Denied, text=Unauthorized, text=403, .chakra-alert").first
            if denied_msg.is_visible():
                return True
            if "/master/" not in self.page.url or "/login" in self.page.url:
                return True
            add_btn = self.page.locator("button:has-text('Add Category'), button:has-text('Add')").first
            return not add_btn.is_visible()
        except Exception:
            return False

    def select_director_document_tab(self):
        """Selects the Director Document category tab."""
        logger.info("Selecting 'Director Document' master tab...")
        tab = self.page.locator("button:has-text('Director Document'), [role='tab']:has-text('Director Document')").first
        if tab.is_visible():
            tab.click()
            self.page.wait_for_timeout(300)

    def get_existing_director_document_categories(self) -> list[str]:
        """Reads all configured Director Document Categories from master table grid."""
        self.navigate_to_document_category_master()
        self.select_director_document_tab()
        results = []
        try:
            self.page.locator("tbody tr").first.wait_for(state="visible", timeout=6000)
            rows = self.page.locator("tbody tr").all()
            for r in rows:
                txt = r.inner_text().strip()
                if txt:
                    category_name = txt.splitlines()[0].strip()
                    results.append(category_name)
        except Exception:
            pass
        return results

    def add_director_document_category(self, category_name: str) -> str | None:
        """Adds a new Director Document Category in Master."""
        logger.info(f"Adding new Director Document Category: '{category_name}'")
        self.navigate_to_document_category_master()
        self.select_director_document_tab()

        add_btn = self.page.locator("button:has-text('Add Category'), button:has-text('Add')").first
        if add_btn.is_visible():
            add_btn.click()
            self.page.wait_for_timeout(300)

        input_elem = self.page.locator(".chakra-modal__content input[type='text'], input[placeholder*='Category']").first
        if input_elem.is_visible():
            input_elem.fill(category_name)

        save_btn = self.page.locator(".chakra-modal__content button[type='submit'], [role='dialog'] button:has-text('Save')").first
        if save_btn.is_visible():
            save_btn.click(force=True)

        return self.wait_for_toast(self.TOAST)

    def select_kyc_document_category_tab(self):
        """Selects the KYC Document Category master tab."""
        logger.info("Selecting 'KYC Document Category' master tab...")
        tab = self.page.locator("button:has-text('KYC Document Category'), [role='tab']:has-text('KYC Document Category'), button:has-text('KYC')").first
        if tab.is_visible():
            tab.click()
            self.page.wait_for_timeout(300)

    def add_kyc_document_category(self, category_name: str) -> str | None:
        """Adds a new KYC Document Category in Master (S.No 6)."""
        logger.info(f"Adding new KYC Document Category: '{category_name}'")
        self.navigate_to_document_category_master()
        self.select_kyc_document_category_tab()

        add_btn = self.page.locator("button:has-text('Add Category'), button:has-text('Add Document Category'), button:has-text('Add')").first
        if add_btn.is_visible():
            add_btn.click()
            self.page.wait_for_timeout(300)

        input_elem = self.page.locator(".chakra-modal__content input[type='text'], input[placeholder*='Category']").first
        if input_elem.is_visible():
            input_elem.fill(category_name)

        save_btn = self.page.locator(".chakra-modal__content button[type='submit'], [role='dialog'] button:has-text('Save')").first
        if save_btn.is_visible():
            save_btn.click(force=True)

        return self.wait_for_toast(self.TOAST)

    def get_existing_kyc_document_categories(self) -> list[str]:
        """Reads all configured KYC Document Categories from master table grid."""
        self.navigate_to_document_category_master()
        self.select_kyc_document_category_tab()
        results = []
        try:
            self.page.locator("tbody tr").first.wait_for(state="visible", timeout=6000)
            rows = self.page.locator("tbody tr").all()
            for r in rows:
                txt = r.inner_text().strip()
                if txt:
                    category_name = txt.splitlines()[0].strip()
                    results.append(category_name)
        except Exception:
            pass
        return results
