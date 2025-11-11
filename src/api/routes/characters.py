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

class Character(BaseModel):
    character_id: str
    name: str
    description: str
    role: str

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
    # Load document text
    upload_dir = Path(settings.UPLOAD_DIR)
    text_path = upload_dir / f"{request.document_id}_text.txt"
    
    if not text_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Document {request.document_id} not found. Please upload a document first."
        )
    
    # Read text
    with open(text_path, 'r', encoding='utf-8') as f:
        full_text = f.read()
    
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