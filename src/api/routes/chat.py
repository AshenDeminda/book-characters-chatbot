"""
Chat API Endpoints
Handles character conversations
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from pathlib import Path
import json

from src.services.chat_service import ChatService
from src.services.character_service import CharacterService
from src.config import settings

router = APIRouter()
chat_service = ChatService()
character_service = CharacterService()

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    document_id: str
    character_id: str
    message: str
    conversation_history: Optional[List[ChatMessage]] = None

class ChatResponse(BaseModel):
    status: str
    character_name: str
    response: str
    context_chunks_used: int
    relevant_context: Optional[List[Dict]] = None

class GreetingRequest(BaseModel):
    document_id: str
    character_id: str

@router.post("/chat", response_model=ChatResponse)
async def chat_with_character(request: ChatRequest):
    """
    Chat with a character from an uploaded book
    Uses RAG to retrieve relevant story context
    """
    # Load character from previous extraction
    # In production, this should be from database
    # For now, we'll extract it on the fly
    
    upload_dir = Path(settings.UPLOAD_DIR)
    chunks_path = upload_dir / f"{request.document_id}_chunks.txt"
    
    if not chunks_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Document {request.document_id} not found"
        )
    
    # Read document chunks
    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks_content = f.read()
    
    # Reconstruct text
    import re
    full_text = re.sub(r'=== CHUNK \d+ ===\n', '', chunks_content)
    
    # Extract characters (should be cached in production)
    characters = character_service.extract_characters(
        text=full_text,
        max_characters=10
    )
    
    # Find the requested character
    character = None
    for char in characters:
        if char['character_id'] == request.character_id:
            character = char
            break
    
    if not character:
        raise HTTPException(
            status_code=404,
            detail=f"Character {request.character_id} not found in document"
        )
    
    # Convert conversation history to dict format
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in request.conversation_history
    ] if request.conversation_history else []
    
    try:
        # Generate character response
        result = chat_service.chat_with_character(
            character=character,
            document_id=request.document_id,
            user_message=request.message,
            conversation_history=history
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )

@router.post("/chat/greeting")
async def get_character_greeting(request: GreetingRequest):
    """
    Get a greeting message from a character
    """
    upload_dir = Path(settings.UPLOAD_DIR)
    chunks_path = upload_dir / f"{request.document_id}_chunks.txt"
    
    if not chunks_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Document {request.document_id} not found"
        )
    
    # Read document chunks
    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks_content = f.read()
    
    # Reconstruct text
    import re
    full_text = re.sub(r'=== CHUNK \d+ ===\n', '', chunks_content)
    
    # Extract characters
    characters = character_service.extract_characters(
        text=full_text,
        max_characters=10
    )
    
    # Find the requested character
    character = None
    for char in characters:
        if char['character_id'] == request.character_id:
            character = char
            break
    
    if not character:
        raise HTTPException(
            status_code=404,
            detail=f"Character {request.character_id} not found"
        )
    
    try:
        greeting = chat_service.get_character_greeting(character)
        
        return {
            "status": "success",
            "character_name": character['name'],
            "greeting": greeting
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating greeting: {str(e)}"
        )
