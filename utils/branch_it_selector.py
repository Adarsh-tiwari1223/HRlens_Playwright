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

# Map each Branch to its IT Persons and Target Branch Employees
BRANCH_RESPONSIBILITY_MAP = {
    "Varanasi": {
        "it_persons": [
            {"name": "Tejasav Jaiswal", "email": "tejasav.jaiswal@tekinspirations.com", "user_key": "it_varanasi_tejasav"},
            {"name": "Ashutosh Kumar", "email": "ashutosh.kumar@jobvritta.com", "user_key": "it_varanasi_ashutosh"}
        ],
        "employees": [
            {"name": "Sanidhy Tiwari", "email": "sanidhy.tiwari@tekinspirations.com", "user_key": "sanidhy"},
            {"name": "Raunak Rai", "email": "raunak.rai@tekinspirations.com", "user_key": "raunak_rai"},
            {"name": "Adarsh Tiwari", "email": "adarsh.tiwari@tekinspirations.com", "user_key": "adarsh_tiwari"},
            {"name": "Kumar Piyush", "email": "kumar.piyush@tekinspirations.com", "user_key": "kumar_piyush"}
        ]
    },
    "Agra": {
        "it_persons": [
            {"name": "Ritesh yadav", "email": "ritesh.y@tekinspirations.com", "user_key": "it_agra_ritesh"},
            {"name": "Sandeep Singh", "email": "sandeep.singh@tekinspirations.com", "user_key": "it_agra_sandeep"}
        ],
        "employees": [
            {"name": "Sandeep Singh", "email": "sandeep.singh@tekinspirations.com", "user_key": "sanidhy"}
        ]
    },
    "Meerut": {
        "it_persons": [
            {"name": "Aditya Saxena", "email": "aditya.saxena@tekinspirations.com", "user_key": "it_meerut_aditya"}
        ],
        "employees": [
            {"name": "Aditya Saxena", "email": "aditya.saxena@tekinspirations.com", "user_key": "sanidhy"}
        ]
    },
    "Noida": {
        "it_persons": [
            {"name": "Chandan", "email": "chandan@tekinspirations.com", "user_key": "it_noida_chandan"},
            {"name": "Puneet Kumar Prasad", "email": "pprasad@vyzeinc.com", "user_key": "it_noida_puneet"},
            {"name": "AMARJEET KUMAR", "email": "amarjeet.kumar@vyzeinc.com", "user_key": "it_noida_amarjeet"},
            {"name": "Abhishek Kumar", "email": "abhishek.kumar@vyzeinc.com", "user_key": "it_noida_abhishek"}
        ],
        "employees": [
            {"name": "Abhishek Singh", "email": "abhisheksingh@tekinspirations.com", "user_key": "abhishek_singh"},
            {"name": "Uttam Kumar", "email": "uttam.kumar@tekinspirations.com", "user_key": "uttam_kumar"}
        ]
    },
    "Lucknow": {
        "it_persons": [
            {"name": "Amit kumar Pal", "email": "amit.pal@codecrewzs.com", "user_key": "it_lucknow_amit"}
        ],
        "employees": [
            {"name": "Amit kumar Pal", "email": "amit.pal@codecrewzs.com", "user_key": "sanidhy"}
        ]
    },
    "Greater Noida": {
        "it_persons": [
            {"name": "Shubham Kumar", "email": "shubham@technovion.com", "user_key": "it_greaternoida_shubham"}
        ],
        "employees": [
            {"name": "Shubham Kumar", "email": "shubham@technovion.com", "user_key": "sanidhy"}
        ]
    },
    "Jaipur": {
        "it_persons": [
            {"name": "Ashu Sain", "email": "ashu.sain@corehuntinc.com", "user_key": "it_jaipur_ashu"}
        ],
        "employees": [
            {"name": "Ashu Sain", "email": "ashu.sain@corehuntinc.com", "user_key": "sanidhy"}
        ]
    }
}

def get_branch_it_person(branch: str = "Varanasi") -> dict:
    """Returns respected IT Person for a specific branch."""
    b_data = BRANCH_RESPONSIBILITY_MAP.get(branch, BRANCH_RESPONSIBILITY_MAP["Varanasi"])
    it_list = b_data["it_persons"]
    return random.choice(it_list)

def get_branch_target_employee(branch: str = "Varanasi") -> dict:
    """Returns respected employee belonging to the specific branch for asset assignment."""
    b_data = BRANCH_RESPONSIBILITY_MAP.get(branch, BRANCH_RESPONSIBILITY_MAP["Varanasi"])
    emp_list = b_data["employees"]
    return random.choice(emp_list)

def get_all_supported_branches() -> list[str]:
    """Returns list of all supported branch locations."""
    return list(BRANCH_RESPONSIBILITY_MAP.keys())
