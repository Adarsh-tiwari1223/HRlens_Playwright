import os
import sys
import json
import re
import urllib.request

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from core.config import settings

def clean_var_name(name: str) -> str:
    # Remove special chars, upper case, replace spaces/dots with underscores
    clean = re.sub(r"[^A-Za-z0-9\s._-]", "", name).strip()
    clean = re.sub(r"[\s._-]+", "_", clean).upper()
    return clean

def sync_branch_users():
    print("==================================================")
    print("HRlens API — Branch Employee Credential Harvester")
    print("==================================================")

    login_url = f"{settings.API_BASE_URL}/user/login"
    creds = settings.USERS.get("admin", {})
    login_data = json.dumps({
        "email": creds["username"],
        "user": creds["username"],
        "password": creds["password"]
    }).encode("utf-8")

    print(f"Logging in to API as {creds['username']}...")
    req = urllib.request.Request(login_url, data=login_data, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        token = json.loads(resp.read().decode("utf-8")).get("token")

    print("Fetching user list from /user?first=0&rows=500...")
    api_url = f"{settings.API_BASE_URL}/user?first=0&rows=500"
    get_req = urllib.request.Request(api_url, headers={"Authorization": f"Bearer {token}", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(get_req, timeout=15) as resp:
        raw_resp = json.loads(resp.read().decode("utf-8"))

    users_list = raw_resp if isinstance(raw_resp, list) else raw_resp.get("users", raw_resp.get("data", raw_resp.get("result", [])))
    print(f"Fetched {len(users_list)} total users from backend API.")

    branch_users = {}
    for u in users_list:
        email = (u.get("login_Email") or u.get("email") or u.get("userName") or "").strip()
        pwd = (u.get("login_Password") or u.get("password") or u.get("login_password") or "").strip()
        name = (u.get("name") or u.get("employeeName") or u.get("fullName") or email).strip()
        branch_raw = u.get("branch") or u.get("branchName") or u.get("branch_Name") or u.get("branchGroup") or "General"
        
        if isinstance(branch_raw, dict):
            branch_name = branch_raw.get("name") or branch_raw.get("branchName") or "General"
        else:
            branch_name = str(branch_raw)
            
        branch_name = branch_name.strip()
        if not email or not pwd or "@" not in email:
            continue
            
        if branch_name not in branch_users:
            branch_users[branch_name] = []
            
        # Avoid duplicate emails per branch
        if not any(e["email"].lower() == email.lower() for e in branch_users[branch_name]):
            branch_users[branch_name].append({
                "name": name,
                "email": email,
                "password": pwd,
                "role": u.get("role") or u.get("roleName") or ""
            })

    formatted_sections = []

    print("\n--- FORMATTING BRANCH EMPLOYEES IN EXACT REQUESTED .ENV STYLE ---")
    for branch, emps in branch_users.items():
        section_lines = [
            f"# ══════════════════════════════════════════════════════════════════════════════",
            f"# EMPLOYEES ({branch})",
            f"# ══════════════════════════════════════════════════════════════════════════════"
        ]
        
        for emp in emps[:10]: # Top 10 per branch
            var_base = clean_var_name(emp['name'])
            # Exclude generic names like ADMIN or SALES
            if var_base in ["ADMIN", "SALES"]:
                continue
                
            username_var = f"{var_base}_USERNAME"
            password_var = f"{var_base}_PASSWORD"
            
            section_lines.append(f"{username_var}={emp['email']}")
            section_lines.append(f"{password_var}={emp['password']}\n")
            
        formatted_sections.append("\n".join(section_lines))

    new_credentials_block = "\n\n".join(formatted_sections)

    env_path = os.path.join(root_dir, ".env")
    with open(env_path, "r", encoding="utf-8") as f:
        existing_env = f.read()

    # Locate where EMPLOYEES section starts or append at end of EMPLOYEES block
    split_marker = "# ══════════════════════════════════════════════════════════════════════════════\n# EMPLOYEES (DEVELOPERS & STAFF)"
    if split_marker in existing_env:
        pre_part = existing_env.split(split_marker)[0].rstrip()
    elif "# BRANCH EMPLOYEES (DYNAMICALLY HARVESTED VIA API)" in existing_env:
        pre_part = existing_env.split("# BRANCH EMPLOYEES (DYNAMICALLY HARVESTED VIA API)")[0].rstrip()
    else:
        pre_part = existing_env.split("# EMPLOYEES")[0].rstrip() if "# EMPLOYEES" in existing_env else existing_env.rstrip()

    final_env = f"{pre_part}\n\n{new_credentials_block}\n"

    with open(env_path, "w", encoding="utf-8") as f:
        f.write(final_env)

    print("\n[SUCCESS] Successfully formatted and updated .env with branch employee sections!")

if __name__ == "__main__":
    sync_branch_users()
