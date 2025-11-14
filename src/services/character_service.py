from typing import List, Dict, Set, Tuple
# OpenAI import - commented for future use when key is purchased
# from openai import OpenAI
import google.generativeai as genai
import json
import logging
import re
from difflib import SequenceMatcher

from src.config import settings

logger = logging.getLogger(__name__)

class CharacterService:
    """Extract character names using LLM (OpenAI or Gemini)"""
    
    def __init__(self):
        # OpenAI client - commented for future use
        # self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Gemini client - currently active
        self.gemini_model = None
        if settings.AI_PROVIDER == "gemini":
            if not settings.GEMINI_API_KEY:
                logger.error("GEMINI_API_KEY not found in settings. Please add it to your .env file.")
            else:
                try:
                    genai.configure(api_key=settings.GEMINI_API_KEY)
                    self.gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
                    logger.info("Gemini model initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize Gemini: {e}")
        
        # Blacklist of non-character terms (insults, titles, groups)
        self.non_character_terms = {
            "idiot", "fool", "princess", "your majesty", "majesty",
            "bloodstained queen", "bloody reina", "reina",
            "lieutenant", "captain", "commander", "colonel",
            "eighty-six", "soldiers", "troops", "children",
            "boy", "girl", "stranger", "enemy", "friend",
            "handler", "officer", "general", "master", "mistress",
            "lord", "lady", "sir", "madam", "miss", "mr", "mrs", "ms"
        }
        
        # Known alias patterns for common character variations
        self.alias_patterns = [
            # Format: (pattern_name, set of aliases that should merge)
            ("shin_group", {"undertaker", "reaper", "shinei", "shin", "nouzen"}),
            ("lena_group", {"handler one", "vladilena", "lena", "milizé", "milize"}),
        ]
    
    def _is_non_character(self, name: str) -> bool:
        """Check if name is in blacklist of non-character terms"""
        normalized = self._normalize_name(name)
        
        # Check exact match
        if normalized in self.non_character_terms:
            return True
        
        # Check if it's purely a title/rank
        title_pattern = r'^(the\s+)?(lieutenant|captain|commander|colonel|general|officer|handler)\s*(one|two|three)?$'
        if re.match(title_pattern, normalized):
            return True
        
        # Check if it's a group reference
        group_pattern = r'^(the\s+)?(soldiers|troops|children|enemies|friends|group|squad|unit)$'
        if re.match(group_pattern, normalized):
            return True
        
        return False
    
    def _check_alias_patterns(self, name: str) -> str:
        """Check if name matches known alias patterns, return pattern group"""
        normalized = self._normalize_name(name)
        
        for pattern_name, aliases in self.alias_patterns:
            # Check if any word from the name appears in the alias set
            name_words = set(normalized.split())
            if name_words.intersection(aliases):
                return pattern_name
        
        return None
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison (lowercase, strip whitespace)"""
        return name.lower().strip()
    
    def _fuzzy_match(self, name1: str, name2: str, threshold: float = 0.85) -> bool:
        """Check if two names are similar using fuzzy matching"""
        norm1 = self._normalize_name(name1)
        norm2 = self._normalize_name(name2)
        
        # Exact match
        if norm1 == norm2:
            return True
        
        # Check if one is substring of another (for nicknames)
        if norm1 in norm2 or norm2 in norm1:
            return True
        
        # Fuzzy matching for similar names
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        return similarity >= threshold
    
    def _extract_name_parts(self, name: str) -> Set[str]:
        """Extract individual name parts (first, last, middle names)"""
        # Remove titles, callsigns in parentheses, etc.
        cleaned = re.sub(r'\([^)]*\)', '', name)
        cleaned = re.sub(r'["\']', '', cleaned)
        
        # Split into parts
        parts = cleaned.split()
        return {self._normalize_name(part) for part in parts if len(part) > 1}
    
    def _are_same_character(self, char1: Dict, char2: Dict) -> bool:
        """
        Determine if two character dictionaries represent the same person
        Uses multiple heuristics: exact match, fuzzy match, name parts overlap, alias patterns
        """
        name1 = char1.get('name', '')
        name2 = char2.get('name', '')
        
        # Check if both belong to same alias pattern
        pattern1 = self._check_alias_patterns(name1)
        pattern2 = self._check_alias_patterns(name2)
        
        if pattern1 and pattern2 and pattern1 == pattern2:
            return True
        
        # Exact or fuzzy match on full names
        if self._fuzzy_match(name1, name2):
            return True
        
        # Check if descriptions mention each other
        desc1 = char1.get('description', '').lower()
        desc2 = char2.get('description', '').lower()
        
        norm1 = self._normalize_name(name1)
        norm2 = self._normalize_name(name2)
        
        if norm1 in desc2 or norm2 in desc1:
            return True
        
        # Check for common name parts (shared first or last name)
        parts1 = self._extract_name_parts(name1)
        parts2 = self._extract_name_parts(name2)
        
        # If they share significant name parts
        common_parts = parts1.intersection(parts2)
        if common_parts and len(common_parts) >= 1:
            # If any common part is longer than 3 chars, consider it a match
            if any(len(part) > 3 for part in common_parts):
                return True
        
        return False
    
    def _merge_characters(self, characters: List[Dict]) -> List[Dict]:
        """
        Merge characters that represent the same person
        Adds 'aliases' field with all name variants
        Filters out non-character terms
        """
        if not characters:
            return []
        
        # First pass: filter out non-characters
        filtered_characters = []
        for char in characters:
            if not self._is_non_character(char['name']):
                filtered_characters.append(char)
            else:
                logger.info(f"Filtered out non-character: {char['name']}")
        
        if not filtered_characters:
            return []
        
        merged = []
        used_indices = set()
        
        for i, char1 in enumerate(filtered_characters):
            if i in used_indices:
                continue
            
            # Start with current character
            main_char = char1.copy()
            aliases = {char1['name']}
            
            # Find all characters that match this one
            for j, char2 in enumerate(filtered_characters):
                if i != j and j not in used_indices:
                    if self._are_same_character(char1, char2):
                        aliases.add(char2['name'])
                        used_indices.add(j)
                        
                        # Merge descriptions if char2 has more detail
                        if len(char2.get('description', '')) > len(main_char.get('description', '')):
                            main_char['description'] = char2['description']
                        
                        # Keep higher role priority (protagonist > supporting)
                        if char2.get('role') == 'protagonist':
                            main_char['role'] = 'protagonist'
            
            # Add aliases field
            main_char['aliases'] = sorted(list(aliases))
            
            # Smart primary name selection
            # 1. Prefer full names (contains space, not all uppercase)
            # 2. Then prefer callsigns/nicknames
            # 3. Avoid titles and single-word insults
            
            primary_candidates = [
                name for name in aliases 
                if " " in name and not name.isupper() and len(name) > 3
            ]
            
            if primary_candidates:
                # Choose longest full name
                main_char['name'] = max(primary_candidates, key=len)
            else:
                # No full name found, use longest alias (probably callsign)
                main_char['name'] = max(aliases, key=len)
            
            merged.append(main_char)
            used_indices.add(i)
        
        logger.info(f"Filtered {len(characters)} → {len(filtered_characters)} (removed {len(characters) - len(filtered_characters)} non-characters)")
        logger.info(f"Merged {len(filtered_characters)} characters into {len(merged)} unique characters")
        return merged
    
    def extract_characters(self, text: str, max_characters: int = 10) -> List[Dict]:
        """
        Use LLM to find character names from story text with entity resolution
        
        Args:
            text: Story text (or first portion of it)
            max_characters: Maximum number of characters to extract
            
        Returns:
            List of character dictionaries with aliases merged
        """
        # Use first 12000 characters for better context
        sample_text = text[:12000]
        
        prompt = f"""You are an expert entity extraction system for novels.

Your job is to identify ONLY real characters that actually exist as people in the story.

Given the following novel text:

{sample_text}

Follow these STRICT rules:

### RULES FOR IDENTIFYING REAL CHARACTERS
1. Extract ONLY entities that represent actual people with agency:
   - If they speak
   - If they act
   - If they are described as individuals

2. IGNORE the following:
   - Insults or mockery nicknames (e.g., "idiot," "princess," "fool," "Your Majesty" used sarcastically)
   - Group names (e.g., "the Eighty-Six", "soldiers", "children")
   - Titles alone (e.g., "the lieutenant," "the captain," "the queen")
   - Epigraph authors unless they appear inside the story's events
   - Generic references (e.g., "boy," "girl," "stranger")

3. When a character has name variations (nicknames, callsigns, shortened forms):
   - LIST EACH VARIANT as a SEPARATE ENTRY (merging will be handled later)
   - Example:
     - "Shin"
     - "Shinei Nouzen"
     - "Undertaker"

4. For each extracted character, include:
   - "name": the exact name or callsign as it appears in text
   - "description": one sentence describing who they are IN THE SCENE ONLY
   - "role": protagonist / antagonist / supporting
     (guess based only on the excerpt)

### OUTPUT FORMAT
Return ONLY a JSON array:
[
  {{
    "name": "Name or alias",
    "description": "One-sentence description",
    "role": "protagonist/supporting/antagonist"
  }}
]

Return ONLY the JSON array, no additional text."""

        try:
            # Use Gemini (currently active)
            if settings.AI_PROVIDER == "gemini":
                if not self.gemini_model:
                    raise Exception("Gemini model not initialized. Check your GEMINI_API_KEY in .env file.")
                response = self.gemini_model.generate_content(prompt)
                content = response.text.strip()
            
            # OpenAI implementation - commented for future use
            # elif settings.AI_PROVIDER == "openai":
            #     response = self.openai_client.chat.completions.create(
            #         model=settings.OPENAI_MODEL,
            #         messages=[
            #             {"role": "system", "content": "You are a literary analyst expert at identifying characters in stories."},
            #             {"role": "user", "content": prompt}
            #         ],
            #         temperature=0.3,
            #         max_tokens=1000
            #     )
            #     content = response.choices[0].message.content.strip()
            
            else:
                raise Exception(f"Unsupported AI provider: {settings.AI_PROVIDER}")
            
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()
            
            characters = json.loads(content)
            
            # Perform entity resolution - merge duplicate characters
            logger.info(f"Raw extraction found {len(characters)} character mentions")
            characters = self._merge_characters(characters)
            
            # Limit to max_characters after merging
            characters = characters[:max_characters]
            
            # Add character IDs based on normalized names
            for i, char in enumerate(characters):
                # Create ID from primary name
                name_slug = self._normalize_name(char['name']).replace(' ', '_')
                name_slug = re.sub(r'[^a-z0-9_]', '', name_slug)
                char['character_id'] = f"char_{name_slug}" if name_slug else f"char_{i+1:03d}"
            
            logger.info(f"Final result: {len(characters)} unique characters after entity resolution")
            return characters
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response content: {content}")
            raise Exception("Failed to parse character list from AI response")
        
        except Exception as e:
            logger.error(f"Error extracting characters: {e}")
            raise

    def generate_personality_summary(self, character_name: str, text: str) -> Dict:
        """
        Generate detailed personality/behavior summary for a specific character
        
        Args:
            character_name: Name of the character to analyze
            text: Full story text (or relevant portion)
            
        Returns:
            Dictionary with personality summary
        """
        # Use first 10000 characters for personality analysis
        sample_text = text[:10000]
        
        prompt = f"""You are a literary psychologist. Analyze the character "{character_name}" from the following story excerpt.

Story excerpt:
{sample_text}

Provide a detailed personality and behavior analysis for {character_name}. Include:
1. Key personality traits (e.g., brave, curious, kind, stubborn)
2. Behavioral patterns and how they interact with others
3. Motivations and goals
4. Character arc or development (if visible in this excerpt)
5. Notable quotes or actions that define them

Return your response as a JSON object with this format:
{{
  "personality_traits": ["trait1", "trait2", "trait3"],
  "behavior_summary": "2-3 sentence summary of how they behave and interact",
  "motivations": "What drives this character",
  "character_arc": "How they change or develop in the story",
  "defining_moments": ["quote or action 1", "quote or action 2"]
}}

Return ONLY the JSON object, no additional text."""

        try:
            # Use Gemini (currently active)
            if settings.AI_PROVIDER == "gemini":
                if not self.gemini_model:
                    raise Exception("Gemini model not initialized. Check your GEMINI_API_KEY in .env file.")
                response = self.gemini_model.generate_content(prompt)
                content = response.text.strip()
            
            # OpenAI implementation - commented for future use
            # elif settings.AI_PROVIDER == "openai":
            #     response = self.openai_client.chat.completions.create(
            #         model=settings.OPENAI_MODEL,
            #         messages=[
            #             {"role": "system", "content": "You are a literary psychologist expert at analyzing character personalities."},
            #             {"role": "user", "content": prompt}
            #         ],
            #         temperature=0.4,
            #         max_tokens=800
            #     )
            #     content = response.choices[0].message.content.strip()
            
            else:
                raise Exception(f"Unsupported AI provider: {settings.AI_PROVIDER}")
            
            # Remove markdown code blocks if present
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()
            
            personality_data = json.loads(content)
            logger.info(f"Generated personality summary for {character_name}")
            return personality_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse personality summary as JSON: {e}")
            logger.error(f"Response content: {content}")
            # Return basic structure if parsing fails
            return {
                "personality_traits": ["Unknown"],
                "behavior_summary": "Unable to generate personality summary",
                "motivations": "Unknown",
                "character_arc": "Unknown",
                "defining_moments": []
            }
        
        except Exception as e:
            logger.error(f"Error generating personality summary: {e}")
            raise
    
    def get_character_count(self, text: str) -> int:
        """Quick count of potential characters in text"""
        try:
            characters = self.extract_characters(text)
            return len(characters)
        except:
            return 0