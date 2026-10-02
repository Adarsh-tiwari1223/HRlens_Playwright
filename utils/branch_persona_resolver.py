"""
Branch-Scoped Persona Resolver Utility.

Strictly provides aligned operational personas belonging to the SAME branch:
- Employee
- IT Person
- HR Person
- Accountant / Finance

Ensures tests never bypass branch-level RBAC.
"""

import logging
from core.config import settings

logger = logging.getLogger(__name__)

# Complete Branch-to-Persona mapping for strict RBAC isolation
BRANCH_PERSONA_MAP = {
    "Varanasi": {
        "branch": "Varanasi",
        "employee": "adarsh_tiwari",
        "employee_name": "Adarsh Tiwari",
        "it_person": "it_varanasi_ashutosh",
        "it_name": "Ashutosh Kumar",
        "hr_person": "tejaswini",
        "hr_name": "Tejaswini Rishivanshi",
        "accountant": "sunil_kumar",
        "accountant_name": "Sunil Kumar",
        "accountant_alt": "riya_tripathi",
        "accountant_alt_name": "Riya Tripathi"
    },
    "Agra": {
        "branch": "Agra",
        "employee": "sanjeev_rohatgi",
        "employee_name": "Sanjeev Rohatgi",
        "it_person": "it_agra_ritesh",
        "it_name": "Ritesh yadav",
        "hr_person": "tejaswini",
        "hr_name": "Tejaswini Rishivanshi",
        "accountant": "shreya_singh",
        "accountant_name": "Shreya Singh"
    },
    "Meerut": {
        "branch": "Meerut",
        "employee": "shatveer",
        "employee_name": "Shatveer",
        "it_person": "it_meerut_aditya",
        "it_name": "Aditya Saxena",
        "hr_person": "tejaswini",
        "hr_name": "Tejaswini Rishivanshi",
        "accountant": "shreya_singh",
        "accountant_name": "Shreya Singh"
    },
    "Noida": {
        "branch": "Noida",
        "employee": "abhishek_singh",
        "employee_name": "Abhishek Singh",
        "it_person": "it_noida_puneet",
        "it_name": "Puneet Kumar Prasad",
        "hr_person": "tejaswini",
        "hr_name": "Tejaswini Rishivanshi",
        "accountant": "shreya_singh",
        "accountant_name": "Shreya Singh"
    }
}


def get_branch_persona_bundle(branch: str = "Varanasi") -> dict:
    """
    Returns the aligned 4-persona dictionary for the target branch:
    - employee: user_key
    - it_person: user_key
    - hr_person: user_key
    - accountant: user_key
    """
    matched_branch = next(
        (k for k in BRANCH_PERSONA_MAP if k.lower() == (branch or "").lower()),
        "Varanasi"
    )
    bundle = BRANCH_PERSONA_MAP[matched_branch]
    logger.info(
        f"[BRANCH PERSONA RESOLVER] Branch: '{matched_branch}' | "
        f"Employee: '{bundle['employee_name']}' | "
        f"IT: '{bundle['it_name']}' | "
        f"HR: '{bundle['hr_name']}' | "
        f"Accountant: '{bundle['accountant_name']}'"
    )
    return bundle


# Branch-specific Employee candidate pools for dynamic selection (no hardcoding)
BRANCH_EMPLOYEE_POOLS = {
    "Varanasi": [
        {"user_key": "adarsh_tiwari", "name": "Adarsh Tiwari"},
        {"user_key": "sanidhy", "name": "Sanidhy Tiwari"},
        {"user_key": "uttam_kumar", "name": "Uttam Kumar"},
        {"user_key": "abhishek_singh", "name": "Abhishek Singh"},
        {"user_key": "namrata_pandey", "name": "Namrata Pandey"},
        {"user_key": "uday_pratap", "name": "Uday Pratap"},
        {"user_key": "kailash_singh", "name": "Kailash Singh"},
    ],
    "Agra": [
        {"user_key": "sanjeev_rohatgi", "name": "Sanjeev Rohatgi"},
        {"user_key": "riyan_sharma", "name": "Riyan Sharma"},
        {"user_key": "saurabh_kumar", "name": "Saurabh Kumar"},
        {"user_key": "deepa_lawaniya", "name": "Deepa Lawaniya"},
        {"user_key": "priyanka_maurya", "name": "Priyanka Maurya"},
    ],
    "Noida": [
        {"user_key": "davesh_sharma", "name": "Davesh Sharma"},
        {"user_key": "pramod_nayak", "name": "Pramod Nayak"},
        {"user_key": "naseema_bano", "name": "Naseema Bano"},
    ],
    "Meerut": [
        {"user_key": "shatveer", "name": "Shatveer"},
        {"user_key": "arvind_kumar", "name": "Arvind Kumar"},
    ]
}


def get_dynamic_resignation_employee(branch: str = "Varanasi", exclude_keys: list = None) -> dict:
    """
    Dynamically resolves an active employee for resignation workflows without hardcoding.
    Allows rotating through available employees in the branch.
    """
    import random
    pool = BRANCH_EMPLOYEE_POOLS.get(branch, BRANCH_EMPLOYEE_POOLS["Varanasi"])
    candidates = [e for e in pool if not exclude_keys or e["user_key"] not in exclude_keys]
    selected = random.choice(candidates) if candidates else pool[0]
    logger.info(f"[DYNAMIC RESIGNATION EMPLOYEE] Selected '{selected['name']}' ({selected['user_key']}) for branch '{branch}'")
    return selected

