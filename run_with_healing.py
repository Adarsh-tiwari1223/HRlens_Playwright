import subprocess
import sys
import os
import re
from utils.auto_healer import heal_file

def run_tests_with_healing(pytest_args):
    """
    Runs pytest, intercepts failures, and attempts to auto-heal them.
    """
    max_retries = 2
    retry_count = 0

    while retry_count <= max_retries:
        print(f"\n[INFO] Running Pytest (Attempt {retry_count + 1}/{max_retries + 1})...")
        
        # Run pytest and capture output using current python executable
        cmd = [sys.executable, "-m", "pytest"] + pytest_args + ["--tb=short"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        output = result.stdout + result.stderr
        print(output)

        if result.returncode == 0:
            print("\n[SUCCESS] All tests passed successfully!")
            break

        print("\n[WARNING] Test Failure Detected!")
        
        # Simple parser to find the file that failed and the error trace
        # Looks for lines like: ERROR tests/test_smoke.py::test_increment_page_loads - TimeoutError...
        # Or standard pytest short traceback formats
        
        failed_file = None
        # Naive extraction of the first test file mentioned in the errors section
        match = re.search(r"(tests/[\w/]+\.py)", output)
        if match:
            failed_file = match.group(1)
        
        if failed_file and os.path.exists(failed_file):
            print(f"[INFO] Attempting to auto-heal {failed_file}...")
            healed = heal_file(failed_file, output)
            
            if healed:
                print("[INFO] Retrying test run after healing...")
                retry_count += 1
                continue
            else:
                print("[ERROR] Auto-healing could not resolve the issue. Exiting.")
                sys.exit(1)
        else:
            print("[ERROR] Could not automatically determine which file to heal from the traceback.")
            sys.exit(1)

if __name__ == "__main__":
    # Remove the script name from args
    args = sys.argv[1:]
    if not args:
        args = ["tests/"]
    run_tests_with_healing(args)
