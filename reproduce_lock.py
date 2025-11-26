import requests
import threading
import time
import sqlite3
import os
from app import app, DATABASE

def run_server():
    app.run(port=5002, use_reloader=False)

def hold_lock():
    print("Acquiring lock...")
    conn = sqlite3.connect(DATABASE)
    try:
        conn.execute("BEGIN EXCLUSIVE")
        print("Lock acquired. Sleeping...")
        time.sleep(10)
        print("Releasing lock...")
        conn.commit()
    except Exception as e:
        print(f"Lock failed: {e}")
    finally:
        conn.close()

def test_reset():
    # Give the server a moment to start
    time.sleep(2)
    
    # Start a thread to hold the lock
    lock_thread = threading.Thread(target=hold_lock)
    lock_thread.start()
    
    # Wait a bit for the lock to be acquired
    time.sleep(1)
    
    print("Attempting reset...")
    try:
        response = requests.post("http://127.0.0.1:5002/api/reset-db")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    # Ensure clean state
    if os.path.exists(DATABASE):
        pass # Keep existing DB
        
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    test_reset()
