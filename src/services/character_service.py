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
            "lord", "lady", "sir", "madam", "miss", "mr", "mrs", "ms",
            "weakest", "strongest"  # Descriptive adjectives, not names
        }
        
        # Patterns that indicate descriptive phrases (not names)
        # These catch phrases like "World's Weakest Hero", "The Strongest Hunter"
        self.descriptive_patterns = [
            r'.*\s+(weakest|strongest|best|worst|greatest|lowest)\s+.*',  # "world's weakest hero"
            r'.*the\s+(weakest|strongest|best|worst|greatest|lowest).*',   # "the strongest hunter"
            r'.*of\s+the\s+.*',                           # "king of the hill"
            r'.*who\s+.*',                                 # "one who"
            r'.*that\s+.*',                               # "person that"
        ]
    
    def _is_non_character(self, name: str) -> bool:
        """Check if name is in blacklist of non-character terms or is a descriptive phrase"""
        normalized = self._normalize_name(name)
        
        # Check exact match
        if normalized in self.non_character_terms:
            return True
        
        # Check if it's a descriptive phrase containing blacklisted adjectives
        # (e.g., "world weakest hero" contains "weakest")
        name_words = set(normalized.split())
        if name_words.intersection(self.non_character_terms):
            # If it's a multi-word phrase (3+ words) with descriptive adjectives, it's likely a description
            # Single or two-word names are more likely to be actual names
            if len(name_words) >= 3:  # Multi-word phrases with descriptive terms are likely descriptions
                return True
        
        # Check if it matches descriptive phrase patterns
        for pattern in self.descriptive_patterns:
            if re.match(pattern, normalized, re.IGNORECASE):
                return True
        
        # Check if it's purely a title/rank
        title_pattern = r'^(the\s+)?(lieutenant|captain|commander|colonel|general|officer|handler)\s*(one|two|three)?$'
        if re.match(title_pattern, normalized):
            return True
        
        # Check if it's a group reference
        group_pattern = r'^(the\s+)?(soldiers|troops|children|enemies|friends|group|squad|unit)$'
        if re.match(group_pattern, normalized):
            return True
        
        # Check if it's a descriptive phrase (contains "the" + adjective + noun pattern)
        descriptive_pattern = r'^(the\s+)?(world|world\'s|kingdom|realm|land)\'?s?\s+(weakest|strongest|best|worst|greatest|lowest)\s+.*'
        if re.match(descriptive_pattern, normalized, re.IGNORECASE):
            return True
        
        return False
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison (lowercase, strip whitespace, remove punctuation)"""
        # Remove punctuation except hyphens and apostrophes
        normalized = re.sub(r'[^\w\s\-\']', '', name.lower())
        return ' '.join(normalized.split())  # Normalize whitespace
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings (0.0 to 1.0)"""
        return SequenceMatcher(None, str1, str2).ratio()
    
    def _is_name_subset(self, short: str, long: str) -> bool:
        """Check if short name is a subset of long name (e.g., 'Shin' in 'Shinei Nouzen')"""
        short_parts = set(short.lower().split())
        long_parts = set(long.lower().split())
        
        # Check if any part of short name appears in long name
        for short_part in short_parts:
            for long_part in long_parts:
                # Direct substring match
                if short_part in long_part or long_part in short_part:
                    return True
                # High similarity match
                if self._calculate_similarity(short_part, long_part) > 0.85:
                    return True
        return False
    
    def _is_title_pattern(self, name: str) -> bool:
        """Check if name is a title pattern (e.g., 'Handler One', 'The Undertaker')"""
        normalized = name.lower()
        
        # Common title patterns
        title_patterns = [
            r'^(the\s+)?handler\s+(one|two|three|four|five|1|2|3|4|5)',
            r'^(the\s+)?(captain|commander|lieutenant|colonel|general|officer)',
            r'^(the\s+)?(undertaker|reaper|handler|observer|striker)',
            r'^(sir|madam|lord|lady|master|mistress)\s+\w+',
        ]
        
        for pattern in title_patterns:
            if re.match(pattern, normalized):
                return True
        return False
    
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
        
        # Check name subset (e.g., "Shin" matches "Shinei Nouzen")
        if self._is_name_subset(norm1, norm2) or self._is_name_subset(norm2, norm1):
            return True
        
        # Fuzzy matching for similar names (typos, translations)
        similarity = self._calculate_similarity(norm1, norm2)
        if similarity >= threshold:
            return True
        
        # Check word-by-word matching for multi-word names
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        # If they share at least one significant word (>3 chars)
        common_words = words1.intersection(words2)
        if common_words:
            # At least one common word longer than 3 chars
            if any(len(word) > 3 for word in common_words):
                return True
        
        return False
    
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
        
        # Skip if either name is empty
        if not name1 or not name2:
            return False
        
        # Direct fuzzy matching (handles nicknames, subsets, similarities)
        if self._fuzzy_match(name1, name2):
            return True
        
        # Check if descriptions are very similar (same person described differently)
        desc1 = char1.get('description', '').lower()
        desc2 = char2.get('description', '').lower()
        
        if desc1 and desc2:
            # If descriptions are highly similar, likely same character
            desc_similarity = self._calculate_similarity(desc1, desc2)
            if desc_similarity > 0.7:
                return True
            
            # Check if one name appears in the other's description
            norm1 = self._normalize_name(name1)
            norm2 = self._normalize_name(name2)
            
            if norm1 in desc2 or norm2 in desc1:
                return True
        
        # Check for common name parts (shared first or last name)
        parts1 = self._extract_name_parts(name1)
        parts2 = self._extract_name_parts(name2)
        
        # If they share significant name parts (>3 chars)
        common_parts = parts1.intersection(parts2)
        if common_parts:
            significant_common = [p for p in common_parts if len(p) > 3]
            if significant_common:
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
            
            # Smart canonical name selection
            # Priority: Full names > First names > Callsigns > Nicknames
            
            # 1. Find full names (contains space, multiple words)
            full_names = [name for name in aliases if ' ' in name and len(name.split()) >= 2]
            
            # 2. Find single-word names (first names)
            single_names = [name for name in aliases if ' ' not in name and len(name) > 2]
            
            # 3. Find callsigns/titles
            titles = [name for name in aliases if self._is_title_pattern(name)]
            
            # Select canonical name
            if full_names:
                # Prefer longest full name (most complete)
                main_char['name'] = max(full_names, key=len)
            elif single_names:
                # Prefer longest single name
                main_char['name'] = max(single_names, key=len)
            elif titles:
                main_char['name'] = titles[0]
            else:
                # Fallback to first alias
                main_char['name'] = list(aliases)[0]
            
            # Add all aliases (sorted)
            main_char['aliases'] = sorted(list(aliases))
            
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
        # Use first 15000 characters for better context
        sample_text = text[:15000]
        
        prompt = f"""You are an expert at extracting character names from novels.

Extract ALL name variations for each character from the text below. A character may appear as:
- Full name: "Sung Jinwoo", "Vladilena Milizé"
- First name only: "Jinwoo", "Lena"
- Last name only: "Sung"
- Nicknames: "Lena", "Shin"
- Callsigns/Titles: "Handler One", "The Undertaker"

TEXT:
{sample_text}

EXTRACTION RULES:

1. WHAT TO EXTRACT (YES):
   ✓ Actual character names (proper nouns): "Sung Jinwoo", "Joohee Lee", "Shinei Nouzen"
   ✓ Nicknames used as names: "Shin", "Lena", "Jinwoo"
   ✓ Callsigns/titles when used AS A NAME: "Undertaker", "Handler One"
   ✓ Name variations: "Sung Jinwoo" AND "Jinwoo" AND "Sung" (list separately)

2. WHAT TO IGNORE (NO):
   ✗ Descriptive phrases: "World's Weakest Hunter", "The Strongest"
   ✗ Insults/mockery: "idiot", "fool", "weakling"
   ✗ Generic titles: "the captain", "the queen" (without name)
   ✗ Group references: "the soldiers", "hunters", "guild members"
   ✗ Generic terms: "boy", "girl", "stranger", "person"

3. IMPORTANT: List each name variation SEPARATELY
   - If a character is called "Sung Jinwoo", "Jinwoo", and "Sung" → create 3 entries
   - If a character has callsign "Undertaker" and name "Shin" → create 2 entries
   - The merging system will combine them later

4. For each name, provide:
   - "name": The exact name/nickname/callsign as it appears
   - "description": WHO this person is (1 sentence, based on text)
   - "role": "protagonist" / "supporting" / "antagonist" (based on text)

OUTPUT FORMAT (JSON only):
[
  {{
    "name": "Sung Jinwoo",
    "description": "An E-rank hunter who receives mysterious daily quests",
    "role": "protagonist"
  }},
  {{
    "name": "Jinwoo",
    "description": "An E-rank hunter who receives mysterious daily quests",
    "role": "protagonist"
  }},
  {{
    "name": "Joohee Lee",
    "description": "A healing spellcaster who worries about Jinwoo",
    "role": "supporting"
  }},
  {{
    "name": "Joohee",
    "description": "A healing spellcaster who worries about Jinwoo",
    "role": "supporting"
  }}
]

Return ONLY the JSON array."""

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