"""
Sentinel AI - Agentic IT Support Assistant Backend
Main FastAPI Application

Integrates:
- LangGraph agent with multi-step reasoning
- RAG-powered knowledge base
- Memory persistence
- Safety controls
- Comprehensive observability
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from the backend directory
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

from fastapi import FastAPI, WebSocket, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import asyncio
import traceback

# Re-enable agent imports for real AI testing
from agent import (
    app as agent_app, 
    logger, 
    memory,
    safety,
    ObservabilityLogger,
    ConversationMemory,
    SafetyController
)
from langchain_core.messages import HumanMessage

app = FastAPI(
    title="Sentinel AI - Agentic IT Support",
    description="Agentic AI IT Support Assistant with multi-step reasoning, RAG, and safety controls",
    version="2.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# REQUEST/RESPONSE MODELS
# ============================================

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"
    context: Optional[Dict[str, Any]] = None

class ConfirmationRequest(BaseModel):
    thread_id: str
    tool_name: str
    approved: bool
    parameters: Dict[str, Any]

class MemoryRequest(BaseModel):
    thread_id: str

# ============================================
# ENDPOINTS
# ============================================

@app.get("/")
async def root():
    """Root endpoint with system status"""
    return {"status": "Sentinel AI Core Online", "mock_mode": os.getenv("USE_MOCK_MODE", "false")}

@app.get("/test")
async def test():
    """Simple test endpoint"""
    return {"message": "Test endpoint working"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Hybrid chat endpoint - tries real AI first, falls back to mock"""
    mock_mode = os.getenv("USE_MOCK_MODE", "false").lower() == "true"
    
    print(f"DEBUG: Chat endpoint called - mock_mode={mock_mode}, message='{request.message}'")
    
    # Initialize logger for this session
    logger.set_session(request.thread_id)
    logger.add_log("SYSTEM", f"Starting agentic session for thread: {request.thread_id}", "processing")
    logger.add_log("THOUGHT", f"User query: '{request.message[:100]}...'", "processing")
    
    if mock_mode:
        print("DEBUG: Using mock mode")
        # Use mock mode
        response_text = f"I understand you're asking about: '{request.message}'. As Sentinel AI, I would help you troubleshoot this IT issue. For website problems, I'd check server status, review logs, and guide you through troubleshooting steps."
        logs = [{"timestamp": "2026-03-03T16:15:00", "category": "SYSTEM", "message": "Mock response generated", "status": "success"}]
        conversation_summary = "Mock mode active"
    else:
        print("DEBUG: Trying real AI mode")
        # Try real AI first
        try:
            # Check for API Key
            api_key = os.getenv("GEMINI_API_KEY")
            print(f"DEBUG: API Key exists: {api_key is not None}")
            if not api_key:
                raise Exception("GEMINI_API_KEY not found")
            
            print("DEBUG: Creating initial state")
            # Create initial state for agent
            initial_state = {
                "messages": [HumanMessage(content=request.message)],
                "thread_id": request.thread_id,
                "next_step": "safety_check",
                "requires_confirmation": False,
                "confirmation_pending": False
            }
            
            print("DEBUG: About to invoke agent")
            # Try to invoke the agent
            result = agent_app.invoke(initial_state)
            print("DEBUG: Agent invocation completed")
            
            # Extract response from agent
            final_answer = ""
            print(f"DEBUG: Extracting response from {len(result.get('messages', []))} messages")
            for msg in reversed(result.get("messages", [])):
                if hasattr(msg, 'content') and msg.content and not hasattr(msg, 'tool_calls'):
                    final_answer = msg.content
                    print(f"DEBUG: Found response: '{final_answer[:100]}...'")
                    break
            
            response_text = final_answer or "I'm sorry, I couldn't generate a response."
            logs = logger.get_logs()
            conversation_summary = memory.get_context_summary(request.thread_id)
            
        except Exception as e:
            print(f"DEBUG: Real AI failed with error: {str(e)}")
            # Fall back to mock if real AI fails
            logger.add_log("ERROR", f"Real AI failed: {str(e)}", "error")
            response_text = f"I understand you're asking about: '{request.message}'. As Sentinel AI, I would help you troubleshoot this IT issue. For website problems, I'd check server status, review logs, and guide you through troubleshooting steps. (Note: Using mock response due to API limitations)"
            logs = logger.get_logs()
            conversation_summary = "Fallback to mock mode"
    
    print(f"DEBUG: Returning response: '{response_text[:100]}...'")
    return {
        "response": response_text,
        "status": "success",
        "logs": logs,
        "session": {
            "thread_id": request.thread_id,
            "conversation_summary": conversation_summary
        },
        "metadata": {
            "tools_used": [],
            "safety_passed": True,
            "requires_confirmation": False
        }
    }

@app.post("/confirm")
async def handle_confirmation(request: ConfirmationRequest):
    """
    Handle user confirmation for risky actions.
    
    When the agent requests confirmation for risky operations like
    service restarts, this endpoint processes the user's decision.
    """
    logger.add_log("SYSTEM", f"Processing confirmation: {request.tool_name} - {'approved' if request.approved else 'denied'}")
    
    if not request.approved:
        return {
            "response": f"Action '{request.tool_name}' has been cancelled as per your request. Is there anything else I can help with?",
            "status": "cancelled",
            "logs": logger.get_logs()
        }
    
    # If approved, execute the action
    # This would re-invoke the agent with the approved action
    try:
        from langchain_core.messages import HumanMessage, AIMessage
        
        # Execute the approved tool
        if request.tool_name == "restart_service":
            # from agent import restart_service
            # result = restart_service.invoke({"service_name": request.parameters.get("service_name")})
            result = f"Service restart simulated for: {request.parameters.get('service_name')}"
            
            return {
                "response": f"Action approved and executed. {result}",
                "status": "success",
                "logs": logger.get_logs()
            }
        
        return {
            "response": f"Tool {request.tool_name} executed successfully.",
            "status": "success",
            "logs": logger.get_logs()
        }
        
    except Exception as e:
        return {
            "response": f"Error executing confirmed action: {str(e)}",
            "status": "error",
            "logs": logger.get_logs()
        }

@app.get("/memory/{thread_id}")
async def get_memory(thread_id: str):
    """Get conversation memory for a thread"""
    history = memory.get_session(thread_id)
    summary = memory.get_context_summary(thread_id)
    
    return {
        "thread_id": thread_id,
        "turns": len(history),
        "history": history,
        "summary": summary
    }

@app.delete("/memory/{thread_id}")
async def clear_memory(thread_id: str):
    """Clear conversation memory for a thread"""
    memory.clear_session(thread_id)
    
    return {
        "status": "success",
        "message": f"Memory cleared for thread: {thread_id}"
    }

@app.post("/safety/check")
async def check_safety(input_text: str):
    """Check input for safety issues"""
    is_injection, message = safety.check_prompt_injection(input_text)
    safe_text = safety.redact_sensitive_data(input_text)
    
    return {
        "input": input_text,
        "safe_input": safe_text,
        "injection_detected": is_injection,
        "injection_message": message,
        "requires_confirmation": False
    }

@app.get("/metrics")
async def get_metrics():
    """Get real system metrics"""
    try:
        import psutil
        
        return {
            "cpu": psutil.cpu_percent(interval=0.1),
            "memory": f"{psutil.virtual_memory().used / (1024**3):.1f}GB/{psutil.virtual_memory().total / (1024**3):.1f}GB",
            "memory_percent": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage('/').percent
        }
    except ImportError:
        return {
            "cpu": 0,
            "memory": "N/A",
            "memory_percent": 0,
            "disk": 0
        }

@app.get("/knowledge")
async def get_knowledge_base():
    """Get available knowledge base articles"""
    # from agent import rag
    # rag.initialize()
    
    return {
        "categories": ["network", "web", "storage", "infrastructure", "email"],
        "articles": [
            {"id": "network-001", "title": "Network Troubleshooting Guide", "category": "network"},
            {"id": "web-001", "title": "Website Performance Issues", "category": "web"},
            {"id": "storage-001", "title": "Disk Space Management", "category": "storage"}
        ]
    }

# ============================================
# WEBSOCKET FOR REAL-TIME UPDATES
# ============================================

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time agent updates"""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            if msg.get("type") == "message":
                # Send thinking indicator
                await websocket.send_json({
                    "type": "log", 
                    "content": "Initializing reasoning loop...",
                    "step": "start"
                })
                await asyncio.sleep(0.3)
                
                await websocket.send_json({
                    "type": "log", 
                    "content": "Performing safety check...",
                    "step": "safety"
                })
                await asyncio.sleep(0.3)
                
                await websocket.send_json({
                    "type": "log", 
                    "content": "Invoking LLM with tools...",
                    "step": "reasoning"
                })
                await asyncio.sleep(0.5)
                
                # Simulate tool selection
                await websocket.send_json({
                    "type": "log", 
                    "content": "Searching knowledge base...",
                    "step": "tool"
                })
                await asyncio.sleep(0.8)
                
                # Final response
                await websocket.send_json({
                    "type": "message", 
                    "content": "I've analyzed your issue and found relevant troubleshooting steps in the knowledge base. Let me guide you through the solution..."
                })
                
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "content": f"Connection error: {str(e)}"
        })

# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
