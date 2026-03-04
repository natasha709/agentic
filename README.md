# Sentinel AI - Agentic IT Support Assistant

An intelligent AI-powered IT support assistant that uses multi-step reasoning, RAG (Retrieval-Augmented Generation), and safety controls to help troubleshoot common IT issues.

##  Features

- **Multi-step Reasoning**: LangGraph-powered agent with stateful conversation flow
- **RAG Knowledge Base**: ChromaDB/FAISS vector database for retrieving relevant runbooks and guides
- **Tool Execution**: Automated tools for server metrics, service restarts, and knowledge search
- **Memory Persistence**: Conversation history and context retention
- **Safety Controls**: Request confirmation and input validation before dangerous operations
- **Real-time Observability**: Detailed reasoning logs showing agent thought process
- **Modern UI**: React frontend with smooth animations and intuitive interface

##  Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **LangGraph** - Agent orchestration with state management
- **Google GenAI** - LLM for natural language understanding
- **ChromaDB** - Vector database for RAG
- **FAISS** - Similarity search
- **Pydantic** - Data validation

### Frontend
- **React 19** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Framer Motion** - Animations
- **Lucide React** - Icons

##  Prerequisites

- Python 3.10+
- Node.js 18+
- Google AI API key (Gemini)

##  Installation

### 1. Clone the repository

```bash
cd agentic
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate 
# source venv/bin/activate  

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with your API keys
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

##  Configuration

### Backend Environment Variables (backend/.env)

Create a `.env` file in the `backend` directory:

```env
# Required: Google AI API Key (get from https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=your_google_api_key_here

# Optional: Enable mock mode for testing without API
USE_MOCK_MODE=false
```

> ** Important**: Make sure your API key is valid and has the Gemini API enabled. If the key is invalid or the API is not enabled, the system will fall back to mock mode.

### Frontend Configuration

The frontend connects to `http://localhost:8000` by default. To change this, update the API URL in [`frontend/src/App.tsx`](frontend/src/App.tsx).

##  Running the Application

### Start Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### Start Frontend

```bash
cd frontend
npm run dev
```

The application will open at `http://localhost:5173`

##  Troubleshooting

### Issue: Only Getting Mock Responses

If you're seeing responses like:
> "I understand you're asking about: '...'. As Sentinel AI, I would help you troubleshoot this IT issue..."

This means the real AI is failing and falling back to mock mode. Here's how to fix it:

1. **Check if GEMINI_API_KEY is set correctly:**
   ```bash
   # In backend/.env file, ensure you have:
   GEMINI_API_KEY=your_actual_api_key_here
   ```

2. **Get a valid API key:**
   - Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create a new API key
   - Make sure the Gemini API is enabled in your Google Cloud Console

3. **Verify the backend is loading the key:**
   - Check the backend console for debug output
   - Look for: `DEBUG: API Key exists: True`

4. **Restart the backend after changing .env:**
   ```bash
   # Stop the current backend (Ctrl+C)
   # Restart it:
   uvicorn main:app --reload --port 8000
   ```

5. **Check for model compatibility:**
   - The current model is `gemini-2.5-flash`
   - If you see model errors, try changing to `gemini-1.5-flash` in `backend/agent.py`

### Issue: CORS Errors

If you see CORS errors in the browser console, make sure:
- The backend is running on port 8000
- The frontend is configured to connect to `http://localhost:8000`

##  Project Structure

```
agentic/
├── backend/
│   ├── .env                 # Environment variables
│   ├── agent.py             # LangGraph agent logic
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── data/
│       └── runbooks/        # Knowledge base documents
│           ├── vpn_guide.md
│           └── website_guide.md
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main React component
│   │   ├── main.tsx         # Entry point
│   │   └── index.css         # Global styles
│   ├── package.json         # Node dependencies
│   └── vite.config.ts       # Vite configuration
├── README.md                # This file
└── TODO.md                  # Development tasks
```

## API Endpoints

### POST /chat
Send a message to the AI assistant.

**Request:**
```json
{
  "message": "How do I setup VPN?",
  "thread_id": "optional-session-id"
}
```

**Response:**
```json
{
  "response": "AI response text",
  "status": "success",
  "logs": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "category": "THOUGHT",
      "message": "User is asking about VPN setup",
      "status": "success"
    }
  ],
  "session": {
    "thread_id": "session-id",
    "conversation_summary": "..."
  },
  "requires_confirmation": false,
  "tool_result": null
}
```

### GET /status
Check the backend status and whether mock mode is enabled.

**Response:**
```json
{
  "status": "Sentinel AI Core Online",
  "mock_mode": "false"
}
```

### POST /confirm
Confirm a pending tool execution.

**Request:**
```json
{
  "thread_id": "session-id",
  "confirmed": true
}
```

##  Available Tools

The agent has access to the following tools:

- **search_runbooks**: Search the knowledge base for relevant guides
- **get_server_metrics**: Retrieve current server performance metrics
- **restart_service**: Restart a specific system service (requires confirmation)

##  Knowledge Base

Add markdown files to [`backend/data/runbooks/`](backend/data/runbooks/) to expand the AI's knowledge. The RAG system will automatically index these documents.

Example runbooks included:
- VPN Setup Guide
- Website Troubleshooting Guide

##  Safety Features

- **Confirmation Required**: Dangerous operations (like service restarts) require explicit user confirmation
- **Input Validation**: All user inputs are validated and sanitized
- **Rate Limiting**: API endpoints have basic rate limiting
- **Error Handling**: Comprehensive error handling with user-friendly messages

##  Development

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Adding New Tools
1. Define the tool function in [`backend/agent.py`](backend/agent.py)
2. Add it to the tools list
3. Update the agent graph if needed

##  License

MIT License

##  Acknowledgments

- [LangGraph](https://langchain-ai.github.io/langgraph/) - Agent orchestration
- [Google AI](https://ai.google/) - LLM powered by Gemini
- [FastAPI](https://fastapi.tiangolo.com/) - Python web framework
- [React](https://react.dev/) - UI library

# Sentinel AI - Agentic IT Support Assistant

An intelligent AI-powered IT support assistant that uses multi-step reasoning, RAG (Retrieval-Augmented Generation), and safety controls to help troubleshoot common IT issues.

##  Features

- **Multi-step Reasoning**: LangGraph-powered agent with stateful conversation flow
- **RAG Knowledge Base**: ChromaDB/FAISS vector database for retrieving relevant runbooks and guides
- **Tool Execution**: Automated tools for server metrics, service restarts, and knowledge search
- **Memory Persistence**: Conversation history and context retention
- **Safety Controls**: Request confirmation and input validation before dangerous operations
- **Real-time Observability**: Detailed reasoning logs showing agent thought process
- **Modern UI**: React frontend with smooth animations and intuitive interface

##  Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **LangGraph** - Agent orchestration with state management
- **Google GenAI** - LLM for natural language understanding
- **ChromaDB** - Vector database for RAG
- **FAISS** - Similarity search
- **Pydantic** - Data validation

### Frontend
- **React 19** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Framer Motion** - Animations
- **Lucide React** - Icons

##  Prerequisites

- Python 3.10+
- Node.js 18+
- Google AI API key (Gemini)

##  Installation

### 1. Clone the repository

```bash
cd agentic
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  
# source venv/bin/activate 

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with your API keys
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
```

##  Configuration

### Backend Environment Variables (backend/.env)

Create a `.env` file in the `backend` directory:

```env
# Required: Google AI API Key
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Configuration
AGENT_MODEL=gemini-2.0-flash
EMBEDDING_MODEL=gemini-embedding-001
```

### Frontend Configuration

The frontend connects to `http://localhost:8000` by default. To change this, update the API URL in [`frontend/src/App.tsx`](frontend/src/App.tsx).

##  Running the Application

### Start Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### Start Frontend

```bash
cd frontend
npm run dev
```

The application will open at `http://localhost:5173`

##  Project Structure

```
agentic/
├── backend/
│   ├── .env                 # Environment variables
│   ├── agent.py             # LangGraph agent logic
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── data/
│       └── runbooks/        # Knowledge base documents
│           ├── vpn_guide.md
│           └── website_guide.md
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main React component
│   │   ├── main.tsx         # Entry point
│   │   └── index.css         # Global styles
│   ├── package.json         # Node dependencies
│   └── vite.config.ts       # Vite configuration
├── README.md                # This file
└── TODO.md                  # Development tasks
```

##  API Endpoints

### POST /chat
Send a message to the AI assistant.

**Request:**
```json
{
  "message": "How do I setup VPN?",
  "conversation_id": "optional-session-id"
}
```

**Response:**
```json
{
  "response": "AI response text",
  "conversation_id": "session-id",
  "logs": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "category": "THOUGHT",
      "message": "User is asking about VPN setup",
      "status": "success"
    }
  ],
  "requires_confirmation": false,
  "tool_result": null
}
```

### POST /confirm
Confirm a pending tool execution.

**Request:**
```json
{
  "conversation_id": "session-id",
  "confirmed": true
}
```

### WebSocket /ws/chat
Real-time streaming chat (optional enhancement).

##  Available Tools

The agent has access to the following tools:

- **search_runbooks**: Search the knowledge base for relevant guides
- **get_server_metrics**: Retrieve current server performance metrics
- **restart_service**: Restart a specific system service (requires confirmation)

##  Knowledge Base

Add markdown files to [`backend/data/runbooks/`](backend/data/runbooks/) to expand the AI's knowledge. The RAG system will automatically index these documents.

Example runbooks included:
- VPN Setup Guide
- Website Troubleshooting Guide

##  Safety Features

- **Confirmation Required**: Dangerous operations (like service restarts) require explicit user confirmation
- **Input Validation**: All user inputs are validated and sanitized
- **Rate Limiting**: API endpoints have basic rate limiting
- **Error Handling**: Comprehensive error handling with user-friendly messages

##  Development

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Adding New Tools
1. Define the tool function in [`backend/agent.py`](backend/agent.py)
2. Add it to the tools list
3. Update the agent graph if needed

##  License

MIT License

##  Acknowledgments

- [LangGraph](https://langchain-ai.github.io/langgraph/) - Agent orchestration
- [Google AI](https://ai.google/) - LLM powered by Gemini
- [FastAPI](https://fastapi.tiangolo.com/) - Python web framework
- [React](https://react.dev/) - UI library
