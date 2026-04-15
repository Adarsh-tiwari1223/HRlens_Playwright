from pages.base_page import BasePage


class LoginPage(BasePage):
 # ----------------------Locators---------------------------------------
    EMAIL = "input[name='email']"
    PASSWORD = "input[name='password']"
    LOGIN_BTN = "button:has-text('Login')"
    FORGOT_PASSWORD = "text=Forgot Password?"
    SEND_OTP_BTN = "button:has-text('Send OTP')"
#----------------------Error messages---------------------------------------
    EMAIL_REQUIRED = "text=Email is required"
    PASSWORD_REQUIRED = "text=Password is required"
    INVALID_CREDS = "text=Email or password is incorrect"
    OTP_EMAIL_REQUIRED = "text=Please enter your email"
 
 #---------------------------------Actions------------------------------------
    def login(self, email: str, password: str):
        self.fill(self.EMAIL, email)
        self.fill(self.PASSWORD, password)
        self.click(self.LOGIN_BTN)

    def click_login(self):
        self.click(self.LOGIN_BTN)

    def click_forgot_password(self):
        self.click(self.FORGOT_PASSWORD)

    def click_send_otp(self):
        self.click(self.SEND_OTP_BTN)
