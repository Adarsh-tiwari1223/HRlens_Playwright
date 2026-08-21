"""
User credentials and Approver mappings for HRlens Portal.
Dynamically resolves secrets from environment variables.
"""

import os
from core.config.environments import ENV


def _get_env(key: str, default: str = None) -> str:
    """
    Resolves environment-scoped key (e.g. KEY_STG or KEY_PROD) or falls back to generic KEY.
    """
    env_key = f"{key}_{ENV.upper()}"
    val = os.getenv(env_key) or os.getenv(key, default)
    return val.strip() if val else default


USERS = {
    "admin": {
        "username": _get_env("ADMIN_USERNAME"),
        "password": _get_env("ADMIN_PASSWORD")
    },
    "vivek": {
        "username": _get_env("VIVEK_USERNAME"),
        "password": _get_env("VIVEK_PASSWORD")
    },
    "tejaswini": {
        "username": _get_env("TEJASWINI"),
        "password": _get_env("TEJSWINI_PASSWORD")
    },
    "shiva": {
        "username": _get_env("SHIVA"),
        "password": _get_env("SHIVA_PASSWORD")
    },
    "sanidhy": {
        "username": _get_env("SANIDHY_USERNAME"),
        "password": _get_env("SANIDHY_PASSWORD")
    },
    "kumar_piyush": {
        "username": _get_env("KUMAR_PIYUSH_USERNAME"),
        "password": _get_env("KUMAR_PIYUSH_PASSWORD")
    },
    "ritesh_singh": {
        "username": _get_env("RITESH_SINGH_USERNAME"),
        "password": _get_env("RITESH_SINGH_PASSWORD")
    },
    "adarsh_tiwari": {
        "username": _get_env("ADARSH_TIWARI"),
        "password": _get_env("ADARSH_TIWARI_PASSWORD")
    },
    "uttam_kumar": {
        "username": _get_env("UTTAM_KUMAR_USERNAME"),
        "password": _get_env("UTTAM_KUMAR_PASSWORD")
    },
    "abhishek_singh": {
        "username": _get_env("ABHISHEK_SINGH_USERNAME"),
        "password": _get_env("ABHISHEK_SINGH_PASSWORD")
    },
    "it_admin": {
        "username": _get_env("IT_ADMIN_USERNAME"),
        "password": _get_env("IT_ADMIN_PASSWORD")
    },
    "it_agra_ritesh": {
        "username": _get_env("IT_AGRA_RITESHYADAV_USERNAME"),
        "password": _get_env("IT_AGRA_RITESHYADAV_PASSWORD")
    },
    "it_lucknow_amit": {
        "username": _get_env("IT_LUCKNOW_AMITPAL_USERNAME"),
        "password": _get_env("IT_LUCKNOW_AMITPAL_PASSWORD")
    },
    "it_greaternoida_shubham": {
        "username": _get_env("IT_GREATERNOIDA_SHUBHAMKUMAR_USERNAME"),
        "password": _get_env("IT_GREATERNOIDA_SHUBHAMKUMAR_PASSWORD")
    },
    "it_admin_greaternoida": {
        "username": _get_env("IT_ADMIN_GREATERNOIDA_USERNAME"),
        "password": _get_env("IT_ADMIN_GREATERNOIDA_PASSWORD")
    },
    "it_varanasi_raunak": {
        "username": _get_env("IT_VARANASI_RAUNAKRAI_USERNAME"),
        "password": _get_env("IT_VARANASI_RAUNAKRAI_PASSWORD")
    },
    "it_jaipur_ashu": {
        "username": _get_env("IT_JAIPUR_ASHUSAIN_USERNAME"),
        "password": _get_env("IT_JAIPUR_ASHUSAIN_PASSWORD")
    },
    "it_admin_jaipur": {
        "username": _get_env("IT_ADMIN_JAIPUR_USERNAME"),
        "password": _get_env("IT_ADMIN_JAIPUR_PASSWORD")
    },
    "it_meerut_aditya": {
        "username": _get_env("IT_MEERUT_ADITYASAXENA_USERNAME"),
        "password": _get_env("IT_MEERUT_ADITYASAXENA_PASSWORD")
    },
    "it_noida_puneet": {
        "username": _get_env("IT_NOIDA_PUNEETPRASAD_USERNAME"),
        "password": _get_env("IT_NOIDA_PUNEETPRASAD_PASSWORD")
    },
    "it_noida_amarjeet": {
        "username": _get_env("IT_NOIDA_AMARJEETKUMAR_USERNAME"),
        "password": _get_env("IT_NOIDA_AMARJEETKUMAR_PASSWORD")
    },
    "it_varanasi_ashutosh": {
        "username": _get_env("IT_VARANASI_ASHUTOSHKUMAR_USERNAME"),
        "password": _get_env("IT_VARANASI_ASHUTOSHKUMAR_PASSWORD")
    },
    "it_noida_abhishek": {
        "username": _get_env("IT_NOIDA_ABHISHEKKUMAR_USERNAME"),
        "password": _get_env("IT_NOIDA_ABHISHEKKUMAR_PASSWORD")
    },
    "it_agra_sandeep": {
        "username": _get_env("IT_AGRA_SANDEEPSINGH_USERNAME"),
        "password": _get_env("IT_AGRA_SANDEEPSINGH_PASSWORD")
    },
    "it_noida_chandan": {
        "username": _get_env("IT_NOIDA_CHANDAN_USERNAME"),
        "password": _get_env("IT_NOIDA_CHANDAN_PASSWORD")
    },
    "it_varanasi_tejasav": {
        "username": _get_env("IT_VARANASI_TEJASAVJAISWAL_USERNAME"),
        "password": _get_env("IT_VARANASI_TEJASAVJAISWAL_PASSWORD")
    }
}

# Maps app display name → USERS key
APPROVERS = {
    "Vivek": "vivek",
    "Vivek Singh": "vivek",
    "Tejaswini Rishivanshi": "tejaswini",
    "Shiva Singh": "shiva",
    "Ritesh Singh": "ritesh_singh",
    "Uttam Kumar": "uttam_kumar",
    "Abhishek Singh": "abhishek_singh",
}
