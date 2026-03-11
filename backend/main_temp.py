@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time agent updates"""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            if msg.get("type") == "message":
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
                
            
                await websocket.send_json({
                    "type": "log", 
                    "content": "Searching knowledge base...",
                    "step": "tool"
                })
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
