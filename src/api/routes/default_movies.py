"""
Default Movies API Routes
Provides pre-loaded movie characters for instant chat
"""
from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
from typing import List, Dict, Optional

router = APIRouter()

MOVIES_METADATA_PATH = Path("data/default_movies/metadata/movies.json")
CHARACTERS_DIR = Path("data/default_movies/preloaded_characters")


@router.get("/default-movies")
async def get_default_movies():
    """
    Get all pre-loaded movies
    Returns list of movies with metadata
    """
    try:
        if not MOVIES_METADATA_PATH.exists():
            return {
                "status": "success",
                "movies": [],
                "total": 0,
                "message": "No default movies configured"
            }
        
        with open(MOVIES_METADATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            "status": "success",
            "movies": data.get("movies", []),
            "total": len(data.get("movies", []))
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading default movies: {str(e)}"
        )


@router.get("/default-movies/{movie_id}")
async def get_default_movie(movie_id: str):
    """
    Get details of a specific default movie
    """
    try:
        if not MOVIES_METADATA_PATH.exists():
            raise HTTPException(
                status_code=404,
                detail="Default movies not found"
            )
        
        with open(MOVIES_METADATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        movies = data.get("movies", [])
        movie = next((m for m in movies if m["movie_id"] == movie_id), None)
        
        if not movie:
            raise HTTPException(
                status_code=404,
                detail=f"Movie {movie_id} not found"
            )
        
        return {
            "status": "success",
            "movie": movie
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading movie: {str(e)}"
        )


@router.get("/default-movies/{movie_id}/characters")
async def get_movie_characters(movie_id: str):
    """
    Get all characters for a specific movie
    """
    try:
        # First, get the movie to find its document_id
        if not MOVIES_METADATA_PATH.exists():
            raise HTTPException(
                status_code=404,
                detail="Default movies not found"
            )
        
        with open(MOVIES_METADATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        movies = data.get("movies", [])
        movie = next((m for m in movies if m["movie_id"] == movie_id), None)
        
        if not movie:
            raise HTTPException(
                status_code=404,
                detail=f"Movie {movie_id} not found"
            )
        
        document_id = movie["document_id"]
        
        # Find the characters file for this movie
        characters_data = None
        for char_file in CHARACTERS_DIR.glob("*_characters.json"):
            with open(char_file, 'r', encoding='utf-8') as f:
                temp_data = json.load(f)
                if temp_data.get("document_id") == document_id:
                    characters_data = temp_data
                    break
        
        if not characters_data:
            raise HTTPException(
                status_code=404,
                detail=f"Characters not found for movie {movie_id}"
            )
        
        return {
            "status": "success",
            "document_id": characters_data["document_id"],
            "movie_title": characters_data["movie_title"],
            "characters": characters_data["characters"],
            "total_found": len(characters_data["characters"]),
            "from_cache": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading characters: {str(e)}"
        )


@router.get("/default-movies/{movie_id}/characters/{character_id}")
async def get_movie_character(movie_id: str, character_id: str):
    """
    Get details of a specific character from a movie
    """
    try:
        # Get all characters for the movie
        characters_response = await get_movie_characters(movie_id)
        characters = characters_response["characters"]
        
        # Find the specific character
        character = next((c for c in characters if c["character_id"] == character_id), None)
        
        if not character:
            raise HTTPException(
                status_code=404,
                detail=f"Character {character_id} not found in movie {movie_id}"
            )
        
        return {
            "status": "success",
            "character": character,
            "movie_title": characters_response["movie_title"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading character: {str(e)}"
        )
