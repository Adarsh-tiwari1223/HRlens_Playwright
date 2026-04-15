from pages.base_page import BasePage


class NegotiationPage(BasePage):
    # Locators
    NEGOTIATION_TAB = "text=Negotiation"
    ACCEPT_BTN = "button:has-text('Accept')"
    REJECT_BTN = "button:has-text('Reject')"
    COUNTER_OFFER_INPUT = "[data-testid='counter-offer']"
    SUBMIT_BTN = "button:has-text('Submit')"
    SUCCESS_TOAST = "text=Negotiation Submitted"

    def navigate_to_negotiation(self):
        self.click(self.NEGOTIATION_TAB)

    def accept_offer(self):
        self.click(self.ACCEPT_BTN)

    def reject_offer(self):
        self.click(self.REJECT_BTN)

    def enter_counter_offer(self, amount: str):
        self.fill(self.COUNTER_OFFER_INPUT, amount)

    def submit(self):
        self.click(self.SUBMIT_BTN)

    def is_success_visible(self) -> bool:
        return self.is_visible(self.SUCCESS_TOAST)
