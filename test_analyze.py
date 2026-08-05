import requests

r = requests.post("http://localhost:8000/analyze", json={
    "log_content": "Pod status is CrashLoopBackOff. Back-off restarting failed container. kubectl get pods shows OOMKilled.",
    "repo_name": "payment-api"
})
print(r.json())