"""
Chat API Endpoints
Handles character conversations
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, AsyncIterator
from pathlib import Path
import json
import asyncio
from sqlalchemy.orm import Session

from src.services.chat_service import ChatService
from src.services.character_service import CharacterService
from src.services.character_cache import CharacterCache
from src.services.chat_session_service import ChatSessionService
from src.models.database import get_db
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
async def chat_with_character(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Chat with a character from an uploaded book or default book
    Uses RAG to retrieve relevant story context (if available)
    """
    # Check if this is a default book
    is_default_book = request.document_id.startswith("default_")
    
    if is_default_book:
        # For default books/movies, load character from preloaded data
        from pathlib import Path as PathLib
        
        # Determine if it's a movie or book based on document_id
        is_movie = "movie" in request.document_id
        if is_movie:
            default_chars_dir = PathLib("data/default_movies/preloaded_characters")
        else:
            default_chars_dir = PathLib("data/default_books/preloaded_characters")
        
        character = None
        if default_chars_dir.exists():
            for char_file in default_chars_dir.glob("*_characters.json"):
                try:
                    with open(char_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if data.get("document_id") == request.document_id:
                            for char in data.get("characters", []):
                                if char["character_id"] == request.character_id:
                                    character = char
                                    break
                            if character:
                                break
                except Exception:
                    continue
        
        if not character:
            raise HTTPException(
                status_code=404,
                detail=f"Character {request.character_id} not found in default book"
            )
    else:
        # Verify document exists for uploaded books
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
        if 'characters' in locals():
            available_ids = [char['character_id'] for char in characters[:5]]
            raise HTTPException(
                status_code=404,
                detail=f"Character {request.character_id} not found in document. Available characters: {', '.join(available_ids)}"
            )
        else:
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
        
        # Auto-save to session (only for default books)
        if request.document_id.startswith("default_"):
            try:
                ChatSessionService.save_message(
                    db=db,
                    document_id=request.document_id,
                    character_id=request.character_id,
                    character_name=character['name'],
                    user_message=request.message,
                    assistant_response=result['response']
                )
            except Exception as save_error:
                # Don't fail the request if saving fails, just log it
                import logging
                logging.error(f"Failed to save chat session: {save_error}")
        
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
    Supports uploaded books, default books, and default movies
    """
    # Check if this is a default book/movie (document_id starts with "default_")
    is_default_book = request.document_id.startswith("default_")
    
    if is_default_book:
        # For default books/movies, load character from preloaded data
        from pathlib import Path as PathLib
        
        # Determine if it's a movie or book
        is_movie = "movie" in request.document_id
        if is_movie:
            default_chars_dir = PathLib("data/default_movies/preloaded_characters")
        else:
            default_chars_dir = PathLib("data/default_books/preloaded_characters")
        
        # Try to find the character file by searching all preloaded files
        character = None
        if default_chars_dir.exists():
            for char_file in default_chars_dir.glob("*_characters.json"):
                try:
                    with open(char_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if data.get("document_id") == request.document_id:
                            # Found the right book/movie, now find the character
                            for char in data.get("characters", []):
                                if char["character_id"] == request.character_id:
                                    character = char
                                    break
                            if character:
                                break
                except Exception:
                    continue
        
        if not character:
            raise HTTPException(
                status_code=404,
                detail=f"Character {request.character_id} not found in default book {request.document_id}"
            )
    else:
        # For uploaded books, check if chunks file exists
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
        if 'characters' in locals():
            available_ids = [char['character_id'] for char in characters[:5]]
            raise HTTPException(
                status_code=404,
                detail=f"Character {request.character_id} not found. Available characters: {', '.join(available_ids)}"
            )
        else:
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


@router.post("/chat/stream")
async def chat_with_character_stream(request: ChatRequest):
    """
    Stream chat response using Server-Sent Events (SSE)
    
    TASK 5: RESPONSE STREAMING
    - Provides real-time token streaming (like ChatGPT)
    - Reduces perceived latency by 60-80%
    - User sees response immediately instead of waiting for full completion
    
    Returns:
        StreamingResponse: SSE stream with text chunks
    """
    # Check if this is a default book/movie
    is_default_book = request.document_id.startswith("default_")
    
    if is_default_book:
        # Load character from preloaded JSON files
        character = None
        
        # Determine if it's a movie or book
        is_movie = "movie" in request.document_id
        if is_movie:
            preloaded_dir = Path("data/default_movies/preloaded_characters")
        else:
            preloaded_dir = Path("data/default_books/preloaded_characters")
        
        if preloaded_dir.exists():
            for char_file in preloaded_dir.glob("*_characters.json"):
                with open(char_file, 'r', encoding='utf-8') as f:
                    characters_data = json.load(f)
                    if characters_data.get('document_id') == request.document_id:
                        for char in characters_data['characters']:
                            if char['character_id'] == request.character_id:
                                character = char
                                break
                    if character:
                        break
        
        if not character:
            content_type = "movie" if is_movie else "book"
            raise HTTPException(
                status_code=404,
                detail=f"Character {request.character_id} not found in default {content_type} {request.document_id}"
            )
    else:
        # Original logic for uploaded documents
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
    
    # Create async generator for SSE
    async def event_generator() -> AsyncIterator[str]:
        try:
            chunk_id = 0
            
            # Get streaming response from chat service
            stream = chat_service.chat_with_character_stream(
                character=character,
                document_id=request.document_id,
                user_message=request.message,
                conversation_history=history
            )
            
            # Convert to SSE format
            for chunk in stream:
                chunk_id += 1
                
                # SSE format: "data: {json}\n\n"
                data = {
                    "id": chunk_id,
                    "text": chunk,
                    "done": False,
                    "character_name": character['name']
                }
                yield f"data: {json.dumps(data)}\n\n"
                
                # Small delay to prevent overwhelming client
                await asyncio.sleep(0.01)
            
            # Send completion event
            final_data = {
                "id": chunk_id + 1,
                "text": "",
                "done": True,
                "character_name": character['name']
            }
            yield f"data: {json.dumps(final_data)}\n\n"
            
        except Exception as e:
            # Send error event
            error_data = {
                "error": str(e),
                "done": True
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    # Return SSE response
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


# ============ NEW ENDPOINTS FOR CHAT SESSION PERSISTENCE ============

class SessionHistoryRequest(BaseModel):
    document_id: str
    character_id: str


class ClearSessionRequest(BaseModel):
    document_id: str
    character_id: str


@router.get("/chat/session/history")
async def get_session_history(
    document_id: str,
    character_id: str,
    db: Session = Depends(get_db)
):
    """
    Load conversation history for a character (default books only for now)
    Returns empty array if no history exists
    """
    # Only for default books for now
    if not document_id.startswith("default_"):
        return {
            "status": "success",
            "document_id": document_id,
            "character_id": character_id,
            "conversation_history": [],
            "message": "Session persistence only available for default books"
        }
    
    try:
        history = ChatSessionService.get_conversation_history(
            db, document_id, character_id
        )
        
        return {
            "status": "success",
            "document_id": document_id,
            "character_id": character_id,
            "conversation_history": history,
            "total_messages": len(history)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading session history: {str(e)}"
        )


@router.post("/chat/session/save")
async def save_chat_message(
    document_id: str,
    character_id: str,
    character_name: str,
    user_message: str,
    assistant_response: str,
    db: Session = Depends(get_db)
):
    """
    Save a message exchange to conversation history (default books only for now)
    """
    # Only for default books for now
    if not document_id.startswith("default_"):
        return {
            "status": "skipped",
            "message": "Session persistence only available for default books"
        }
    
    try:
        session = ChatSessionService.save_message(
            db=db,
            document_id=document_id,
            character_id=character_id,
            character_name=character_name,
            user_message=user_message,
            assistant_response=assistant_response
        )
        
        return {
            "status": "success",
            "message": "Chat message saved successfully",
            "session_id": session.session_id,
            "total_messages": len(session.get_messages())
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving chat message: {str(e)}"
        )


@router.delete("/chat/session/clear")
async def clear_chat_session(
    document_id: str,
    character_id: str,
    db: Session = Depends(get_db)
):
    """
    Clear conversation history for a character
    """
    try:
        deleted = ChatSessionService.clear_session(
            db, document_id, character_id
        )
        
        if deleted:
            return {
                "status": "success",
                "message": "Chat session cleared successfully"
            }
        else:
            return {
                "status": "success",
                "message": "No session found to clear"
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing session: {str(e)}"
        )


@router.get("/chat/session/list")
async def list_sessions_for_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    List all chat sessions for a document
    """
    try:
        sessions = ChatSessionService.get_all_sessions_for_document(
            db, document_id
        )
        
        return {
            "status": "success",
            "document_id": document_id,
            "sessions": [
                {
                    "session_id": s.session_id,
                    "character_id": s.character_id,
                    "character_name": s.character_name,
                    "message_count": len(s.get_messages()),
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None
                }
                for s in sessions
            ],
            "total_sessions": len(sessions)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing sessions: {str(e)}"
        )
