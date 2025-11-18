"""
Chat Session Service
Handles saving and loading conversation history
"""
from sqlalchemy.orm import Session
from src.models.chat_session import ChatSession
from typing import List, Dict, Optional


class ChatSessionService:
    """Manage chat session persistence"""
    
    @staticmethod
    def get_or_create_session(
        db: Session,
        document_id: str,
        character_id: str,
        character_name: str
    ) -> ChatSession:
        """Get existing session or create new one"""
        session_id = f"{document_id}_{character_id}"
        
        # Try to find existing session
        chat_session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if not chat_session:
            # Create new session
            chat_session = ChatSession(
                session_id=session_id,
                document_id=document_id,
                character_id=character_id,
                character_name=character_name,
                conversation_history="[]"
            )
            db.add(chat_session)
            db.commit()
            db.refresh(chat_session)
        
        return chat_session
    
    @staticmethod
    def get_conversation_history(
        db: Session,
        document_id: str,
        character_id: str
    ) -> List[Dict[str, str]]:
        """Load conversation history for a character"""
        session_id = f"{document_id}_{character_id}"
        
        chat_session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if chat_session:
            return chat_session.get_messages()
        return []
    
    @staticmethod
    def save_message(
        db: Session,
        document_id: str,
        character_id: str,
        character_name: str,
        user_message: str,
        assistant_response: str
    ) -> ChatSession:
        """Save a message exchange to history"""
        chat_session = ChatSessionService.get_or_create_session(
            db, document_id, character_id, character_name
        )
        
        # Get current history
        messages = chat_session.get_messages()
        
        # Add new messages
        messages.append({"role": "user", "content": user_message})
        messages.append({"role": "assistant", "content": assistant_response})
        
        # Save updated history
        chat_session.set_messages(messages)
        db.commit()
        db.refresh(chat_session)
        
        return chat_session
    
    @staticmethod
    def clear_session(
        db: Session,
        document_id: str,
        character_id: str
    ) -> bool:
        """Clear conversation history for a character"""
        session_id = f"{document_id}_{character_id}"
        
        chat_session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if chat_session:
            db.delete(chat_session)
            db.commit()
            return True
        return False
    
    @staticmethod
    def get_all_sessions_for_document(
        db: Session,
        document_id: str
    ) -> List[ChatSession]:
        """Get all chat sessions for a document"""
        return db.query(ChatSession).filter(
            ChatSession.document_id == document_id
        ).all()
