import os
import time
from playwright.sync_api import sync_playwright
from core.config import settings
from pages.login_page import LoginPage
from pages.increment.increment_page import IncrementPage

def inspect_dropdowns():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto(settings.BASE_URL)
        creds = settings.USERS["vivek"]
        login_page = LoginPage(page)
        login_page.login(creds["username"], creds["password"])
        page.wait_for_url("**/dashboard")
        
        increment_page = IncrementPage(page)
        increment_page.go_to_increment()
        page.wait_for_timeout(2000)
        
        # Get all companies
        companies = page.locator("select").nth(0).locator("option").all_inner_texts()
        print("Companies:", companies)
        
        for company in companies:
            if company == "Select Company":
                continue
                
            print(f"\\n--- Selecting company: {company} ---")
            page.locator("select").nth(0).select_option(label=company)
            
            # Wait a bit for API call
            page.wait_for_timeout(2000)
            
            branch_html = page.evaluate('document.querySelectorAll("select")[1].innerHTML')
            print(f"Branches for {company}: {branch_html}")
            
            # If branches exist, select the first valid one
            branches = page.locator("select").nth(1).locator("option").all_inner_texts()
            valid_branches = [b for b in branches if b != "Select Branch"]
            if valid_branches:
                branch = valid_branches[0]
                print(f"Selecting branch {branch}")
                page.locator("select").nth(1).select_option(label=branch)
                page.wait_for_timeout(2000)
                dept_html = page.evaluate('document.querySelectorAll("select")[2].innerHTML')
                print(f"Departments for {branch}: {dept_html}")
                
        browser.close()

if __name__ == "__main__":
    inspect_dropdowns()
