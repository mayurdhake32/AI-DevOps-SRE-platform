# AI DevOps SRE — Restart Guide

Use this every time after shutting down your laptop or closing the terminal.

---

## Step 1: Open PowerShell

Press `Win` → type `PowerShell` → press Enter.

---

## Step 2: Go to Project Folder

```powershell
cd C:\Users\ASUS\Downloads\ai-devops-sre
```

---

## Step 3: Start the Backend Server

```powershell
python -m uvicorn src.app:app --reload --app-dir .
```

Wait until you see:
```
"Loaded knowledge base with 200+ entries"
"Application startup complete."
Uvicorn running on http://127.0.0.1:8000
```

**Leave this window open.**

---

## Step 4: Start the Streamlit UI (Optional)

Open a **second PowerShell window** (keep first one running):

```powershell
cd C:\Users\ASUS\Downloads\ai-devops-sre
streamlit run streamlit_app.py
```

Your browser will open automatically at:
```
http://localhost:8501
```

---

## Quick Test (Browser)

Open Chrome/Edge and go to:
```
http://localhost:8000/docs
```

Or test knowledge base:
```
http://localhost:8000/knowledge-base/search?query=pod+crash&top_k=3
```

---

## Quick Test (PowerShell)

In a **third PowerShell window**:

```powershell
cd C:\Users\ASUS\Downloads\ai-devops-sre
python test_analyze.py
```

---

## Common Issues After Restart

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `0 entries` in KB | Run `python ingest_docs.py --persist-dir "./data/chroma_db"` |
| Port 8000 in use | Kill old process: `taskkill /f /im python.exe` then restart |
| Streamlit not found | Run `pip install streamlit pandas` |

---

## One-Line Health Check

```powershell
python -c "import requests; print(requests.get('http://localhost:8000/health').json())"
```

Should return:
```json
{"status": "healthy", "version": "1.0.0"}
```

---

## Shutdown

1. Press `Ctrl + C` in the UI terminal (stops Streamlit)
2. Press `Ctrl + C` in the server terminal (stops FastAPI)
3. Close PowerShell windows

---

## File Checklist (Keep These)

| File | Purpose |
|------|---------|
| `src/app.py` | FastAPI server |
| `src/rag/knowledge_base.py` | Vector store |
| `src/ml/training/error_classifier.py` | ML classifier |
| `main.py` | Core engine |
| `ingest_docs.py` | KB ingestion |
| `streamlit_app.py` | Web UI |
| `docs/` | Source documents |
| `data/chroma_db/` | Vector database |
| `data/models/error_classifier.pkl` | Trained model |
| `training_data.json` | Training samples |
