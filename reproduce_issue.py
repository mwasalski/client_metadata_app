import requests
import threading
import time
import sys
from app import app

def run_server():
    app.run(port=5001, use_reloader=False)

def test_reset():
    # Give the server a moment to start
    time.sleep(2)
    try:
        response = requests.post("http://127.0.0.1:5001/api/reset-db")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")
    finally:
        # We can't easily kill the flask server thread, but we can exit the script
        pass

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    test_reset()
