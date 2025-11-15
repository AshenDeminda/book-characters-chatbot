from fastapi import APIRouter, HTTPException
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional
import logging

from src.services.character_service import CharacterService
from src.services.character_cache import CharacterCache
from src.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
character_service = CharacterService()
character_cache = CharacterCache()

class ExtractCharactersRequest(BaseModel):
    document_id: str
    max_characters: Optional[int] = 10
    include_personality: Optional[bool] = False

class Character(BaseModel):
    character_id: str
    name: str
    aliases: List[str]
    description: str
    role: str
    personality: Optional[dict] = None

class ExtractCharactersResponse(BaseModel):
    status: str
    document_id: str
    characters: List[Character]
    total_found: int

@router.post("/characters/extract-characters", response_model=ExtractCharactersResponse)
async def extract_characters(request: ExtractCharactersRequest):
    """
    Extract character names from uploaded document using AI
    """
    # Load document text from chunks
    upload_dir = Path(settings.UPLOAD_DIR)
    chunks_path = upload_dir / f"{request.document_id}_chunks.txt"
    
    if not chunks_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Document {request.document_id} not found. Please upload a document first."
        )
    
    # Read and reconstruct text from chunks
    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks_content = f.read()
    
    # Extract text from chunks (remove chunk headers)
    import re
    full_text = re.sub(r'=== CHUNK \d+ ===\n', '', chunks_content)
    
    if not full_text or len(full_text) < 100:
        raise HTTPException(
            status_code=400,
            detail="Document text is too short or empty"
        )
    
    try:
        # Extract characters using LLM
        characters = character_service.extract_characters(
            text=full_text,
            max_characters=request.max_characters
        )
        
        # Generate personality summaries if requested
        if request.include_personality:
            for character in characters:
                try:
                    personality = character_service.generate_personality_summary(
                        character_name=character['name'],
                        text=full_text
                    )
                    character['personality'] = personality
                except Exception as e:
                    # If personality generation fails, continue without it
                    character['personality'] = None
                    logger.warning(f"Failed to generate personality for {character['name']}: {e}")
        
        # Save to cache
        character_cache.save_characters(document_id, characters)
        
        return {
            "status": "success",
            "document_id": document_id,
            "characters": characters,
            "total_found": len(characters),
            "from_cache": False
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting characters: {str(e)}"
        )

@router.get("/characters/extract-characters/{document_id}", response_model=ExtractCharactersResponse)
async def extract_characters_get(document_id: str, include_personality: bool = True, force_refresh: bool = False):
    """
    Extract character names from uploaded document using AI (GET version for easy testing)
    Uses cache to avoid re-extraction unless force_refresh=true
    """
    # Check cache first (unless force refresh)
    if not force_refresh:
        cached_characters = character_cache.load_characters(document_id)
        if cached_characters:
            logger.info(f"Returning {len(cached_characters)} characters from cache")
            return {
                "status": "success",
                "document_id": document_id,
                "characters": cached_characters,
                "total_found": len(cached_characters)
            }
    
    # Load document text from chunks
    upload_dir = Path(settings.UPLOAD_DIR)
    chunks_path = upload_dir / f"{document_id}_chunks.txt"
    
    if not chunks_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found. Please upload a document first."
        )
    
    # Read and reconstruct text from chunks
    try:
        with open(chunks_path, 'r', encoding='utf-8') as f:
            chunks_content = f.read()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading document file: {str(e)}"
        )
    
    # Extract text from chunks (remove chunk headers)
    import re
    full_text = re.sub(r'=== CHUNK \d+ ===\n', '', chunks_content)
    
    if not full_text or len(full_text) < 100:
        raise HTTPException(
            status_code=400,
            detail="Document text is too short or empty"
        )
    
    try:
        # Extract characters using LLM
        characters = character_service.extract_characters(
            text=full_text,
            max_characters=10
        )
        
        # Generate personality summaries if requested
        if include_personality:
            for character in characters:
                try:
                    personality = character_service.generate_personality_summary(
                        character_name=character['name'],
                        text=full_text
                    )
                    character['personality'] = personality
                except Exception as e:
                    # If personality generation fails, continue without it
                    character['personality'] = None
                    logger.warning(f"Failed to generate personality for {character['name']}: {e}")
        
        # Save to cache for future use
        character_cache.save_characters(document_id, characters)
        
        return {
            "status": "success",
            "document_id": document_id,
            "characters": characters,
            "total_found": len(characters)
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error extracting characters for document {document_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting characters: {str(e)}"
        )