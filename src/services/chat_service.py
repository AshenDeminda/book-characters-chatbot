"""
Character Chat Service
Handles conversations with book characters using RAG and personality profiles
"""
from typing import List, Dict, Optional
import google.generativeai as genai
import json
import logging

from src.config import settings
from src.rag.rag_service import RAGService

logger = logging.getLogger(__name__)

# ===============================================
# CHAT ACCURACY IMPROVEMENTS
#
# Focus: RAG-based character accuracy for ANY book
# - Strict in-character responses using personality + story context
# - Greetings match character's actual personality (not generic)
# - Reduced hallucinations via structured prompts
# - Better use of RAG excerpts
# ===============================================

class ChatService:
    """Manages character-based conversations with RAG context"""
    
    def __init__(self):
        # Initialize Gemini model
        self.gemini_model = None
        if settings.AI_PROVIDER == "gemini":
            if not settings.GEMINI_API_KEY:
                logger.error("GEMINI_API_KEY not found")
            else:
                try:
                    genai.configure(api_key=settings.GEMINI_API_KEY)
                    self.gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
                    logger.info("Chat service initialized with Gemini")
                except Exception as e:
                    logger.error(f"Failed to initialize Gemini: {e}")
        
        # Initialize RAG service
        self.rag_service = RAGService()
    
    def _build_character_prompt(
        self,
        character: Dict,
        user_message: str,
        relevant_context: List[Dict],
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Build the prompt for character conversation with strict accuracy controls
        
        Args:
            character: Character information (name, personality, aliases)
            user_message: User's message
            relevant_context: Relevant story chunks from RAG
            conversation_history: Previous conversation turns
            
        Returns:
            Formatted prompt string
        """
        # Extract character info
        name = character.get('name', 'Unknown')
        description = character.get('description', '')
        role = character.get('role', 'character')
        personality = character.get('personality', {})
        
        # Build personality section with structure
        personality_section = ""
        if personality:
            traits = personality.get('personality_traits', [])
            behavior = personality.get('behavior_summary', '')
            motivations = personality.get('motivations', '')
            
            if traits:
                personality_section += f"\nPersonality: {', '.join(traits)}"
            if behavior:
                personality_section += f"\nBehavior patterns: {behavior}"
            if motivations:
                personality_section += f"\nMotivations: {motivations}"
        
        # Build context from RAG with clear boundaries
        context_section = ""
        if relevant_context:
            context_section = "\n\n=== STORY CONTEXT (Your source of truth) ===\n"
            for i, ctx in enumerate(relevant_context[:3], 1):
                # Truncate very long contexts
                context_text = ctx['text'][:500] if len(ctx['text']) > 500 else ctx['text']
                context_section += f"\n[Context {i}]:\n{context_text}\n"
            context_section += "\n=== END STORY CONTEXT ===\n"
        
        # Build conversation history
        history_section = ""
        if conversation_history and len(conversation_history) > 0:
            history_section = "\n\nRecent conversation:\n"
            for turn in conversation_history[-4:]:  # Last 4 turns
                role_text = turn.get('role', 'user')
                content = turn.get('content', '')
                history_section += f"- {role_text.capitalize()}: {content}\n"
        
        # Build final prompt with strict instructions
        prompt = f"""You are roleplaying as {name} from a story.

CHARACTER PROFILE:
Name: {name}
Role: {role}
Description: {description}{personality_section}
{context_section}
CRITICAL RULES:
1. You ARE {name}. Respond using "I", "me", "my" (first person only)
2. ONLY use information from the STORY CONTEXT above
3. Match {name}'s personality, tone, and speaking style from the description
4. If the user asks about something NOT in the story context, say you don't recall that specific detail
5. DO NOT add information not present in the context
6. Stay completely in character - never break the fourth wall
7. Keep responses concise and natural (2-4 sentences typically)
{history_section}
User asks: {user_message}

Respond as {name}:"""
        
        return prompt
    
    def chat_with_character(
        self,
        character: Dict,
        document_id: str,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Generate a character's response to user message
        
        Args:
            character: Character information
            document_id: Document ID for context retrieval
            user_message: User's message
            conversation_history: Previous conversation turns
            
        Returns:
            Dictionary with character response and metadata
        """
        try:
            # Retrieve relevant context from story using RAG
            relevant_context = self.rag_service.search_relevant_context(
                query=user_message,
                document_id=document_id,
                n_results=5
            )
            
            # Build prompt
            prompt = self._build_character_prompt(
                character=character,
                user_message=user_message,
                relevant_context=relevant_context,
                conversation_history=conversation_history
            )
            
            # Generate response using Gemini
            if settings.AI_PROVIDER == "gemini":
                if not self.gemini_model:
                    raise Exception("Gemini model not initialized")
                
                response = self.gemini_model.generate_content(prompt)
                character_response = response.text.strip()
            else:
                raise Exception(f"Unsupported AI provider: {settings.AI_PROVIDER}")
            
            # Return response with metadata
            return {
                "status": "success",
                "character_name": character.get('name'),
                "response": character_response,
                "context_chunks_used": len(relevant_context),
                "relevant_context": [
                    {
                        "text": ctx['text'][:200] + "...",  # Preview only
                        "relevance_score": 1 - ctx['distance'] if ctx.get('distance') else None
                    }
                    for ctx in relevant_context[:3]
                ]
            }
            
        except Exception as e:
            logger.error(f"Error generating character response: {e}")
            raise
    
    def get_character_greeting(self, character: Dict) -> str:
        """
        Generate a character's initial greeting that matches their personality
        
        Args:
            character: Character information
            
        Returns:
            Greeting message
        """
        name = character.get('name', 'Character')
        description = character.get('description', '')
        role = character.get('role', 'character')
        personality = character.get('personality', {})
        
        # Extract personality details
        traits = personality.get('personality_traits', []) if personality else []
        behavior = personality.get('behavior_summary', '') if personality else ''
        
        try:
            # Build context-aware greeting prompt
            personality_hint = ""
            if traits:
                personality_hint = f"\nYour personality: {', '.join(traits[:3])}"
            if behavior:
                personality_hint += f"\nHow you act: {behavior[:200]}"
            
            prompt = f"""You are {name}, a {role} from a story.

About you:
{description}{personality_hint}

Generate a BRIEF greeting (1-2 sentences max) as {name} meeting someone for the first time.

RULES:
- Stay TRUE to {name}'s personality and situation in the story
- Use first person ("I", "me", "my")
- Match {name}'s tone (formal/casual, friendly/reserved, etc.)
- DO NOT be overly cheerful if the character isn't cheerful
- DO NOT use modern slang unless the character would
- Keep it natural and authentic to who {name} is

{name} says:"""
            
            if settings.AI_PROVIDER == "gemini":
                if not self.gemini_model:
                    return f"I'm {name}."
                
                response = self.gemini_model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,  # Some creativity but controlled
                        max_output_tokens=100  # Keep greetings short
                    )
                )
                greeting = response.text.strip()
                
                # Clean up any quotes or extra formatting
                greeting = greeting.strip('"\'')
                return greeting
            else:
                return f"I'm {name}."
                
        except Exception as e:
            logger.error(f"Error generating greeting: {e}")
            # Fallback: Simple, character-appropriate greeting
            return f"I'm {name}."
