from fastapi import APIRouter, HTTPException
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional

from src.services.character_service import CharacterService
from src.config import settings

router = APIRouter()
character_service = CharacterService()

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
                    print(f"Failed to generate personality for {character['name']}: {e}")
        
        return {
            "status": "success",
            "document_id": request.document_id,
            "characters": characters,
            "total_found": len(characters)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error extracting characters: {str(e)}"
        )

@router.get("/characters/{document_id}")
async def get_characters(document_id: str):
    """
    Get cached character list for a document
    (In production, this would query a database)
    """
    return {
        "message": "Character retrieval endpoint",
        "document_id": document_id,
        "note": "Implement database storage for production"
    }