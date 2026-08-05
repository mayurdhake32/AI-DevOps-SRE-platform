import requests, json

BASE = "http://localhost:8000"

# 1. Health - works
print("HEALTH:", requests.get(f"{BASE}/health").json())

# 2. KB Search - works
print("SEARCH:", requests.post(f"{BASE}/knowledge-base/search", json={
    "query": "pod keeps crashing"
}).json())

# 3. Predict - might work differently
print("PREDICT:", requests.post(f"{BASE}/predict", json={
    "error_type": "kubernetes",
    "error_message": "Pod status is CrashLoopBackOff",
    "log_content": "Back-off restarting failed container",
    "repo_name": "payment-api"
}).json())