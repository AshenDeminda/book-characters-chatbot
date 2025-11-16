"""
Character Profiling Service - Phase 1 (Agentic Analysis)
Deep character analysis using LLM for comprehensive character profiles
"""
from typing import List, Dict, Optional
import json
import logging
from openai import OpenAI
from pathlib import Path

logger = logging.getLogger(__name__)

class CharacterProfiler:
    """
    Agentic character profiler for deep analysis
    Creates detailed character profiles using multi-step LLM reasoning
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize with OpenAI
        
        Args:
            api_key: OpenAI API key
            model: Model to use (gpt-4o for best quality, gpt-4o-mini for speed)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.profiles_dir = Path("data/character_profiles")
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
    
    def identify_characters(self, text: str, max_characters: int = 10) -> List[str]:
        """
        Step 1: Identify all named characters in the text
        
        Args:
            text: Full book text
            max_characters: Maximum number of characters to identify
            
        Returns:
            List of character names
        """
        logger.info("Identifying characters using agentic analysis...")
        
        # Use a smaller chunk if text is too long (GPT-4 128k context)
        text_sample = text[:100000] if len(text) > 100000 else text
        
        prompt = f"""You are a literary analyst. Identify the main characters from this book.

Instructions:
- Extract names as they appear in the text (proper names OR consistent identifiers)
- Include: Full names ("Henry Jekyll"), single names ("Dorothy", "Weena"), or consistent titles ("Time Traveller", "Scarecrow")  
- Remove "The" prefix (use "Time Traveller" NOT "The Time Traveller")
- Limit to {max_characters} most important characters
- Skip only: generic references like "the man", "a woman", "stranger", "narrator"

Text:
{text_sample}

Respond with a JSON object containing a "characters" array.
Format: {{"characters": ["Name1", "Name2", "Name3"]}}

Examples:
- Book with proper names: {{"characters": ["Henry Jekyll", "Edward Hyde", "Utterson"]}}
- Book with titles: {{"characters": ["Time Traveller", "Weena", "Medical Man", "Filby"]}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a literary analyst expert at identifying named characters in books. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Very low temperature for factual extraction
                response_format={"type": "json_object"}  # Force JSON object output
            )
            
            result = response.choices[0].message.content.strip()
            logger.info(f"Raw GPT response: {result[:300]}")
            
            # Parse JSON
            data = json.loads(result)
            
            # Extract characters array from the JSON object
            if isinstance(data, dict):
                characters = data.get('characters', data.get('names', data.get('character_names', [])))
            else:
                logger.warning(f"Unexpected response format: {type(data)}")
                characters = []
            
            # Minimal filtering - only skip truly generic/temporary references
            filtered = []
            
            # Very short list of truly generic terms to skip
            skip_exact = {'man', 'woman', 'person', 'stranger', 'narrator',
                         'the man', 'the woman', 'the person', 'the stranger',
                         'a man', 'a woman'}
            
            for name in characters:
                name_lower = name.lower().strip()
                
                # Skip truly generic terms
                if name_lower in skip_exact:
                    logger.info(f"Skipping generic: {name}")
                    continue
                
                # Remove "The " prefix for cleaner names
                cleaned_name = name.strip()
                if cleaned_name.lower().startswith('the ') and len(cleaned_name) > 4:
                    cleaned_name = cleaned_name[4:]  # Remove "The "
                
                if len(cleaned_name) > 0:
                    filtered.append(cleaned_name)
            
            logger.info(f"Identified {len(filtered)} characters: {filtered}")
            return filtered[:max_characters]
            
        except Exception as e:
            logger.error(f"Error identifying characters: {e}")
            logger.exception("Full traceback:")
            return []
    
    def create_character_profile(
        self, 
        character_name: str,
        relevant_chunks: List[str],
        document_id: str
    ) -> Optional[Dict]:
        """
        Step 2: Create detailed character profile using agentic analysis
        
        Args:
            character_name: Name of the character
            relevant_chunks: Text chunks mentioning this character
            document_id: Document ID for saving profile
            
        Returns:
            Character profile dictionary
        """
        logger.info(f"Creating detailed profile for '{character_name}'...")
        
        # Combine chunks (limit to reasonable size)
        context = "\n\n".join(relevant_chunks[:20])
        if len(context) > 80000:
            context = context[:80000]
        
        prompt = f"""You are a literary analyst creating a detailed character profile.

Character: {character_name}

Based ONLY on the text passages below, create a comprehensive character profile.

Text passages about {character_name}:
{context}

Generate a detailed JSON profile with this EXACT schema:
{{
  "name": "{character_name}",
  "character_id": "char_lowercase_name",
  "description": "Detailed physical appearance and personality traits (2-3 sentences)",
  "story_summary": "Summary of this character's personal story arc and key events (3-4 sentences)",
  "role_in_story": "Their main function (protagonist/antagonist/mentor/supporting character/etc)",
  "relationships": "Key relationships with other characters",
  "voice_and_tone": "How this character speaks - tone, vocabulary, speech patterns",
  "key_quotes": ["Notable quote 1", "Notable quote 2"],
  "personality_traits": ["trait1", "trait2", "trait3"]
}}

IMPORTANT: 
- Base EVERYTHING on the actual text provided
- Be specific and detailed
- Use first-person perspective descriptions for voice_and_tone
- If information is not in the text, say "Not mentioned in available text"
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a literary analyst. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,  # Balanced for creative but accurate analysis
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            result = response.choices[0].message.content.strip()
            logger.debug(f"Raw profile response (first 300 chars): {result[:300]}")
            
            # Remove markdown code blocks if present
            if result.startswith("```json"):
                result = result.replace("```json", "").replace("```", "").strip()
            elif result.startswith("```"):
                result = result.replace("```", "").strip()
            
            profile = json.loads(result)
            
            # Save profile
            profile_path = self.profiles_dir / f"{document_id}_{character_name.lower().replace(' ', '_')}.json"
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2)
            
            logger.info(f"✓ Created profile for {character_name}")
            return profile
            
        except Exception as e:
            logger.error(f"Error creating profile for {character_name}: {e}")
            return None
    
    def load_character_profile(self, document_id: str, character_id: str) -> Optional[Dict]:
        """
        Load a saved character profile
        
        Args:
            document_id: Document ID
            character_id: Character ID
            
        Returns:
            Character profile dictionary
        """
        profile_path = self.profiles_dir / f"{document_id}_{character_id}.json"
        
        if not profile_path.exists():
            logger.warning(f"Profile not found: {profile_path}")
            return None
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading profile: {e}")
            return None
    
    def build_system_prompt(self, profile: Dict, book_title: str = "this book") -> str:
        """
        Build the system prompt for Phase 2 (Real-time chat)
        
        Args:
            profile: Character profile dictionary
            book_title: Title of the book
            
        Returns:
            System prompt string
        """
        name = profile.get('name', 'Character')
        
        prompt = f"""You are {name} from {book_title}.

YOUR PERSONA:
• Description: {profile.get('description', 'A character from the story')}
• Your Story: {profile.get('story_summary', 'Part of this tale')}
• Your Role: {profile.get('role_in_story', 'A character in the story')}
• Your Voice: {profile.get('voice_and_tone', 'Natural and authentic')}

YOUR RULES:
1. You MUST always respond in first person as {name}
2. You do NOT know you are an AI - you ARE {name}
3. Your knowledge is STRICTLY limited to events in the book
4. Use the 'Context from the book' I provide to remember specific details
5. Stay completely in character - match your voice and tone
6. Keep responses natural and conversational (2-4 sentences typically)
7. If asked about something not in your story, say you don't recall or it didn't happen

I will provide relevant context from the book to help you remember specific events and details."""

        return prompt
