"""
API tests for main.py FastAPI endpoints
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient


# Mock the agent imports before importing main
with patch('main.load_dotenv'):
    with patch('main.agent_app'):
        with patch('main.logger'):
            with patch('main.memory'):
                with patch('main.safety'):
                    with patch('main.ObservabilityLogger'):
                        with patch('main.ConversationMemory'):
                            with patch('main.SafetyController'):
                                with patch('main.HumanMessage'):
                                    from main import app


client = TestClient(app)


class TestRootEndpoint:
    """Tests for the root / endpoint"""
    
    def test_root_returns_status(self):
        """Test root endpoint returns system status"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "message" in data


class TestHealthEndpoint:
    """Tests for the /health endpoint"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestChatEndpoint:
    """Tests for the /chat endpoint"""
    
    @patch('main.agent_app')
    def test_chat_with_valid_message(self, mock_agent):
        """Test chat endpoint with valid message"""
        # Mock the async agent invoke
        mock_agent.invoke = AsyncMock(return_value={
            "messages": [
                {"type": "ai", "content": "Test response"}
            ]
        })
        
        response = client.post("/chat", json={
            "message": "Hello, I need help",
            "thread_id": "test_thread"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data or "messages" in data
    
    def test_chat_without_message(self):
        """Test chat endpoint without message returns error"""
        response = client.post("/chat", json={
            "thread_id": "test_thread"
        })
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_chat_with_empty_message(self):
        """Test chat endpoint with empty message"""
        response = client.post("/chat", json={
            "message": "",
            "thread_id": "test_thread"
        })
        
        # Should return validation error (empty string)
        assert response.status_code == 422


class TestConfirmEndpoint:
    """Tests for the /confirm endpoint"""
    
    @patch('main.agent_app')
    def test_confirm_approval(self, mock_agent):
        """Test confirmation with approved=True"""
        mock_agent.invoke = AsyncMock(return_value={
            "messages": [
                {"type": "ai", "content": "Action approved"}
            ]
        })
        
        response = client.post("/confirm", json={
            "thread_id": "test_thread",
            "tool_name": "create_ticket",
            "approved": True,
            "parameters": {
                "title": "Test",
                "description": "Test ticket"
            }
        })
        
        assert response.status_code == 200
    
    @patch('main.agent_app')
    def test_confirm_rejection(self, mock_agent):
        """Test confirmation with approved=False"""
        mock_agent.invoke = AsyncMock(return_value={
            "messages": [
                {"type": "ai", "content": "Action cancelled"}
            ]
        })
        
        response = client.post("/confirm", json={
            "thread_id": "test_thread",
            "tool_name": "restart_service",
            "approved": False,
            "parameters": {
                "service_name": "nginx"
            }
        })
        
        assert response.status_code == 200


class TestMemoryEndpoint:
    """Tests for the /memory endpoint"""
    
    @patch('main.memory')
    def test_get_memory(self, mock_memory):
        """Test getting memory for a thread"""
        mock_memory.get_messages = MagicMock(return_value=[
            {"role": "user", "content": "Hello"},
            {"role": "bot", "content": "Hi there!"}
        ])
        
        response = client.get("/memory/test_thread")
        
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
    
    @patch('main.memory')
    def test_clear_memory(self, mock_memory):
        """Test clearing memory for a thread"""
        mock_memory.clear_thread = MagicMock()
        
        response = client.delete("/memory/test_thread")
        
        assert response.status_code == 200
        mock_memory.clear_thread.assert_called_once_with("test_thread")


class TestMetricsEndpoint:
    """Tests for the /metrics endpoint"""
    
    def test_metrics_returns_data(self):
        """Test metrics endpoint returns system metrics"""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        data = response.json()
        # Metrics should contain some system information
        assert isinstance(data, dict)
