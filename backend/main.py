from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import os
from datetime import datetime

from ai_service import generate_chart_code, generate_chat_response
from execution_engine import execute_and_capture_chart

app = FastAPI(title="Real Estate Data Visualizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    prompt: str

class ChatRequest(BaseModel):
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

class ModifyRequest(BaseModel):
    current_code: str
    prompt: str

class ExplainRequest(BaseModel):
    image_base64: str

@app.post("/api/ai/generate")
async def api_generate(request: GenerateRequest):
    try:
        return generate_chart_code(request.prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/modify")
async def api_modify(request: ModifyRequest):
    try:
        from ai_service import modify_chart_code
        return modify_chart_code(request.current_code, request.prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/chat")
async def api_chat(request: ChatRequest):
    try:
        content = generate_chat_response(request.prompt)
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/execute")
async def api_execute(request: ExecuteRequest):
    result = execute_and_capture_chart(request.code, request.dataset_path)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["error"])
    return {"image_base64": result["image"]}

@app.post("/api/ai/explain")
async def api_explain(request: ExplainRequest):
    try:
        from ai_service import explain_chart_vision
        explanation = explain_chart_vision(request.image_base64)
        return {"explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/logs")
async def api_log(request: LogRequest):
    log_entry = {"timestamp": datetime.now().isoformat(), **request.dict()}
    log_path = "../logs/system_logs.json"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logs = []
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            try: logs = json.load(f)
            except: pass
    logs.append(log_entry)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)
    return {"status": "ok"}