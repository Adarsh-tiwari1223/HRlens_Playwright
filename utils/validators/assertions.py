from playwright.sync_api import Page, expect


def assert_visible(page: Page, locator: str):
    expect(page.locator(locator)).to_be_visible()


def assert_text(page: Page, locator: str, text: str):
    expect(page.locator(locator)).to_have_text(text)


def assert_url(page: Page, url: str):
    expect(page).to_have_url(url)


def assert_url_contains(page: Page, partial: str):
    expect(page).to_have_url(partial)
