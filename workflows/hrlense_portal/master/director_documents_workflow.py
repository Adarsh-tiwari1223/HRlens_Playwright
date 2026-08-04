"""
Director Documents Module Workflow Layer for HR Lens Portal (Under Masters).
Follows 3-Tier Architecture (Page Object -> Workflow Layer -> Test Suite).
Implements Business Rule BR-001 (Director Data Consistency Validation):
Every Director displayed in /directors table must also appear in the Director dropdown of the Add Document modal.
"""

from playwright.sync_api import Page
from pages.hrlense_portal.master.director_page import DirectorPage
from pages.hrlense_portal.master.director_documents_page import DirectorDocumentsPage
from utils.logger import log_step, log_debug


class DirectorDocumentsWorkflow:
    def __init__(self, page: Page):
        self.page = page
        self.director_page = DirectorPage(page)
        self.docs_page = DirectorDocumentsPage(page)

    def refresh_page(self):
        """Reloads page to ensure UI state is clean."""
        try:
            self.page.reload()
            self.page.wait_for_load_state("domcontentloaded")
            self.page.wait_for_timeout(300)
        except Exception:
            pass

    def get_all_table_directors(self) -> list[str]:
        """Reads every Director name from the /directors table."""
        log_step("Read All Directors from Table Grid")
        self.director_page.navigate_to_directors()
        return self.director_page.get_existing_director_names()

    def get_all_dropdown_directors(self) -> list[str]:
        """Reads every Director option from the Add Document modal dropdown."""
        log_step("Read All Directors from Add Document Dropdown")
        self.docs_page.navigate_to_director_documents()
        self.docs_page.click_add_document()
        options = self.docs_page.get_available_director_options()
        self.docs_page.click_cancel()
        self.refresh_page()
        return options

    def validate_director_data_consistency(self) -> dict:
        """
        Phase 1: Director Data Consistency Validation (BR-001)
        - Reads table_directors from /directors.
        - Reads dropdown_directors from Add Document modal.
        - Validates every Director in table_directors exists in dropdown_directors.
        """
        log_step("Phase 1: Director Data Consistency Validation")
        table_directors = self.get_all_table_directors()
        dropdown_directors = self.get_all_dropdown_directors()

        # Normalize whitespace and lower case for strict subset comparison
        clean_table = {" ".join(d.split()).strip().upper() for d in table_directors if d.strip()}
        clean_dropdown = {" ".join(d.split()).strip().upper() for d in dropdown_directors if d.strip()}

        missing = clean_table - clean_dropdown

        return {
            "table_directors": list(table_directors),
            "dropdown_directors": list(dropdown_directors),
            "clean_table": clean_table,
            "clean_dropdown": clean_dropdown,
            "missing_directors": list(missing),
            "is_valid": len(missing) == 0 if clean_table else True
        }

    def get_valid_director_and_doc_type_pair(self) -> tuple[str | None, str | None]:
        """
        Document Creation Rule:
        Selects a Director from table_directors and a Document Type (PAN, Aadhaar, Passport)
        that does NOT already exist for that Director in the Director Documents grid.
        Returns (director_name, doc_type) or (None, None) if no valid pair exists.
        """
        log_step("Find Valid Director + Document Type Pair")
        table_directors = self.get_all_table_directors()
        if not table_directors:
            return None, None

        self.docs_page.navigate_to_director_documents()
        doc_types = ["PAN", "AADHAAR", "PASSPORT"]

        for director_name in table_directors:
            existing = self.docs_page.get_existing_document_types_for_director(director_name)
            for dt in doc_types:
                if dt not in existing:
                    log_debug(f"Found valid pair: Director='{director_name}', DocType='{dt}'")
                    return director_name, dt

        return None, None

    def add_director_document_workflow(self, director_name: str, doc_type: str, doc_number: str, file_path: str = None) -> str:
        """Executes document creation for selected Director and Document Type."""
        log_step("Document Creation Workflow", value=f"{director_name} | {doc_type}")
        self.docs_page.navigate_to_director_documents()
        self.docs_page.click_add_document()

        self.docs_page.fill_document_form(
            director_name=director_name,
            doc_type=doc_type,
            doc_number=doc_number,
            file_path=file_path
        )

        self.docs_page.click_save_document()
        toast = self.docs_page.wait_for_toast_message()
        log_step("Document Toast Notification", value=toast)

        self.refresh_page()
        return toast

    def verify_document_exists(self, doc_number: str) -> bool:
        """Verifies target document record is visible in Director Documents repository grid."""
        log_step("Verify Document Grid", value=doc_number)
        self.docs_page.navigate_to_director_documents()
        self.docs_page.filter_by_director("")
        self.page.wait_for_timeout(300)
        try:
            row = self.page.locator("tbody tr").filter(has_text=doc_number).first
            row.wait_for(state="visible", timeout=6000)
            return row.is_visible()
        except Exception:
            return False
