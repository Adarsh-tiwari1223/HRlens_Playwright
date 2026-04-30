import os
import re
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

ALLOWED_BASE = Path(os.getcwd()).resolve()


def _safe_path(filepath: str) -> Path:
    path = Path(filepath).resolve()
    if not str(path).startswith(str(ALLOWED_BASE)):
        raise ValueError(f"Path traversal detected: {filepath}")
    return path

def heal_file(filepath: str, error_trace: str) -> bool:
    """
    Analyzes the error trace, calls an LLM to generate a fix, and applies it to the file.
    """
    print(f"\n[Healer] [INFO] Analyzing failure in {filepath}...")
    
    path = _safe_path(filepath)
    file_content = path.read_text(encoding="utf-8")

    # If no API key, use a simple mock fallback to demonstrate functionality
    if not GEMINI_API_KEY:
        print("[Healer] [WARNING] No GEMINI_API_KEY found in .env. Falling back to mock healing.")
        return mock_heal(filepath, file_content, error_trace)

    prompt = f"""
    You are an expert Playwright automation engineer.
    A test has failed with the following error trace:
    {error_trace}

    Here is the source code of the file {filepath}:
    ```python
    {file_content}
    ```

    Analyze the error and the code. Provide the fixed source code for the entire file.
    Return ONLY the raw python code without any markdown blocks, explanations, or quotes.
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2}
    }

    try:
        response = requests.post(GEMINI_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        fixed_code = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        # Clean up markdown if the LLM hallucinated it despite instructions
        fixed_code = fixed_code.removeprefix("```python").removesuffix("```").strip()

        if fixed_code and fixed_code != file_content:
            _safe_path(filepath).write_text(fixed_code, encoding="utf-8")
            print("[Healer] [SUCCESS] Successfully applied AI fix to the file!")
            return True
        else:
            print("[Healer] [ERROR] AI could not determine a fix.")
            return False

    except requests.RequestException as e:
        print(f"[Healer] [ERROR] Failed to call LLM API: {e}")
        return False

def mock_heal(filepath: str, file_content: str, error_trace: str) -> bool:
    """Mock healing logic for demonstration purposes."""
    if 'settings.USERS["admin"]' in file_content and "Timeout" in error_trace:
        print("[Healer] [INFO] Auto-detected staging credentials issue. Swapping 'admin' to 'vivek'.")
        fixed_content = file_content.replace('settings.USERS["admin"]', 'settings.USERS["vivek"]')
        _safe_path(filepath).write_text(fixed_content, encoding="utf-8")
        return True
    
    if 'locator("text=Fake Button")' in error_trace:
        print("[Healer] [INFO] Auto-detected broken locator. Patching to a valid locator.")
        fixed_content = file_content.replace('"text=Fake Button"', '"text=Logged in Successfully"')
        _safe_path(filepath).write_text(fixed_content, encoding="utf-8")
        return True
        
    print("[Healer] [ERROR] Mock healer could not find a predefined fix for this error.")
    return False
