"""
Syncs all existing user passwords in .env with the latest passwords from GET /api/user.
Preserves exact file structure, comments, and non-password settings in .env.
"""

import os
import re
import requests
from dotenv import load_dotenv

load_dotenv(".env")

api_base = os.getenv("API_BASE_URL", "https://audit.jobvritta.com/api")
admin_user = os.getenv("ADMIN_USERNAME_STG", "admin@tek.com")
admin_pass = os.getenv("ADMIN_PASSWORD_STG", "Admin@ST2001")

print(f"[AUTH] Logging into API as: {admin_user}")
login_resp = requests.post(
    f"{api_base}/user/login",
    json={"email": admin_user, "user": admin_user, "password": admin_pass},
    timeout=30
)
if login_resp.status_code != 200:
    raise Exception(f"Admin login failed: {login_resp.status_code} - {login_resp.text}")

token = login_resp.json().get("token")
print("[AUTH] Admin bearer token acquired.")

headers = {"Authorization": f"Bearer {token}"}
print("[API] Fetching all user records via GET /api/user?first=0&rows=1000...")
user_resp = requests.get(
    f"{api_base}/user",
    headers=headers,
    params={"first": 0, "rows": 1000},
    timeout=30
)
if user_resp.status_code != 200:
    raise Exception(f"GET /user failed: {user_resp.status_code} - {user_resp.text}")

users_data = user_resp.json()
if isinstance(users_data, dict):
    users = users_data.get("users") or users_data.get("data") or users_data.get("result") or []
elif isinstance(users_data, list):
    users = users_data
else:
    users = []

print(f"[API] Total users retrieved: {len(users)}")

# Build email -> password mapping (case-insensitive)
email_to_pwd = {}
for u in users:
    email = (u.get("email") or u.get("login_Email") or "").strip().lower()
    pwd = (u.get("login_Password") or u.get("password") or "").strip()
    name = (u.get("name") or u.get("userName") or "").strip()
    if email and pwd:
        email_to_pwd[email] = {
            "password": pwd,
            "name": name,
            "login_ID": u.get("login_ID")
        }

# Read .env lines
env_path = ".env"
with open(env_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Parse all lines into key-value pairs
parsed_entries = []
for idx, line in enumerate(lines):
    line_s = line.strip()
    if line_s and not line_s.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        parsed_entries.append({
            "idx": idx,
            "key": k.strip(),
            "val": v.rstrip("\r\n").strip(),
            "raw": line
        })

# Map email variables to their password variables
# For each entry whose value is an email in email_to_pwd:
email_var_map = {}
for entry in parsed_entries:
    val_lower = entry["val"].lower()
    if "@" in val_lower and val_lower in email_to_pwd:
        email_var_map[entry["key"]] = {
            "email": val_lower,
            "idx": entry["idx"],
            "api_pwd": email_to_pwd[val_lower]["password"],
            "name": email_to_pwd[val_lower]["name"]
        }

updates = []

for email_key, info in email_var_map.items():
    email = info["email"]
    api_pwd = info["api_pwd"]
    email_idx = info["idx"]

    # Target password variable name candidates
    prefix = email_key.replace("_USERNAME", "").replace("_EMAIL", "")
    candidates = [
        f"{prefix}_PASSWORD",
        f"{email_key}_PASSWORD",
        f"{prefix}_PASS",
    ]
    if email_key == "TEJASWINI":
        candidates.extend(["TEJSWINI_PASSWORD", "TEJASWINI_PASSWORD"])
    elif email_key == "SHIVA":
        candidates.append("SHIVA_PASSWORD")
    elif email_key == "ADARSH_TIWARI":
        candidates.append("ADARSH_TIWARI_PASSWORD")

    # Search nearby lines (+/- 4 lines) or entire parsed entries for candidates
    found_pwd_entry = None
    for cand in candidates:
        for p in parsed_entries:
            if p["key"] == cand and abs(p["idx"] - email_idx) <= 4:
                found_pwd_entry = p
                break
        if found_pwd_entry:
            break

    if not found_pwd_entry:
        for cand in candidates:
            for p in parsed_entries:
                if p["key"] == cand:
                    found_pwd_entry = p
                    break
            if found_pwd_entry:
                break

    if found_pwd_entry:
        current_pwd = found_pwd_entry["val"]
        pwd_key = found_pwd_entry["key"]
        pwd_idx = found_pwd_entry["idx"]

        if current_pwd != api_pwd:
            updates.append({
                "email_key": email_key,
                "pwd_key": pwd_key,
                "email": email,
                "name": info["name"],
                "old_pwd": current_pwd,
                "new_pwd": api_pwd,
                "line_idx": pwd_idx
            })
            lines[pwd_idx] = f"{pwd_key}={api_pwd}\n"
        else:
            print(f"[OK] {pwd_key} already matches API password ('{api_pwd}').")
    else:
        print(f"[WARN] No password variable found for email key '{email_key}' ({email})")

print("\n" + "=" * 80)
print(f"PASSWORD SYNC REPORT: {len(updates)} UPDATES FOUND")
print("=" * 80)
for u in updates:
    print(f"-> {u['pwd_key']} ({u['name']} <{u['email']}>):")
    print(f"   OLD: '{u['old_pwd']}'")
    print(f"   NEW: '{u['new_pwd']}'")

# Write updated lines back to .env
with open(env_path, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("=" * 80)
print("[SUCCESS] .env file successfully updated with latest passwords from GET /api/user!")
