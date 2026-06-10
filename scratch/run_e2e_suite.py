import os
import sys

# Setup script files
SCRIPTS = [
    "scratch/e2e_attendance.py",
    "scratch/e2e_leaves.py",
    "scratch/e2e_profile.py",
    "scratch/e2e_work_transfers.py",
    "scratch/e2e_tasks.py",
    "scratch/e2e_meetings.py",
    "scratch/e2e_announcements.py"
]

def run_all_tests():
    print("="*60)
    print("STARTING HR PORTAL END-TO-END WORKFLOW VERIFICATION")
    print("="*60)
    
    passed_count = 0
    failed_count = 0
    failures = []
    
    import subprocess
    python_exe = sys.executable

    for script in SCRIPTS:
        print(f"Running {script}...")
        try:
            res = subprocess.run([python_exe, script], capture_output=True, text=True, check=True)
            print(res.stdout.strip())
            passed_count += 1
        except subprocess.CalledProcessError as err:
            print(f"FAIL: {script}")
            print(err.stderr)
            failed_count += 1
            failures.append((script, err.stderr))
        print("-" * 40)

    print("\n" + "="*60)
    print("WORKFLOW VERIFICATION REPORT SUMMARY")
    print("="*60)
    print(f"Total Tests Executed: {len(SCRIPTS)}")
    print(f"PASSED: {passed_count}")
    print(f"FAILED: {failed_count}")
    
    if failed_count > 0:
        print("\nFailures Detail:")
        for script, err in failures:
            print(f"- {script}: {err.strip()}")
        sys.exit(1)
    else:
        print("\nALL WORKFLOW MODULES PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    run_all_tests()
