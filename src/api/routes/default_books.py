from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
from typing import List, Dict

router = APIRouter()

DEFAULT_BOOKS_PATH = Path("data/default_books/metadata/books.json")
CHARACTERS_PATH = Path("data/default_books/preloaded_characters")


@router.get("/default-books")
async def get_default_books():
    """
    Get list of all default books available in the application
    
    Returns:
        List of default books with metadata (title, author, cover, etc.)
    """
    try:
        if not DEFAULT_BOOKS_PATH.exists():
            return {
                "status": "success",
                "books": [],
                "message": "No default books configured"
            }
        
        with open(DEFAULT_BOOKS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            "status": "success",
            "books": data.get("books", []),
            "total": len(data.get("books", []))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading default books: {str(e)}")


@router.get("/default-books/{book_id}")
async def get_default_book(book_id: str):
    """
    Get specific default book details by book_id
    
    Args:
        book_id: Unique identifier for the book (e.g., "harry_potter_1")
    
    Returns:
        Book details with metadata
    """
    try:
        if not DEFAULT_BOOKS_PATH.exists():
            raise HTTPException(status_code=404, detail="Default books not configured")
        
        with open(DEFAULT_BOOKS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        book = next((b for b in data.get("books", []) if b["book_id"] == book_id), None)
        
        if not book:
            raise HTTPException(status_code=404, detail=f"Book '{book_id}' not found")
        
        return {
            "status": "success",
            "book": book
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading book: {str(e)}")


@router.get("/default-books/{book_id}/characters")
async def get_default_book_characters(book_id: str):
    """
    Get pre-loaded characters for a default book
    
    Args:
        book_id: Unique identifier for the book
    
    Returns:
        List of characters with full details (name, aliases, personality, etc.)
    """
    try:
        # Verify book exists
        if DEFAULT_BOOKS_PATH.exists():
            with open(DEFAULT_BOOKS_PATH, 'r', encoding='utf-8') as f:
                books_data = json.load(f)
            
            book = next((b for b in books_data.get("books", []) if b["book_id"] == book_id), None)
            if not book:
                raise HTTPException(status_code=404, detail=f"Book '{book_id}' not found")
        
        # Read character file
        char_file = CHARACTERS_PATH / f"{book_id}_characters.json"
        
        if not char_file.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"Characters not found for book '{book_id}'. File expected: {char_file}"
            )
        
        with open(char_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            "status": "success",
            "document_id": data.get("document_id"),
            "book_title": data.get("book_title"),
            "characters": data.get("characters", []),
            "total_found": data.get("total_found", len(data.get("characters", []))),
            "from_cache": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading characters: {str(e)}")


@router.get("/default-books/{book_id}/characters/{character_id}")
async def get_default_character_details(book_id: str, character_id: str):
    """
    Get specific character details from a default book
    
    Args:
        book_id: Unique identifier for the book
        character_id: Unique identifier for the character
    
    Returns:
        Character details with personality and traits
    """
    try:
        # Read character file
        char_file = CHARACTERS_PATH / f"{book_id}_characters.json"
        
        if not char_file.exists():
            raise HTTPException(status_code=404, detail=f"Characters not found for book '{book_id}'")
        
        with open(char_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        character = next((c for c in data.get("characters", []) if c["character_id"] == character_id), None)
        
        if not character:
            raise HTTPException(status_code=404, detail=f"Character '{character_id}' not found")
        
        return {
            "status": "success",
            "character": character,
            "document_id": data.get("document_id")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading character: {str(e)}")
