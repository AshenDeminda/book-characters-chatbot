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
        Build the prompt for character conversation
        
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
        aliases = character.get('aliases', [])
        description = character.get('description', '')
        personality = character.get('personality', {})
        
        # Build personality section
        personality_text = ""
        if personality:
            traits = personality.get('personality_traits', [])
            behavior = personality.get('behavior_summary', '')
            motivations = personality.get('motivations', '')
            
            if traits:
                personality_text += f"Personality traits: {', '.join(traits)}\n"
            if behavior:
                personality_text += f"Behavior: {behavior}\n"
            if motivations:
                personality_text += f"Motivations: {motivations}\n"
        
        # Build context from RAG
        context_text = ""
        if relevant_context:
            context_text = "\n\nRelevant story excerpts:\n"
            for i, ctx in enumerate(relevant_context[:3], 1):  # Use top 3 chunks
                context_text += f"\n[Excerpt {i}]:\n{ctx['text']}\n"
        
        # Build conversation history
        history_text = ""
        if conversation_history:
            history_text = "\n\nRecent conversation:\n"
            for turn in conversation_history[-5:]:  # Last 5 turns
                role = turn.get('role', 'user')
                content = turn.get('content', '')
                history_text += f"{role.capitalize()}: {content}\n"
        
        # Build final prompt
        prompt = f"""You are {name}, a character from a story. You must respond AS THIS CHARACTER, staying completely in character.

Character Information:
{description}

{personality_text}

Known aliases: {', '.join(aliases) if aliases else name}
{context_text}
{history_text}

IMPORTANT INSTRUCTIONS:
1. Respond as {name} would, using their personality, speech patterns, and knowledge
2. Stay consistent with the story context provided above
3. Do not break character or mention you are an AI
4. Use first person ("I", "my", "me")
5. Reference events from the story naturally if relevant
6. Match the character's tone and manner of speaking

User's message: {user_message}

{name}'s response:"""
        
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
        Generate a character's initial greeting
        
        Args:
            character: Character information
            
        Returns:
            Greeting message
        """
        name = character.get('name', 'Character')
        description = character.get('description', '')
        
        try:
            prompt = f"""You are {name}, a character from a story.

Character info: {description}

Generate a brief, friendly greeting (1-2 sentences) to welcome someone who wants to talk to you. Stay in character.

{name}'s greeting:"""
            
            if settings.AI_PROVIDER == "gemini":
                if not self.gemini_model:
                    return f"Hello, I'm {name}. What would you like to know?"
                
                response = self.gemini_model.generate_content(prompt)
                return response.text.strip()
            else:
                return f"Hello, I'm {name}. What would you like to know?"
                
        except Exception as e:
            logger.error(f"Error generating greeting: {e}")
            return f"Hello, I'm {name}. What would you like to know?"
