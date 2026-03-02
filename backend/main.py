import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import asyncio

from agent import app as agent_app, add_reasoning_log, get_reasoning_logs, clear_reasoning_logs
from langchain_core.messages import HumanMessage, AIMessage

app = FastAPI(title="Sentinel AI Support Backend")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    thread_id: str

@app.get("/")
async def root():
    return {"status": "Sentinel AI Core Online", "version": "1.0.4"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # Clear previous reasoning logs
    clear_reasoning_logs()
    
    # Check for API Key
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return {"response": "Error: GEMINI_API_KEY not found. Please add it to the .env file.", "status": "error", "logs": []}

    # Call the real LangGraph agent
    try:
        from langchain_core.messages import HumanMessage
        config = {"configurable": {"thread_id": request.thread_id}}
        
        add_reasoning_log("SYSTEM", f"Starting agent with query: '{request.message}'", "processing")
        
        # Invoke the graph
        # This will return the final state after the recursion
        result = agent_app.invoke({"messages": [HumanMessage(content=request.message)]}, config)
        
        # Extract logs from the result
        final_answer = result["messages"][-1].content
        
        # Get detailed reasoning logs from the agent
        reasoning_logs = get_reasoning_logs()
        
        # Add final summary log
        final_log = {
            "label": "SYSTEM",
            "message": f"Agent completed. Graph traversed through {len(result['messages'])} nodes.",
            "status": "success"
        }
        
        return {
            "response": final_answer,
            "status": "success",
            "logs": reasoning_logs + [final_log]
        }
    except Exception as e:
        error_log = {
            "label": "ERROR",
            "message": f"Agent execution failed: {str(e)}",
            "status": "error"
        }
        return {"response": f"Agent Logic Error: {str(e)}", "status": "error", "logs": [error_log]}

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        msg = json.loads(data)
        
        # Real-time streaming of agent steps would go here
        await websocket.send_json({"type": "log", "content": "Initializing reasoning loop..."})
        await asyncio.sleep(0.5)
        
        # Simulate tool calls
        await websocket.send_json({"type": "log", "content": "Searching IT runbooks..."})
        await asyncio.sleep(1)
        
        await websocket.send_json({"type": "message", "content": "I've checked the manuals. Please try restarting your VPN client first."})

@app.get("/metrics")
async def get_metrics():
    """Get real system metrics"""
    import psutil
    
    return {
        "cpu": psutil.cpu_percent(interval=0.1),
        "memory": f"{psutil.virtual_memory().used / (1024**3):.1f}GB/{psutil.virtual_memory().total / (1024**3):.1f}GB",
        "memory_percent": psutil.virtual_memory().percent
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
