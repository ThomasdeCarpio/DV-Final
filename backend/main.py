from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import os
from datetime import datetime

# Import custom modules
from ai_service import generate_chart_code
from execution_engine import execute_and_capture_chart

app = FastAPI(title="Real Estate Data Visualizer API")

# Allow Streamlit (Frontend) to talk to FastAPI (Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PYDANTIC MODELS (Data Validation) ---
class GenerateRequest(BaseModel):
    prompt: str

class ExecuteRequest(BaseModel):
    code: str
    dataset_path: str = "../data/cleaned_vietnam_real_estates.csv"

class LogRequest(BaseModel):
    prompt: str
    original_code: str
    edited_code: str
    status: str
    error_message: Optional[str] = None

# --- API 1: AI GENERATOR ---
@app.post("/api/ai/generate")
async def api_generate(request: GenerateRequest):
    try:
        response = generate_chart_code(request.prompt)
        return response # Returns dict with "explanation" and "code"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- API 2: EXECUTION ENGINE ---
@app.post("/api/execute")
async def api_execute(request: ExecuteRequest):
    result = execute_and_capture_chart(request.code, request.dataset_path)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])
    return {"image_base64": result["image"]}

# --- API 3: SYSTEM LOGGER ---
@app.post("/api/logs")
async def api_log(request: LogRequest):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "prompt": request.prompt,
        "original_code": request.original_code,
        "edited_code": request.edited_code,
        "status": request.status,
        "error_message": request.error_message
    }
    
    log_path = "../logs/system_logs.json"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    logs = []
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            try:
                logs = json.load(f)
            except:
                pass
                
    logs.append(log_entry)
    
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)
        
    return {"message": "Log saved successfully"}