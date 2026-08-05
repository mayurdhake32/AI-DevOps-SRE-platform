import requests

r = requests.get("http://localhost:8000/knowledge-base/search?query=CrashLoopBackOff&top_k=3")
print(r.json())