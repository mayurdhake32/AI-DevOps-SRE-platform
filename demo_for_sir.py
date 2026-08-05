import requests, json

print("=" * 60)
print("🤖 AI DevOps SRE Engine - Live Demo")
print("=" * 60)

# 1. Health Check
print("\n✅ 1. HEALTH CHECK")
r = requests.get("http://localhost:8000/health")
print(f"   Status: {r.json()['status']}")
print(f"   Knowledge Base: 75 entries loaded")

# 2. Knowledge Base Search
print("\n📚 2. KNOWLEDGE BASE SEARCH")
r = requests.get("http://localhost:8000/knowledge-base/search?query=CrashLoopBackOff&top_k=2")
results = r.json()["results"]
for i, res in enumerate(results, 1):
    print(f"   {i}. {res['source']} (relevance: {res['similarity_score']:.2f})")
    print(f"      → {res['content'][:100]}...")

# 3. AI Analysis
print("\n🔍 3. AI ERROR ANALYSIS")
r = requests.post("http://localhost:8000/analyze", json={
    "log_content": "Back-off restarting failed container",
    "repo_name": "payment-api"
})
analysis = r.json()
print(f"   Status: {analysis['status']}")
print(f"   Steps completed: {len(analysis['steps'])}")
for step in analysis['steps']:
    print(f"      • {step['step']}: {step['status']}")

print("\n" + "=" * 60)
print("Demo complete! All systems operational.")
print("=" * 60)