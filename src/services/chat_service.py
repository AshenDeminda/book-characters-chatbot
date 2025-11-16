"""
Character Chat Service
Handles conversations with book characters using RAG and personality profiles

PHASE 2: Persona-Driven RAG Chat
- Load detailed character profiles created in Phase 1
- Build rich system prompts from character JSON
- Use OpenAI for better quality responses
- Maintain fast response times with pre-computed personas
"""
from typing import List, Dict, Optional, Generator
import google.generativeai as genai
from openai import OpenAI
import json
import logging

from src.config import settings
from src.rag.rag_service import RAGService
from src.services.character_profiler import CharacterProfiler

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
        # Initialize OpenAI client for Phase 2
        self.openai_client = None
        self.profiler = None
        if settings.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.profiler = CharacterProfiler(
                api_key=settings.OPENAI_API_KEY,
                model="gpt-4o-mini"
            )
            logger.info("Chat service initialized with OpenAI (Phase 2)")
        
        # Initialize Gemini model (fallback)
        self.gemini_model = None
        if settings.AI_PROVIDER == "gemini":
            if not settings.GEMINI_API_KEY:
                logger.error("GEMINI_API_KEY not found")
            else:
                try:
                    genai.configure(api_key=settings.GEMINI_API_KEY)
                    self.gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL)
                    logger.info("Chat service initialized with Gemini (fallback)")
                except Exception as e:
                    logger.error(f"Failed to initialize Gemini: {e}")
        
        # Initialize RAG service
        self.rag_service = RAGService()
    
    def _has_character_profile(self, character: Dict) -> bool:
        """Check if character has a Phase 1 profile"""
        return 'profile' in character and character['profile'] is not None
    
    def _build_persona_system_prompt(self, character: Dict, book_title: str = "this book") -> str:
        """
        PHASE 2: Build persona-driven system prompt from character profile
        
        If character has a Phase 1 profile, uses detailed profile data.
        Otherwise, falls back to basic description.
        """
        if self._has_character_profile(character):
            # Use CharacterProfiler to build rich system prompt
            return self.profiler.build_system_prompt(
                profile=character['profile'],
                book_title=book_title
            )
        else:
            # Fallback: Basic system prompt
            name = character.get('name', 'Character')
            description = character.get('description', 'A character from the story')
            
            return f"""You are {name} from {book_title}.

YOUR PERSONA:
• Description: {description}
• Your Role: {character.get('role', 'A character in the story')}

YOUR RULES:
1. You MUST always respond in first person as {name}
2. You do NOT know you are an AI - you ARE {name}
3. Your knowledge is STRICTLY limited to events in the book
4. Use the 'Context from the book' I provide to remember specific details
5. Stay completely in character
6. Keep responses natural and conversational (2-4 sentences typically)
7. If asked about something not in your story, say you don't recall or it didn't happen

I will provide relevant context from the book to help you remember specific events and details."""
    
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
            # IMPROVED: Use more chunks (up to 5) since they're smaller and more focused
            for i, ctx in enumerate(relevant_context[:5], 1):
                # Don't truncate - use full chunk since it's already appropriately sized
                context_text = ctx['text']
                context_section += f"\n[Context {i}]:\n{context_text}\n"
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
        
        PHASE 2: Uses OpenAI with persona-driven system prompts for better accuracy
        
        Args:
            character: Character information (with optional profile from Phase 1)
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
                n_results=8  # More chunks for better context
            )
            
            # PHASE 2: Use OpenAI if available
            if self.openai_client and self.profiler:
                character_response = self._chat_with_openai(
                    character=character,
                    user_message=user_message,
                    relevant_context=relevant_context,
                    conversation_history=conversation_history
                )
            else:
                # Fallback: Use Gemini with traditional prompt
                character_response = self._chat_with_gemini(
                    character=character,
                    user_message=user_message,
                    relevant_context=relevant_context,
                    conversation_history=conversation_history
                )
            
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
    
    def _chat_with_openai(
        self,
        character: Dict,
        user_message: str,
        relevant_context: List[Dict],
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        PHASE 2: Chat using OpenAI with persona-driven system prompts
        """
        # Build persona system prompt
        system_prompt = self._build_persona_system_prompt(character, "this book")
        
        # Build context section
        context_text = "\n\nContext from the book:\n"
        for i, ctx in enumerate(relevant_context[:5], 1):
            context_text += f"\n[Passage {i}]:\n{ctx['text']}\n"
        
        # Build user prompt
        user_prompt = f"{context_text}\n\nUser asks: {user_message}\n\nRespond as {character.get('name')}:"
        
        # Build messages array
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add conversation history
        if conversation_history:
            for turn in conversation_history[-4:]:
                role = "assistant" if turn.get('role') == 'assistant' else "user"
                messages.append({"role": role, "content": turn.get('content', '')})
        
        # Add current user message
        messages.append({"role": "user", "content": user_prompt})
        
        # Generate with OpenAI
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cost-effective
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
    
    def _chat_with_gemini(
        self,
        character: Dict,
        user_message: str,
        relevant_context: List[Dict],
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Fallback: Chat using Gemini with traditional prompt
        """
        # Build prompt
        prompt = self._build_character_prompt(
            character=character,
            user_message=user_message,
            relevant_context=relevant_context,
            conversation_history=conversation_history
        )
        
        # Generate response using Gemini
        if not self.gemini_model:
            raise Exception("Gemini model not initialized")
        
        response = self.gemini_model.generate_content(prompt)
        return response.text.strip()
    
    def chat_with_character_stream(
        self,
        character: Dict,
        document_id: str,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7
    ) -> Generator[str, None, None]:
        """
        Generate a streaming character response to user message
        
        TASK 5: RESPONSE STREAMING (Enhanced with Phase 2)
        - Streams response tokens as they're generated
        - Uses OpenAI streaming or Gemini streaming
        - Persona-driven prompts for better accuracy
        - Expected improvement: 60-80% perceived latency reduction
        
        Args:
            character: Character information (with optional profile from Phase 1)
            document_id: Document ID for context retrieval
            user_message: User's message
            conversation_history: Previous conversation turns
            max_tokens: Maximum tokens to generate
            temperature: Response randomness (0.0-1.0)
            
        Yields:
            String chunks of the response as they're generated
        """
        try:
            # Retrieve relevant context from story using RAG
            relevant_context = self.rag_service.search_relevant_context(
                query=user_message,
                document_id=document_id,
                n_results=8  # More chunks for better context
            )
            
            # PHASE 2: Use OpenAI streaming if available
            if self.openai_client and self.profiler:
                yield from self._chat_with_openai_stream(
                    character=character,
                    user_message=user_message,
                    relevant_context=relevant_context,
                    conversation_history=conversation_history,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            else:
                # Fallback: Use Gemini streaming
                yield from self._chat_with_gemini_stream(
                    character=character,
                    user_message=user_message,
                    relevant_context=relevant_context,
                    conversation_history=conversation_history,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
        except Exception as e:
            logger.error(f"Error generating streaming response: {e}")
            yield f"[Error: {str(e)}]"
    
    def _chat_with_openai_stream(
        self,
        character: Dict,
        user_message: str,
        relevant_context: List[Dict],
        conversation_history: Optional[List[Dict]],
        max_tokens: int,
        temperature: float
    ) -> Generator[str, None, None]:
        """
        PHASE 2: Stream chat using OpenAI with persona-driven system prompts
        """
        # Build persona system prompt
        system_prompt = self._build_persona_system_prompt(character, "this book")
        
        # Build context section
        context_text = "\n\nContext from the book:\n"
        for i, ctx in enumerate(relevant_context[:5], 1):
            context_text += f"\n[Passage {i}]:\n{ctx['text']}\n"
        
        # Build user prompt
        user_prompt = f"{context_text}\n\nUser asks: {user_message}\n\nRespond as {character.get('name')}:"
        
        # Build messages array
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add conversation history
        if conversation_history:
            for turn in conversation_history[-4:]:
                role = "assistant" if turn.get('role') == 'assistant' else "user"
                messages.append({"role": role, "content": turn.get('content', '')})
        
        # Add current user message
        messages.append({"role": "user", "content": user_prompt})
        
        # Stream with OpenAI
        stream = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True  # Enable streaming
        )
        
        # Yield chunks as they arrive
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def _chat_with_gemini_stream(
        self,
        character: Dict,
        user_message: str,
        relevant_context: List[Dict],
        conversation_history: Optional[List[Dict]],
        max_tokens: int,
        temperature: float
    ) -> Generator[str, None, None]:
        """
        Fallback: Stream chat using Gemini with traditional prompt
        """
        # Build prompt
        prompt = self._build_character_prompt(
            character=character,
            user_message=user_message,
            relevant_context=relevant_context,
            conversation_history=conversation_history
        )
        
        # Generate streaming response using Gemini
        if not self.gemini_model:
            raise Exception("Gemini model not initialized")
        
        # Configure generation parameters
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens
        )
        
        # Stream response from Gemini
        response_stream = self.gemini_model.generate_content(
            prompt,
            generation_config=generation_config,
            stream=True  # Enable streaming
        )
        
        # Yield chunks as they arrive
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
    
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
