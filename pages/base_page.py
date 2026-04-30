from playwright.sync_api import Page


class BasePage:
    def __init__(self, page: Page):
        self.page = page

    def navigate(self, url: str):
        self.page.goto(url)

    def click(self, locator: str):
        self.page.locator(locator).wait_for(state="visible")
        self.page.locator(locator).click()

    def fill(self, locator: str, value: str):
        self.page.locator(locator).wait_for(state="visible")
        self.page.locator(locator).fill(value)

    def get_text(self, locator: str) -> str:
        self.page.locator(locator).wait_for(state="visible")
        return self.page.locator(locator).inner_text()

    def get_all_texts(self, locator: str) -> list[str]:
        return self.page.locator(locator).all_inner_texts()

    def is_visible(self, locator: str) -> bool:
        return self.page.locator(locator).is_visible()

    def is_enabled(self, locator: str) -> bool:
        return self.page.locator(locator).is_enabled()

    def select_option(self, locator: str, value: str):
        self.page.locator(locator).wait_for(state="visible")
        self.page.locator(locator).select_option(value)

    def wait_for_url(self, partial: str, timeout: int = 10000):
        self.page.wait_for_url(f"**{partial}**", timeout=timeout)

    def wait_for_toast(self, locator: str, timeout: int = 5000) -> str:
        self.page.locator(locator).wait_for(state="visible", timeout=timeout)
        return self.page.locator(locator).inner_text()

    def wait_for_hidden(self, locator: str, timeout: int = 10000):
        self.page.locator(locator).wait_for(state="hidden", timeout=timeout)

    def get_count(self, locator: str) -> int:
        return self.page.locator(locator).count()

    def upload_file(self, locator: str, file_path: str):
        self.page.locator(locator).set_input_files(file_path)

    def scroll_into_view(self, locator: str):
        self.page.locator(locator).scroll_into_view_if_needed()

    def reload(self):
        self.page.reload()

