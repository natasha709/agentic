"""
Unit tests for ConversationMemory in agent.py
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestConversationMemory:
    """Tests for the ConversationMemory class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('agent.load_dotenv'):
            from agent import ConversationMemory
            self.memory = ConversationMemory()
    
    def test_initialization(self):
        """Test ConversationMemory initializes correctly"""
        assert self.memory is not None
        assert hasattr(self.memory, 'threads')
        assert isinstance(self.memory.threads, dict)
    
    def test_add_message_to_thread(self):
        """Test adding messages to a thread"""
        thread_id = "test_thread_1"
        
        # Add user message
        self.memory.add_message(thread_id, "user", "Hello, I need help")
        
        # Add bot message
        self.memory.add_message(thread_id, "bot", "Hello! How can I assist you?")
        
        # Verify messages were added
        messages = self.memory.get_messages(thread_id)
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "bot"
    
    def test_get_messages_empty_thread(self):
        """Test getting messages from non-existent thread returns empty list"""
        messages = self.memory.get_messages("non_existent_thread")
        assert messages == []
    
    def test_clear_thread(self):
        """Test clearing a thread's messages"""
        thread_id = "test_thread_2"
        
        # Add messages
        self.memory.add_message(thread_id, "user", "Test message")
        
        # Verify messages exist
        assert len(self.memory.get_messages(thread_id)) > 0
        
        # Clear thread
        self.memory.clear_thread(thread_id)
        
        # Verify messages are cleared
        assert len(self.memory.get_messages(thread_id)) == 0
    
    def test_multiple_threads(self):
        """Test multiple threads work independently"""
        thread1 = "thread_1"
        thread2 = "thread_2"
        
        self.memory.add_message(thread1, "user", "Message in thread 1")
        self.memory.add_message(thread2, "user", "Message in thread 2")
        
        messages1 = self.memory.get_messages(thread1)
        messages2 = self.memory.get_messages(thread2)
        
        assert len(messages1) == 1
        assert len(messages2) == 1
        assert messages1[0]["content"] == "Message in thread 1"
        assert messages2[0]["content"] == "Message in thread 2"
    
    def test_message_format(self):
        """Test message format includes role and content"""
        thread_id = "test_thread_3"
        self.memory.add_message(thread_id, "user", "Test message")
        
        messages = self.memory.get_messages(thread_id)
        message = messages[0]
        
        assert "role" in message
        assert "content" in message
        assert message["role"] == "user"
        assert message["content"] == "Test message"
