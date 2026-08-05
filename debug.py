import requests, traceback

try:
    r = requests.post("http://localhost:8000/analyze", json={
        "error_type": "kubernetes",
        "error_message": "Pod status is CrashLoopBackOff",
        "log_content": "Back-off restarting failed container",
        "repo_name": "payment-api"
    })
    print(r.json())
except Exception as e:
    traceback.print_exc()