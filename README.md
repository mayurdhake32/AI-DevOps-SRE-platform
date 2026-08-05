# AI DevOps Engineer (Virtual SRE)

An AI-powered Site Reliability Engineering agent that automatically debugs failed deployments, identifies root causes, generates fixes, creates pull requests, and redeploys applications.

## Architecture
Deployment Logs
|
v
[Log Parser] --> [Error Classifier (ML)]
|                    |
v                    v
[Root Cause Analyzer] <-- [RAG Knowledge Base]
|
v
[Fix Generator] --> [GitHub PR]
|
v
[Deployment Manager] --> [Redeploy]
plain

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Web API | FastAPI |
| ML Models | scikit-learn (Random Forest, Gradient Boosting) |
| LLM | OpenAI GPT-4 / Local LLM |
| Vector DB | ChromaDB |
| Embeddings | sentence-transformers |
| Git Integration | PyGithub |
| Containerization | Docker |
| Orchestration | Kubernetes |
| Monitoring | Prometheus + Grafana |

## Step-by-Step Setup

### 1. Create Project Structure
```bash
mkdir ai-devops-sre
cd ai-devops-sre
mkdir -p src/{agents,fixers,integrations,ml/{models,training},parsers,rag,utils}
mkdir -p config data/{training,knowledge_base} deployment tests
2. Install Dependencies
bash
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
3. Configure Environment
bash
cp .env.example .env
# Edit .env and add:
# OPENAI_API_KEY=sk-your-key
# GITHUB_TOKEN=ghp-your-token
4. Initialize Knowledge Base
bash
python main.py --init-kb
5. Train ML Models
bash
python -c "
from main import AIDevOpsSRE
import json
sre = AIDevOpsSRE()
with open('data/training/sample_logs.json') as f:
    logs = json.load(f)
with open('data/training/sample_deployments.json') as f:
    deployments = json.load(f)
results = sre.train_models(logs=logs, deployments=deployments)
print(json.dumps(results, indent=2))
"
6. Run Web API
bash
python app.py
# API available at http://localhost:8000
7. Test API Endpoints
bash
# Health check
curl http://localhost:8000/health

# Analyze logs
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"log_content": "docker build failed: pull access denied", "repo_name": "owner/repo"}'

# Predict failure
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"deployment_info": {"lines_added": 500, "files_changed": 10, "author_failure_rate": 0.1}}'
8. Run with Docker
bash
cd deployment
docker-compose up -d
9. Deploy to Kubernetes
bash
kubectl apply -f deployment/k8s-manifest.yaml
API Endpoints
Table
Method	Endpoint	Description
GET	/health	Health check
POST	/analyze	Analyze deployment logs
POST	/predict	Predict deployment failure
POST	/train	Retrain ML models
POST	/webhook/github	GitHub webhook handler
GET	/knowledge-base/search	Search knowledge base
For Your Final Year Project
Key Components
ML Pipeline - TF-IDF + Random Forest for multi-label classification
RAG System - ChromaDB with sentence-transformers embeddings
LLM Integration - GPT-4 for root cause analysis
DevOps Automation - GitHub API for PR creation
Monitoring - Prometheus metrics and Grafana dashboards
Report Structure
Introduction & Problem Statement
Literature Survey
System Design & Architecture
Implementation Details
Testing & Results
Conclusion & Future Scope
plain

---

## Complete Step-by-Step: How to Run

### Step 1: Create all folders
```bash
mkdir -p ai-devops-sre/{src/{agents,fixers,integrations,ml/{models,training},parsers,rag,utils},config,data/{training,knowledge_base},deployment,tests}
cd ai-devops-sre
Step 2: Create all files above
Copy-paste each file into its location.
Step 3: Install and run
bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY="sk-your-key"
export GITHUB_TOKEN="ghp-your-token"

# Initialize knowledge base
python main.py --init-kb

# Train models
python -c "
from main import AIDevOpsSRE
import json
sre = AIDevOpsSRE()
with open('data/training/sample_logs.json') as f:
    logs = json.load(f)
with open('data/training/sample_deployments.json') as f:
    deps = json.load(f)
print(sre.train_models(logs=logs, deployments=deps))
"

# Start API server
python app.py
Step 4: Test
Open browser to http://localhost:8000/docs for interactive API docs.