import os
import shutil
import glob

dirs_to_clean = [
    "reports/payroll blocker report",
    "reports/payroll data report"
]

for d in dirs_to_clean:
    if os.path.exists(d):
        print(f"Cleaning directory: {d}")
        # Delete all files in the directory
        for item in os.listdir(d):
            item_path = os.path.join(d, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                    print(f"  Deleted file: {item_path}")
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    print(f"  Deleted dir: {item_path}")
            except Exception as e:
                print(f"  Failed to delete {item_path}: {e}")
    else:
        print(f"Directory {d} does not exist.")

# Clean any payroll_release txt files in reports/ root
for f in glob.glob("reports/payroll_release_*.txt"):
    try:
        os.unlink(f)
        print(f"Deleted root release file: {f}")
    except Exception as e:
        print(f"Failed to delete {f}: {e}")

print("Cleanup complete.")
