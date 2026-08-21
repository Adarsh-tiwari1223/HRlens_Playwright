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
            {"name": "Kumar Piyush", "email": "kumar.piyush@tekinspirations.com", "user_key": "kumar_piyush"}
        ]
    },
    "Agra": {
        "it_persons": [
            {"name": "Ritesh yadav", "email": "ritesh.y@tekinspirations.com", "user_key": "it_agra_ritesh"},
            {"name": "Sandeep Singh", "email": "sandeep.singh@tekinspirations.com", "user_key": "it_agra_sandeep"}
        ],
        "employees": [
            {"name": "Adarsh Tiwari", "email": "adarsh.tiwari@tekinspirations.com", "user_key": "adarsh_tiwari"},
            {"name": "Sanidhy Tiwari", "email": "sanidhy.tiwari@tekinspirations.com", "user_key": "sanidhy"}
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

def get_branch_it_person(branch: str = "Varanasi") -> dict:
    """Returns respected IT Person for a specific branch with valid credentials in .env."""
    from core.config import settings
    b_data = BRANCH_RESPONSIBILITY_MAP.get(branch, BRANCH_RESPONSIBILITY_MAP["Varanasi"])
    it_list = b_data.get("it_persons", [])
    valid_its = [
        it for it in it_list
        if settings.USERS.get(it.get("user_key"), {}).get("password")
    ]
    if valid_its:
        return random.choice(valid_its)
    return it_list[0] if it_list else {"name": "Ashutosh Kumar", "email": "ashutosh.kumar@jobvritta.com", "user_key": "it_varanasi_ashutosh"}

def get_branch_target_employee(branch: str = "Varanasi") -> dict:
    """Returns respected employee belonging to the specific branch for asset assignment, randomly chosen from valid .env credentials."""
    from core.config import settings
    b_data = BRANCH_RESPONSIBILITY_MAP.get(branch, BRANCH_RESPONSIBILITY_MAP["Varanasi"])
    emp_list = b_data.get("employees", [])
    valid_emps = [
        e for e in emp_list
        if settings.USERS.get(e.get("user_key"), {}).get("password")
    ]
    if valid_emps:
        return random.choice(valid_emps)
    
    fallback_pool = []
    for key, name, email in [
        ("sanidhy", "Sanidhy Tiwari", "sanidhy.tiwari@tekinspirations.com"),
        ("adarsh_tiwari", "Adarsh Tiwari", "adarsh.tiwari@tekinspirations.com"),
        ("kumar_piyush", "Kumar Piyush", "kumar.piyush@tekinspirations.com"),
        ("abhishek_singh", "Abhishek Singh", "abhisheksingh@tekinspirations.com"),
        ("uttam_kumar", "Uttam Kumar", "uttam.kumar@tekinspirations.com")
    ]:
        if settings.USERS.get(key, {}).get("password"):
            fallback_pool.append({"name": name, "email": email, "user_key": key})
            
    if fallback_pool:
        return random.choice(fallback_pool)
        
    return {"name": "Sanidhy Tiwari", "email": "sanidhy.tiwari@tekinspirations.com", "user_key": "sanidhy"}

def get_all_supported_branches() -> list[str]:
    """Returns list of all supported branch locations."""
    return list(BRANCH_RESPONSIBILITY_MAP.keys())
