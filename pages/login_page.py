from pages.base_page import BasePage
from playwright.sync_api import expect


class LoginPage(BasePage):

    def _fill_email(self, email: str):
        self.page.get_by_label("Email").fill(email)

    def _fill_password(self, password: str):
        self.page.get_by_label("Password").fill(password)

    def login(self, email: str, password: str):
        self._fill_email(email)
        self._fill_password(password)
        self.page.get_by_role("button", name="Login").click()

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
        try:
            expect(self.page.get_by_text("Email or password is incorrect").first).to_be_visible()
            return True
        except:
            return False

    def is_otp_email_required_visible(self) -> bool:
        return self.page.get_by_text("Please enter your email", exact=True).is_visible()

    def is_login_success_visible(self) -> bool:
        try:
            expect(self.page.get_by_text("Loggedin Successfully")).to_be_visible()
            return True
        except:
            return False
