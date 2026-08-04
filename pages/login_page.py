import logging
from pages.base_page import BasePage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)


class LoginPage(BasePage):

    def _fill_email(self, email: str):
        self.page.get_by_label("Email").fill(email)

    def _fill_password(self, password: str):
        self.page.get_by_label("Password").fill(password)

    def login(self, email: str, password: str):
        logger.info(f"[UI] Log In As               : {email}")
        try:
            self.page.wait_for_selector("input, label:has-text('Email')", timeout=15000)
        except Exception:
            pass
        self._fill_email(email)
        self._fill_password(password)
        self.page.get_by_role("button", name="Login").click()
        try:
            self.page.wait_for_url(lambda url: "/login" not in url, timeout=12000)
            self.page.wait_for_load_state("domcontentloaded")
        except Exception:
            self.page.wait_for_timeout(1500)
        logger.info(f"[UI] Logged In As            : {email}")





    def click_login(self):
        self.page.get_by_role("button", name="Login").click()

    def click_forgot_password(self):
        self.page.get_by_text("Forgot Password?").click()

    def click_send_otp(self):
        self.page.get_by_role("button", name="Send OTP").click()

    def is_email_required_visible(self) -> bool:
        return self.page.get_by_text("Email is required").is_visible()

    def is_password_required_visible(self) -> bool:
        return self.page.get_by_text("Password is required").is_visible()

    def is_invalid_creds_visible(self) -> bool:
        import re
        self.page.wait_for_timeout(2000)
        try:
            # First check standard Chakra toast containers
            toast_loc = self.page.locator("#chakra-toast-manager-top-right, .chakra-toast, [role='status'], [role='alert'], .chakra-alert").first
            if toast_loc.is_visible(timeout=2000):
                txt = toast_loc.inner_text().strip()
                logger.info(f"Discovered authentication error toast: '{txt}'")
                return True
        except Exception:
            pass

        # Check all visible text elements for authentication error keywords
        try:
            elements = self.page.locator("p, div, span, label, [role='alert']").all()
            for el in elements:
                try:
                    if el.is_visible():
                        t = el.inner_text().strip()
                        if t and len(t) < 150 and any(k in t.lower() for k in ["invalid", "incorrect", "failed", "unauthorized", "wrong", "error", "not match"]):
                            logger.info(f"Discovered authentication error element text: '{t}'")
                            return True
                except Exception:
                    pass
        except Exception:
            pass

        return False

    def is_otp_email_required_visible(self) -> bool:
        return self.page.get_by_text("Please enter your email", exact=True).is_visible()

    def is_login_success_visible(self) -> bool:
        try:
            expect(self.page.get_by_text("Loggedin Successfully")).to_be_visible()
            return True
        except:
            return False


