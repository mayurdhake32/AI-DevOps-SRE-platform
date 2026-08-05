"""FastAPI Web Application for AI DevOps SRE"""
import os
import json
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from main import AIDevOpsSRE
from src.utils.logger import get_logger

from dotenv import load_dotenv
load_dotenv()  # Add this at the very top of main.py and app.py

logger = get_logger(__name__)

app = FastAPI(
    title="AI DevOps SRE",
    description="AI-powered Site Reliability Engineering Agent",
    version="1.0.0"
)

sre_engine: Optional[AIDevOpsSRE] = None

class LogAnalysisRequest(BaseModel):
    log_content: str
    repo_name: str
    platform: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PredictionRequest(BaseModel):
    deployment_info: Dict[str, Any]

class TrainingRequest(BaseModel):
    logs: Optional[list] = None
    deployments: Optional[list] = None

@app.on_event("startup")
async def startup():
    global sre_engine
    sre_engine = AIDevOpsSRE()
    logger.info("AI DevOps SRE engine initialized")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "version": "1.0.0"}

@app.post("/analyze")
async def analyze_logs(request: LogAnalysisRequest, background_tasks: BackgroundTasks):
    if not sre_engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    result = sre_engine.process_failed_deployment(
        log_content=request.log_content,
        repo_name=request.repo_name,
        repo_context=request.metadata
    )
    return JSONResponse(content=result)

@app.post("/predict")
async def predict_failure(request: PredictionRequest):
    if not sre_engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    prediction = sre_engine.predict_failure(request.deployment_info)
    return JSONResponse(content=prediction)

@app.post("/train")
async def train_models(request: TrainingRequest):
    if not sre_engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    results = sre_engine.train_models(
        logs=request.logs or [],
        deployments=request.deployments or []
    )
    return JSONResponse(content=results)

@app.post("/webhook/github")
async def github_webhook(request: Request):
    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event", "")
    logger.info(f"Received GitHub webhook: {event_type}")
    if event_type == "workflow_run" and payload.get("action") == "completed":
        workflow_run = payload.get("workflow_run", {})
        if workflow_run.get("conclusion") == "failure":
            repo_name = payload.get("repository", {}).get("full_name")
            logger.info(f"Failed workflow detected: {repo_name}")
            return {
                "status": "processing", "repo": repo_name,
                "workflow": workflow_run.get("name"), "run_id": workflow_run.get("id")
            }
    return {"status": "ignored", "event": event_type}

@app.get("/knowledge-base/search")
async def search_knowledge(query: str, category: Optional[str] = None, top_k: int = 5):
    if not sre_engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    results = sre_engine.knowledge_base.query(query, category, top_k)
    return JSONResponse(content={"results": results})

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)