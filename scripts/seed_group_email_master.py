"""
HRlens Portal — Group Email Master Seeder Script.
Target: https://stg-hrlense.jobvritta.com/master/group-email
API: https://audit.jobvritta.com/api/Group_Mail_Master

Seeds group email configurations for:
1. Company (mail_Group_Type = 1)
2. Branch (mail_Group_Type = 2)
3. Branch + Department (mail_Group_Type = 5)
4. Branch Group (mail_Group_Type = 8)
5. Branch Group + Department (mail_Group_Type = 9)
6. Global (mail_Group_Type = 10)

Enforces:
- Unique email per record across all non-global groups (backend 400 constraint)
- Idempotency (detects existing entity configurations and skips safely)
- Clean slugified naming convention: group.<scope>.<slug>.<ids>@jobvritta.com
"""

import os
import re
import sys
import time
import logging
import argparse
import requests
from typing import Dict, List, Set, Tuple, Any

# Framework configuration
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def clean_entity_slug(text: str) -> str:
    """Converts display text into a clean alphanumeric email-safe slug without legal suffixes."""
    if not text:
        return "company"
    s = text.lower().strip()
    s = re.sub(r'\b(inc|llc|pvt|ltd|solutions|technologies|global|services|branch)\b', '', s)
    s = re.sub(r'[^a-z0-9]+', '', s)
    return s[:20] or "comp"


def slugify(text: str) -> str:
    """Legacy slugify preserved for compatibility."""
    return clean_entity_slug(text)


class GroupEmailSeeder:
    def __init__(self, api_base_url: str = settings.API_BASE_URL):
        self.api_base_url = api_base_url
        self.headers = self._get_auth_headers()
        self.existing_emails: Set[str] = set()
        self.existing_mappings: Set[Tuple[int, Any, Any, Any, Any]] = set()
        self.records_data: List[Dict[str, Any]] = []

    def _get_auth_headers(self) -> Dict[str, str]:
        """Authenticates as Admin and extracts Bearer JWT token."""
        login_url = f"{self.api_base_url}/user/login"
        creds = settings.USERS["admin"]
        logger.info(f"Authenticating as admin to {login_url}...")
        resp = requests.post(
            login_url,
            json={"email": creds["username"], "user": creds["username"], "password": creds["password"]},
            timeout=20
        )
        resp.raise_for_status()
        token = resp.json().get("token", "")
        if not token:
            raise RuntimeError("Admin authentication succeeded but no JWT token was returned.")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def load_existing_records(self) -> None:
        """Fetches existing records to ensure idempotency and prevent duplicate email conflicts."""
        url = f"{self.api_base_url}/Group_Mail_Master?first=0&rows=5000"
        for attempt in range(1, 4):
            try:
                resp = requests.get(url, headers=self.headers, timeout=20)
                if resp.status_code == 200:
                    self.records_data = resp.json().get("data", [])
                    break
                elif attempt < 3:
                    time.sleep(2)
                    continue
                else:
                    resp.raise_for_status()
            except Exception as e:
                if attempt < 3:
                    time.sleep(2)
                    continue
                raise e
        
        self.existing_emails.clear()
        self.existing_mappings.clear()
        for item in self.records_data:
            mgt = item.get("mail_Group_Type")
            email = (item.get("email_Id") or "").strip().lower()
            if email:
                if mgt == 10:
                    # Global can have multiple comma-separated emails
                    for e in re.split(r'[,;\s]+', email):
                        if e:
                            self.existing_emails.add(e.strip().lower())
                else:
                    self.existing_emails.add(email)

            cid = item.get("company_Id")
            bid = item.get("branch_Id")
            bgid = item.get("branch_Group_Id")
            did = item.get("department_Id")
            self.existing_mappings.add((mgt, cid, bid, bgid, did))

        logger.info(f"Loaded {len(self.records_data)} existing Group Email records.")

    def _generate_unique_email(self, prefix: str, domain: str = "tekinspirations.com", fallback_prefix: str = None) -> str:
        """Generates a guaranteed unique email following {prefix}@{domain} format."""
        base_email = f"{prefix}@{domain}".lower()
        if base_email not in self.existing_emails:
            self.existing_emails.add(base_email)
            return base_email

        if fallback_prefix:
            fallback_email = f"{fallback_prefix}@{domain}".lower()
            if fallback_email not in self.existing_emails:
                self.existing_emails.add(fallback_email)
                return fallback_email

        counter = 2
        while True:
            candidate = f"{prefix}{counter}@{domain}".lower()
            if candidate not in self.existing_emails:
                self.existing_emails.add(candidate)
                return candidate
            counter += 1

    def create_group_email_record(self, payload: Dict[str, Any], description: str) -> bool:
        """Sends POST request to create group email record with retry and gentle throttling."""
        url = f"{self.api_base_url}/Group_Mail_Master"
        for attempt in range(1, 4):
            try:
                resp = requests.post(url, json=payload, headers=self.headers, timeout=20)
                if resp.status_code in (200, 201):
                    logger.info(f"[CREATED] {description} -> {payload['email_Id']}")
                    time.sleep(0.2)
                    return True
                elif resp.status_code in (500, 502, 503, 504) and attempt < 3:
                    logger.warning(f"[RETRY {attempt}/3] Server {resp.status_code} on {description}, backing off 2s...")
                    time.sleep(2)
                    continue
                else:
                    logger.warning(f"[FAILED] {description}: {resp.status_code} - {resp.text}")
                    return False
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt < 3:
                    logger.warning(f"[RETRY {attempt}/3] Connection error on {description}: {e}, backing off 2s...")
                    time.sleep(2)
                    continue
                logger.error(f"[ERROR] {description}: {e}")
                return False
            except Exception as e:
                logger.error(f"[ERROR] {description}: {e}")
                return False
        return False

    def seed_companies(self, limit: int = 50) -> int:
        """Seeds Group Emails for Companies (Type 1)."""
        url = f"{self.api_base_url}/DropDown/permissionWiseCompany"
        companies = requests.get(url, headers=self.headers, timeout=20).json()
        logger.info(f"Discovered {len(companies)} Companies.")

        created = 0
        for comp in companies[:limit]:
            cid = comp.get("company_ID")
            name = comp.get("company_Name") or "Company"
            mapping_key = (1, cid, None, None, None)
            if mapping_key in self.existing_mappings:
                logger.debug(f"[SKIP] Company '{name}' (ID: {cid}) already has group email.")
                continue

            c_slug = clean_entity_slug(name)
            # Format: {company}1@{company}.com
            email = self._generate_unique_email(f"{c_slug}1", domain=f"{c_slug}.com")
            payload = {
                "id": 0,
                "mail_Group_Type": 1,
                "email_Id": email,
                "company_Id": cid,
                "branch_Id": None,
                "branch_Group_Id": None,
                "department_Id": None,
                "isActive": True
            }
            if self.create_group_email_record(payload, f"Company: '{name}' (ID: {cid})"):
                self.existing_mappings.add(mapping_key)
                created += 1

        return created

    def seed_branches(self, limit: int = 50) -> int:
        """Seeds Group Emails for Branches (Type 2)."""
        c_url = f"{self.api_base_url}/DropDown/permissionWiseCompany"
        companies = requests.get(c_url, headers=self.headers, timeout=20).json()
        company_map = {c.get("company_ID"): c.get("company_Name") for c in companies}

        url = f"{self.api_base_url}/DropDown/branchWithCompany"
        branches = requests.get(url, headers=self.headers, timeout=20).json()
        logger.info(f"Discovered {len(branches)} Branches.")

        created = 0
        for br in branches[:limit]:
            bid = br.get("branchId")
            cid = br.get("company_ID")
            name = br.get("branchName") or "Branch"
            mapping_key = (2, cid, bid, None, None)
            if mapping_key in self.existing_mappings:
                logger.debug(f"[SKIP] Branch '{name}' (ID: {bid}) already has group email.")
                continue

            c_name = company_map.get(cid) or "company"
            clean_b_name = re.sub(r'\(.*?\)', '', name).strip() or name
            c_slug = clean_entity_slug(c_name)
            b_slug = clean_entity_slug(clean_b_name)
            # Format: {company}.{branch}@{company}.com
            email = self._generate_unique_email(f"{c_slug}.{b_slug}", domain=f"{c_slug}.com")
            payload = {
                "id": 0,
                "mail_Group_Type": 2,
                "email_Id": email,
                "company_Id": cid,
                "branch_Id": bid,
                "branch_Group_Id": None,
                "department_Id": None,
                "isActive": True
            }
            if self.create_group_email_record(payload, f"Branch: '{clean_b_name}' ({c_name}) (ID: {bid})"):
                self.existing_mappings.add(mapping_key)
                created += 1

        return created

    def seed_branch_groups(self, limit: int = 50) -> int:
        """Seeds Group Emails for Branch Groups (Type 8)."""
        url = f"{self.api_base_url}/Hrlense_Branch/branch-group"
        branch_groups = requests.get(url, headers=self.headers, timeout=20).json()
        logger.info(f"Discovered {len(branch_groups)} Branch Groups.")

        created = 0
        for bg in branch_groups[:limit]:
            bgid = bg.get("id")
            name = bg.get("group_Name") or "BranchGroup"
            mapping_key = (8, None, None, bgid, None)
            if mapping_key in self.existing_mappings:
                logger.debug(f"[SKIP] Branch Group '{name}' (ID: {bgid}) already has group email.")
                continue

            slug = clean_entity_slug(name)
            email = self._generate_unique_email(f"{slug}1", domain=f"{slug}.com")
            payload = {
                "id": 0,
                "mail_Group_Type": 8,
                "email_Id": email,
                "company_Id": None,
                "branch_Id": None,
                "branch_Group_Id": bgid,
                "department_Id": None,
                "isActive": True
            }
            if self.create_group_email_record(payload, f"Branch Group: '{name}' (ID: {bgid})"):
                self.existing_mappings.add(mapping_key)
                created += 1

        return created

    def seed_branch_departments(self, branch_limit: int = 15, dept_limit: int = 8) -> int:
        """Seeds Group Emails for Branch + Department combinations (Type 5)."""
        c_url = f"{self.api_base_url}/DropDown/permissionWiseCompany"
        companies = requests.get(c_url, headers=self.headers, timeout=20).json()
        company_map = {c.get("company_ID"): c.get("company_Name") for c in companies}

        b_url = f"{self.api_base_url}/DropDown/branchWithCompany"
        d_url = f"{self.api_base_url}/DropDown/department"
        branches = requests.get(b_url, headers=self.headers, timeout=20).json()[:branch_limit]
        departments = requests.get(d_url, headers=self.headers, timeout=20).json()[:dept_limit]

        logger.info(f"Seeding Branch + Department across {len(branches)} branches and {len(departments)} departments...")
        created = 0
        for br in branches:
            bid = br.get("branchId")
            cid = br.get("company_ID")
            b_name = br.get("branchName") or f"b{bid}"
            for dp in departments:
                did = dp.get("id")
                d_name = dp.get("departmentName") or f"d{did}"
                mapping_key = (5, None, bid, None, did)
                if mapping_key in self.existing_mappings:
                    continue

                c_name = company_map.get(cid) or "company"
                clean_b_name = re.sub(r'\(.*?\)', '', b_name).strip() or b_name
                c_slug = clean_entity_slug(c_name)
                d_slug = clean_entity_slug(d_name)
                b_slug = clean_entity_slug(clean_b_name)
                # Format: {company}.{dept}@{company}.com (with fallback if same company has multiple branches for dept)
                email = self._generate_unique_email(
                    f"{c_slug}.{d_slug}",
                    domain=f"{c_slug}.com",
                    fallback_prefix=f"{c_slug}.{b_slug}.{d_slug}"
                )
                payload = {
                    "id": 0,
                    "mail_Group_Type": 5,
                    "email_Id": email,
                    "company_Id": None,
                    "branch_Id": bid,
                    "branch_Group_Id": None,
                    "department_Id": did,
                    "isActive": True
                }
                desc = f"Branch+Dept: '{clean_b_name}' ({c_name}) x '{d_name}'"
                if self.create_group_email_record(payload, desc):
                    self.existing_mappings.add(mapping_key)
                    created += 1

        return created

    def seed_branch_group_departments(self, bg_limit: int = 50, dept_limit: int = 50) -> int:
        """Seeds Group Emails for Branch Group + Department combinations (Type 9)."""
        bg_url = f"{self.api_base_url}/Hrlense_Branch/branch-group"
        d_url = f"{self.api_base_url}/DropDown/department"
        b_groups = requests.get(bg_url, headers=self.headers, timeout=20).json()[:bg_limit]
        departments = requests.get(d_url, headers=self.headers, timeout=20).json()[:dept_limit]

        logger.info(f"Seeding Branch Group + Department across {len(b_groups)} branch groups and {len(departments)} departments...")
        created = 0
        for bg in b_groups:
            bgid = bg.get("id")
            bg_name = bg.get("group_Name") or f"bg{bgid}"
            for dp in departments:
                did = dp.get("id")
                d_name = dp.get("departmentName") or f"d{did}"
                mapping_key = (9, None, None, bgid, did)
                if mapping_key in self.existing_mappings:
                    continue

                bg_slug = clean_entity_slug(bg_name)
                d_slug = clean_entity_slug(d_name)
                # Format: {branch_group}.{dept}@{branch_group}.com
                email = self._generate_unique_email(f"{bg_slug}.{d_slug}", domain=f"{bg_slug}.com")
                payload = {
                    "id": 0,
                    "mail_Group_Type": 9,
                    "email_Id": email,
                    "company_Id": None,
                    "branch_Id": None,
                    "branch_Group_Id": bgid,
                    "department_Id": did,
                    "isActive": True
                }
                desc = f"BranchGroup+Dept: '{bg_name}' x '{d_name}'"
                if self.create_group_email_record(payload, desc):
                    self.existing_mappings.add(mapping_key)
                    created += 1

        return created

    def seed_global(self) -> int:
        """Ensures Global Group Broadcast emails (Type 10) are configured."""
        existing_global = [r for r in self.records_data if r.get("mail_Group_Type") == 10]
        if existing_global:
            logger.info(f"[SKIP] Global group email already configured: ID {existing_global[0].get('id')} -> '{existing_global[0].get('email_Id')}'")
            return 0

        global_emails = "all.staff@tekinspirations.com, global.broadcast@tekinspirations.com, management@tekinspirations.com"
        payload = {
            "id": 0,
            "mail_Group_Type": 10,
            "email_Id": global_emails,
            "company_Id": None,
            "branch_Id": None,
            "branch_Group_Id": None,
            "department_Id": None,
            "isActive": True
        }
        if self.create_group_email_record(payload, "Global Broadcast Email"):
            return 1
        return 0

    def run_all(self) -> Dict[str, int]:
        """Runs complete seeding process across all group mail tabs."""
        logger.info("================================================================================")
        logger.info("STARTING GROUP EMAIL MASTER SEEDING PIPELINE")
        logger.info("================================================================================")
        self.load_existing_records()

        summary = {
            "companies_seeded": self.seed_companies(),
            "branches_seeded": self.seed_branches(),
            "branch_groups_seeded": self.seed_branch_groups(),
            "branch_departments_seeded": self.seed_branch_departments(),
            "branch_group_departments_seeded": self.seed_branch_group_departments(),
            "global_seeded": self.seed_global(),
        }

        # Refresh count
        self.load_existing_records()
        summary["total_records_in_db"] = len(self.records_data)

        logger.info("================================================================================")
        logger.info("GROUP EMAIL MASTER SEEDING COMPLETED")
        for k, v in summary.items():
            logger.info(f" - {k.replace('_', ' ').title()}: {v}")
        logger.info("================================================================================")
        return summary


def main():
    parser = argparse.ArgumentParser(description="Seed HRlens Group Email Master Data.")
    parser.add_argument("--scope", choices=["all", "company", "branch", "branch_group", "dept", "bg_dept", "global"], default="all")
    args = parser.parse_args()

    seeder = GroupEmailSeeder()
    if args.scope == "all":
        seeder.run_all()
    elif args.scope == "company":
        seeder.load_existing_records()
        seeder.seed_companies()
    elif args.scope == "branch":
        seeder.load_existing_records()
        seeder.seed_branches()
    elif args.scope == "branch_group":
        seeder.load_existing_records()
        seeder.seed_branch_groups()
    elif args.scope == "dept":
        seeder.load_existing_records()
        seeder.seed_branch_departments()
    elif args.scope == "bg_dept":
        seeder.load_existing_records()
        seeder.seed_branch_group_departments()
    elif args.scope == "global":
        seeder.load_existing_records()
        seeder.seed_global()


if __name__ == "__main__":
    main()
