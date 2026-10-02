"""
Branch-Scoped IT Person Responsibility Selector Utility.

Maps each branch to its respected IT Person and Branch Employees for:
- Asset Procurement & Generation
- Direct Asset Assignment
- Asset Return Request & IT Condition Assessment (Good, Repair Required, Damaged, Lost)
- Asset Maintenance & Repair Outcomes
- Asset Disposal / Scrap
"""

import os
import json
import random
import logging

logger = logging.getLogger(__name__)

# Map each Branch to its IT Persons and Target Branch Employees (present in .env)
BRANCH_RESPONSIBILITY_MAP = {
    "Varanasi": {
        "it_persons": [
            {"name": "Ashutosh Kumar", "email": "ashutosh.kumar@jobvritta.com", "user_key": "it_varanasi_ashutosh"},
            {"name": "Tejasav Jaiswal", "email": "tejasav.jaiswal@tekinspirations.com", "user_key": "it_varanasi_tejasav"}
        ],
        "employees": [
            {"name": "Adarsh Tiwari", "email": "adarsh.tiwari@tekinspirations.com", "user_key": "adarsh_tiwari"},
            {"name": "Sanidhy Tiwari", "email": "sanidhy.tiwari@tekinspirations.com", "user_key": "sanidhy"},
            {"name": "Kumar Piyush", "email": "kumar.piyush@tekinspirations.com", "user_key": "kumar_piyush"},
            {"name": "Ritesh Singh", "email": "ritesh.singh@tekinspirations.com", "user_key": "ritesh_singh"},
            {"name": "Uttam Kumar", "email": "uttam.kumar@tekinspirations.com", "user_key": "uttam_kumar"},
            {"name": "Abhishek Singh", "email": "abhisheksingh@tekinspirations.com", "user_key": "abhishek_singh"}
        ]
    },
    "Agra": {
        "it_persons": [
            {"name": "Ritesh yadav", "email": "ritesh.y@tekinspirations.com", "user_key": "it_agra_ritesh"},
            {"name": "Sandeep Singh", "email": "sandeep.singh@tekinspirations.com", "user_key": "it_agra_sandeep"}
        ],
        "employees": [
            {"name": "Sanjeev Rohatgi", "email": "srohatgi@tekinspirations.com", "user_key": "sanjeev_rohatgi"},
            {"name": "Riyan Sharma", "email": "Riyan@tekinspirations.com", "user_key": "riyan_sharma"},
            {"name": "Saurabh Kumar", "email": "saurabh.kumar@tekinspirations.com", "user_key": "saurabh_kumar"}
        ]
    },
    "Meerut": {
        "it_persons": [
            {"name": "Aditya Saxena", "email": "aditya.saxena@tekinspirations.com", "user_key": "it_meerut_aditya"}
        ],
        "employees": [
            {"name": "Adarsh Tiwari", "email": "adarsh.tiwari@tekinspirations.com", "user_key": "adarsh_tiwari"},
            {"name": "Sanidhy Tiwari", "email": "sanidhy.tiwari@tekinspirations.com", "user_key": "sanidhy"}
        ]
    },
    "Noida": {
        "it_persons": [
            {"name": "Puneet Kumar Prasad", "email": "pprasad@vyzeinc.com", "user_key": "it_noida_puneet"},
            {"name": "Chandan", "email": "chandan@tekinspirations.com", "user_key": "it_noida_chandan"},
            {"name": "AMARJEET KUMAR", "email": "amarjeet.kumar@vyzeinc.com", "user_key": "it_noida_amarjeet"},
            {"name": "Abhishek Kumar", "email": "abhishek.kumar@vyzeinc.com", "user_key": "it_noida_abhishek"}
        ],
        "employees": [
            {"name": "Abhishek Singh", "email": "abhisheksingh@tekinspirations.com", "user_key": "abhishek_singh"},
            {"name": "Uttam Kumar", "email": "uttam.kumar@tekinspirations.com", "user_key": "uttam_kumar"},
            {"name": "Sanidhy Tiwari", "email": "sanidhy.tiwari@tekinspirations.com", "user_key": "sanidhy"}
        ]
    },
    "Lucknow": {
        "it_persons": [
            {"name": "Amit kumar Pal", "email": "amit.pal@codecrewzs.com", "user_key": "it_lucknow_amit"}
        ],
        "employees": [
            {"name": "Sanidhy Tiwari", "email": "sanidhy.tiwari@tekinspirations.com", "user_key": "sanidhy"}
        ]
    },
    "Greater Noida": {
        "it_persons": [
            {"name": "Shubham Kumar", "email": "shubham@technovion.com", "user_key": "it_greaternoida_shubham"}
        ],
        "employees": [
            {"name": "Sanidhy Tiwari", "email": "sanidhy.tiwari@tekinspirations.com", "user_key": "sanidhy"}
        ]
    },
    "Jaipur": {
        "it_persons": [
            {"name": "Ashu Sain", "email": "ashu.sain@corehuntinc.com", "user_key": "it_jaipur_ashu"}
        ],
        "employees": [
            {"name": "Sanidhy Tiwari", "email": "sanidhy.tiwari@tekinspirations.com", "user_key": "sanidhy"}
        ]
    }
}

def get_branch_it_person(branch: str = "Varanasi", shuffle: bool = True) -> dict:
    """Returns an IT Person for a specific branch with valid credentials in .env (shuffled if shuffle=True)."""
    valid_its = get_all_branch_it_persons(branch)
    if valid_its:
        return random.choice(valid_its) if shuffle else valid_its[0]
    return {"name": "Ashutosh Kumar", "email": "ashutosh.kumar@jobvritta.com", "user_key": "it_varanasi_ashutosh"}

def get_all_branch_it_persons(branch: str = "Varanasi") -> list[dict]:
    """Returns all IT persons belonging to a branch with valid credentials in .env."""
    from core.config import settings
    matched_branch = next((k for k in BRANCH_RESPONSIBILITY_MAP if k.lower() == (branch or "").lower()), "Varanasi")
    b_data = BRANCH_RESPONSIBILITY_MAP.get(matched_branch, BRANCH_RESPONSIBILITY_MAP["Varanasi"])
    it_list = b_data.get("it_persons", [])
    return [
        it for it in it_list
        if settings.USERS.get(it.get("user_key"), {}).get("password")
    ]

def get_all_branch_employees(branch: str = "Varanasi") -> list[dict]:
    """Returns all test employees belonging to a branch."""
    matched_branch = next((k for k in BRANCH_RESPONSIBILITY_MAP if k.lower() == (branch or "").lower()), "Varanasi")
    b_data = BRANCH_RESPONSIBILITY_MAP.get(matched_branch, BRANCH_RESPONSIBILITY_MAP["Varanasi"])
    return b_data.get("employees", [])

def get_branch_target_employee(branch: str = "Varanasi") -> dict:
    """Returns a target test employee belonging to a branch."""
    emps = get_all_branch_employees(branch)
    return emps[0] if emps else {"name": "Adarsh Tiwari", "email": "adarsh.tiwari@tekinspirations.com", "user_key": "adarsh_tiwari"}

def get_all_supported_branches() -> list[str]:
    """Returns a list of all branches supported in the responsibility map."""
    return list(BRANCH_RESPONSIBILITY_MAP.keys())
