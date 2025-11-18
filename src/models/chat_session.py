"""
Chat Session Model
Stores conversation history for character chats
"""
from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.sql import func
from src.models.database import Base
import json


class ChatSession(Base):
    """Store chat conversation history"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)  # Format: {document_id}_{character_id}
    document_id = Column(String(255), index=True, nullable=False)
    character_id = Column(String(255), index=True, nullable=False)
    character_name = Column(String(255), nullable=False)
    conversation_history = Column(Text, nullable=False, default="[]")  # JSON string of messages
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    def get_messages(self):
        """Parse conversation history JSON"""
        try:
            return json.loads(self.conversation_history)
        except:
            return []
    
    def set_messages(self, messages: list):
        """Store messages as JSON"""
        self.conversation_history = json.dumps(messages)
