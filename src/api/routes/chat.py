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
from src.services.character_cache import CharacterCache
from src.config import settings

router = APIRouter()
chat_service = ChatService()
character_service = CharacterService()
character_cache = CharacterCache()

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
    # Verify document exists
    upload_dir = Path(settings.UPLOAD_DIR)
    chunks_path = upload_dir / f"{request.document_id}_chunks.txt"
    
    if not chunks_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Document {request.document_id} not found"
        )
    
    # Try to load character from cache first (FAST PATH)
    character = character_cache.get_character_by_id(request.document_id, request.character_id)
    
    if not character:
        # Cache miss - need to extract characters (SLOW PATH)
        # Read document chunks
        with open(chunks_path, 'r', encoding='utf-8') as f:
            chunks_content = f.read()
        
        # Reconstruct text
        import re
        full_text = re.sub(r'=== CHUNK \d+ ===\n', '', chunks_content)
        
        # Extract characters (use higher limit to find more characters)
        characters = character_service.extract_characters(
            text=full_text,
            max_characters=30
        )
        
        # Save to cache for future requests
        character_cache.save_characters(request.document_id, characters)
        
        # Find the requested character by character_id first
        for char in characters:
            if char['character_id'] == request.character_id:
                character = char
                break
        
        # If not found by ID, try matching by name or aliases
        if not character:
            # Extract name from character_id (format: char_name_slug)
            name_from_id = request.character_id.replace('char_', '').replace('_', ' ').strip()
            for char in characters:
                # Check if name matches (case-insensitive)
                if name_from_id.lower() in char['name'].lower() or char['name'].lower() in name_from_id.lower():
                    character = char
                    break
            # Check aliases
            if char.get('aliases'):
                for alias in char['aliases']:
                    if name_from_id.lower() in alias.lower() or alias.lower() in name_from_id.lower():
                        character = char
                        break
                if character:
                    break
    
    if not character:
        # Provide helpful error message with available characters
        available_ids = [char['character_id'] for char in characters[:5]]
        raise HTTPException(
            status_code=404,
            detail=f"Character {request.character_id} not found in document. Available characters: {', '.join(available_ids)}"
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
    
    # Try to load character from cache first (FAST PATH)
    character = character_cache.get_character_by_id(request.document_id, request.character_id)
    
    if not character:
        # Cache miss - need to extract characters (SLOW PATH)
        # Read document chunks
        with open(chunks_path, 'r', encoding='utf-8') as f:
            chunks_content = f.read()
        
        # Reconstruct text
        import re
        full_text = re.sub(r'=== CHUNK \d+ ===\n', '', chunks_content)
        
        # Extract characters (use higher limit to find more characters)
        characters = character_service.extract_characters(
            text=full_text,
            max_characters=30
        )
        
        # Save to cache for future requests
        character_cache.save_characters(request.document_id, characters)
        
        # Find the requested character by character_id first
        for char in characters:
            if char['character_id'] == request.character_id:
                character = char
                break
        
        # If not found by ID, try matching by name or aliases
        if not character:
            # Extract name from character_id (format: char_name_slug)
            name_from_id = request.character_id.replace('char_', '').replace('_', ' ').strip()
            for char in characters:
                # Check if name matches (case-insensitive)
                if name_from_id.lower() in char['name'].lower() or char['name'].lower() in name_from_id.lower():
                    character = char
                    break
                # Check aliases
                if char.get('aliases'):
                    for alias in char['aliases']:
                        if name_from_id.lower() in alias.lower() or alias.lower() in name_from_id.lower():
                            character = char
                            break
                    if character:
                        break
                for alias in char['aliases']:
                    if name_from_id.lower() in alias.lower() or alias.lower() in name_from_id.lower():
                        character = char
                        break
                if character:
                    break
    
    if not character:
        # Provide helpful error message with available characters
        available_ids = [char['character_id'] for char in characters[:5]]
        raise HTTPException(
            status_code=404,
            detail=f"Character {request.character_id} not found. Available characters: {', '.join(available_ids)}"
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
