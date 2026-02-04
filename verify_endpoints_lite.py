import requests
import sys

BASE_URL = "http://localhost:5001"

def check_endpoint(method, path):
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json={}, timeout=5)
        
        status = response.status_code
        print(f"[{status}] {method} {path}")
        
        if status == 500:
            print(f"❌ INTERNAL SERVER ERROR on {path}")
            return False
        if status == 404:
            print(f"⚠️ 404 NOT FOUND on {path} (Might be intended)")
            # 404 is better than 500 regarding crash safety
            return True
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running?")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error checking {path}: {e}")
        return False

print("🔍 Checking Critical Endpoints...")
endpoints = [
    ("GET", "/api/dashboard/stats"),
    ("GET", "/api/ai/status"),
    ("GET", "/api/banking/stats"),
    ("GET", "/api/autoprocessor/stats"), 
    ("POST", "/api/chat"), # Should be 401 or 400, not 500
    ("POST", "/api/ocr/upload"), # Should be 401 or 400
]

failures = 0
for method, path in endpoints:
    if not check_endpoint(method, path):
        failures += 1

if failures > 0:
    print(f"\n❌ Found {failures} failures.")
    sys.exit(1)
else:
    print("\n✅ All critical endpoints responded (non-crash).")
