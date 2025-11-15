"""
Character Cache Service
Stores and retrieves extracted characters to avoid re-extraction
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class CharacterCache:
    """Manages cached character data"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        """
        Initialize character cache
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, document_id: str) -> Path:
        """Get cache file path for a document"""
        return self.cache_dir / f"{document_id}_characters.json"
    
    def save_characters(self, document_id: str, characters: List[Dict]) -> bool:
        """
        Save extracted characters to cache
        
        Args:
            document_id: Document identifier
            characters: List of character dictionaries
            
        Returns:
            True if successful
        """
        try:
            cache_path = self._get_cache_path(document_id)
            
            cache_data = {
                "document_id": document_id,
                "characters": characters,
                "character_count": len(characters)
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Cached {len(characters)} characters for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving character cache: {e}")
            return False
    
    def load_characters(self, document_id: str) -> Optional[List[Dict]]:
        """
        Load characters from cache
        
        Args:
            document_id: Document identifier
            
        Returns:
            List of characters or None if not cached
        """
        try:
            cache_path = self._get_cache_path(document_id)
            
            if not cache_path.exists():
                logger.info(f"No cache found for document {document_id}")
                return None
            
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            characters = cache_data.get('characters', [])
            logger.info(f"Loaded {len(characters)} characters from cache for document {document_id}")
            return characters
            
        except Exception as e:
            logger.error(f"Error loading character cache: {e}")
            return None
    
    def get_character_by_id(self, document_id: str, character_id: str) -> Optional[Dict]:
        """
        Get a specific character from cache
        
        Args:
            document_id: Document identifier
            character_id: Character identifier
            
        Returns:
            Character dictionary or None if not found
        """
        characters = self.load_characters(document_id)
        
        if not characters:
            return None
        
        for char in characters:
            if char.get('character_id') == character_id:
                return char
        
        return None
    
    def cache_exists(self, document_id: str) -> bool:
        """
        Check if cache exists for a document
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if cache exists
        """
        cache_path = self._get_cache_path(document_id)
        return cache_path.exists()
    
    def delete_cache(self, document_id: str) -> bool:
        """
        Delete cache for a document
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if successful
        """
        try:
            cache_path = self._get_cache_path(document_id)
            
            if cache_path.exists():
                cache_path.unlink()
                logger.info(f"Deleted cache for document {document_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting cache: {e}")
            return False
