from typing import List, Dict
# OpenAI import - commented for future use when key is purchased
# from openai import OpenAI
import google.generativeai as genai
import json
import logging

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
    
    def extract_characters(self, text: str, max_characters: int = 10) -> List[Dict]:
        """
        Use LLM to find character names from story text
        
        Args:
            text: Story text (or first portion of it)
            max_characters: Maximum number of characters to extract
            
        Returns:
            List of character dictionaries
        """
        # Use first 8000 characters to avoid token limits
        sample_text = text[:8000]
        
        prompt = f"""You are a literary analyst. Read the following story excerpt and identify the main character names.

Story excerpt:
{sample_text}

Instructions:
1. List all character names mentioned in the text
2. Focus on characters that appear to be important to the story
3. Return ONLY proper names of people (not places or things)
4. For each character, provide a brief description based on the text

Return your response as a JSON array with this format:
[
  {{
    "name": "Character Full Name",
    "description": "Brief description of the character",
    "role": "protagonist/antagonist/supporting"
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
            
            # Limit to max_characters
            characters = characters[:max_characters]
            
            # Add character IDs
            for i, char in enumerate(characters):
                char['character_id'] = f"char_{i+1:03d}"
            
            logger.info(f"Extracted {len(characters)} characters using {settings.AI_PROVIDER}")
            return characters
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response content: {content}")
            raise Exception("Failed to parse character list from AI response")
        
        except Exception as e:
            logger.error(f"Error extracting characters: {e}")
            raise

    def get_character_count(self, text: str) -> int:
        """Quick count of potential characters in text"""
        try:
            characters = self.extract_characters(text)
            return len(characters)
        except:
            return 0