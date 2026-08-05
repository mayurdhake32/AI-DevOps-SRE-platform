import requests
import json

# Load training data
with open("training_data.json", "r") as f:
    logs = json.load(f)

print(f"Loaded {len(logs)} training samples")

# Train the model
response = requests.post("http://localhost:8000/train", json={
    "logs": logs,
    "deployments": []
})

result = response.json()
print("\nTraining Results:")
print(json.dumps(result, indent=2))