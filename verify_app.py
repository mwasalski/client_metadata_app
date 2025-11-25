import requests
import time
import subprocess
import sys
import os
import signal

BASE_URL = "http://127.0.0.1:5000"

def is_server_running():
    try:
        requests.get(BASE_URL, timeout=1)
        return True
    except requests.exceptions.ConnectionError:
        return False

def start_server():
    print("Starting server...")
    # Set env var to prevent browser auto-open if possible, though app.py doesn't check it.
    # We'll just let it open.
    process = subprocess.Popen([sys.executable, "app.py"], cwd=os.getcwd())
    time.sleep(3) # Wait for startup
    return process

def test_endpoints():
    print(f"Testing against {BASE_URL}...")
    
    # 1. Reset DB
    print("[TEST] Reset DB...", end=" ")
    try:
        res = requests.post(f"{BASE_URL}/api/reset-db")
        if res.status_code == 200 and res.json().get("reset") is True:
            print("PASS")
        else:
            print(f"FAIL ({res.status_code} {res.text})")
            return False
    except Exception as e:
        print(f"FAIL (Exception: {e})")
        return False

    # 2. Create Client
    print("[TEST] Create Client...", end=" ")
    payload = {
        "full_name": "Test User",
        "company": "Test Corp",
        "status": "prospect",
        "go_factors": "Likes the UI",
        "no_go_factors": "None"
    }
    try:
        res = requests.post(f"{BASE_URL}/api/clients", json=payload)
        if res.status_code == 201:
            print("PASS")
        else:
            print(f"FAIL ({res.status_code} {res.text})")
            return False
    except Exception as e:
        print(f"FAIL (Exception: {e})")
        return False

    # 3. Export CSV
    print("[TEST] Export CSV...", end=" ")
    try:
        res = requests.get(f"{BASE_URL}/api/export-csv")
        if res.status_code == 200 and res.headers["Content-Type"] == "text/csv":
            content = res.text
            if "Test User" in content and "Test Corp" in content:
                print("PASS")
            else:
                print("FAIL (Content missing created user)")
                print(f"Content preview: {content[:100]}")
                return False
        else:
            print(f"FAIL ({res.status_code})")
            return False
    except Exception as e:
        print(f"FAIL (Exception: {e})")
        return False

    return True

def main():
    server_process = None
    if not is_server_running():
        server_process = start_server()
    
    success = test_endpoints()
    
    if server_process:
        print("Stopping server...")
        server_process.terminate()
        # server_process.kill() # Force kill if needed
    
    if success:
        print("\nAll checks passed!")
        sys.exit(0)
    else:
        print("\nSome checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
