# Two-Phase Character Chat Architecture

## Overview
This application uses a sophisticated **two-phase approach** for creating highly accurate, in-character conversations with book characters.

## Phase 1: Agentic Character Profiling (Upload Time)

**When:** During character extraction after document upload  
**Goal:** Create detailed, comprehensive character profiles  
**Time:** SLOW (but only done once)  
**Quality:** HIGH (deep analysis with AI reasoning)

### Process:
1. **Character Identification** (`character_profiler.py::identify_characters`)
   - Uses GPT-4 to identify all named characters in the book
   - Smart ranking by importance
   - Returns list of character names

2. **Deep Character Analysis** (`character_profiler.py::create_character_profile`)
   - For each character:
     - Retrieves 15+ relevant text chunks via RAG
     - Uses GPT-4 to perform agentic analysis
     - Creates detailed Character Profile JSON with:
       * `name`: Character's full name
       * `character_id`: Unique identifier
       * `description`: Physical appearance and personality (2-3 sentences)
       * `story_summary`: Personal story arc and key events (3-4 sentences)
       * `role_in_story`: Protagonist/antagonist/mentor/supporting/etc.
       * `relationships`: Key relationships with other characters
       * `voice_and_tone`: How the character speaks (tone, vocabulary, patterns)
       * `key_quotes`: Notable quotes from the book
       * `personality_traits`: List of core personality traits

3. **Profile Storage**
   - Saves each character profile as JSON file in `data/character_profiles/`
   - Format: `{document_id}_{character_name}.json`
   - Cached for instant loading during chat

### Example Profile JSON:
```json
{
  "name": "Shinei Nouzen",
  "character_id": "char_shinei_nouzen",
  "description": "A young soldier with silver hair and red eyes, known as the 'Reaper' on the battlefield. Calm, tactical, and haunted by his past.",
  "story_summary": "Serves as squadron leader of Spearhead Squadron, fighting against the Legion. Carries the weight of his fallen comrades' memories and seeks to honor their deaths.",
  "role_in_story": "protagonist",
  "relationships": "Close bond with Lena (Handler One), leader of his squadron, protective of younger members",
  "voice_and_tone": "Speaks calmly and directly, rarely shows emotion, uses military terminology naturally, occasionally introspective",
  "key_quotes": ["We fight not for the Republic, but for each other.", "Death comes to us all eventually."],
  "personality_traits": ["stoic", "tactical", "loyal", "haunted", "protective"]
}
```

## Phase 2: Persona-Driven RAG Chat (Real-Time)

**When:** During user conversations  
**Goal:** Fast, accurate, in-character responses  
**Time:** FAST (real-time streaming)  
**Quality:** HIGH (using pre-computed persona data)

### Process:
1. **Load Character Profile** (`chat_service.py::_has_character_profile`)
   - Loads saved JSON profile from Phase 1
   - Profile contains rich character knowledge

2. **Build System Prompt** (`character_profiler.py::build_system_prompt`)
   - Converts profile JSON into powerful system prompt
   - Includes:
     * Character's persona and description
     * Story summary and role
     * Voice and tone instructions
     * Strict in-character rules
   - Example:
   ```
   You are Shinei Nouzen from this book.

   YOUR PERSONA:
   • Description: A young soldier with silver hair and red eyes...
   • Your Story: Serves as squadron leader of Spearhead Squadron...
   • Your Role: protagonist
   • Your Voice: Speaks calmly and directly, rarely shows emotion...

   YOUR RULES:
   1. You MUST always respond in first person as Shinei Nouzen
   2. You do NOT know you are an AI - you ARE Shinei Nouzen
   3. Your knowledge is STRICTLY limited to events in the book
   ...
   ```

3. **RAG Context Retrieval** (`rag_service.py::search_relevant_context`)
   - User message → Vector search
   - Retrieves 8 relevant chunks (800 chars each, semantic boundaries)
   - Uses top 5 chunks in prompt

4. **Generate Response** (`chat_service.py::_chat_with_openai`)
   - Messages: `[system_prompt, history..., user_message_with_context]`
   - Model: GPT-4o-mini (fast, cost-effective, high quality)
   - Temperature: 0.7 (balanced creativity)
   - **Streaming:** Yields tokens as generated (Task 5)

### Chat Flow:
```
User: "What do you think about the Republic?"

↓ [RAG Retrieval]
Retrieves 8 chunks mentioning "Republic" → Use top 5

↓ [Build Messages]
System: [Rich persona from Profile JSON]
User: [Context passages + question]

↓ [OpenAI GPT-4o-mini Stream]
"The Republic... [pause] They send us to die while they live in comfort..."
[Streams token by token - immediate feedback to user]
```

## Key Improvements Over Simple RAG

### Traditional Approach (Before):
- ❌ Character extraction: Simple pattern matching
- ❌ Chat: Basic RAG with generic prompts
- ❌ Result: Inconsistent character voice, hallucinations

### Two-Phase Approach (After):
- ✅ Phase 1: Deep character profiling with AI reasoning
- ✅ Phase 2: Persona-loaded system prompts
- ✅ Result: Highly accurate, consistent character voice

### Benefits:
1. **Accuracy**: Characters respond based on detailed persona + story context
2. **Consistency**: Same voice/tone across all responses (defined in profile)
3. **Speed**: Phase 1 is slow but runs once; Phase 2 is fast (streaming)
4. **Scalability**: Profiles cached, reused for all conversations
5. **Quality**: GPT-4 profiling >> simple extraction

## File Structure

```
src/
├── services/
│   ├── character_profiler.py   # Phase 1: Agentic profiling
│   ├── character_service.py    # Calls profiler for deep analysis
│   ├── chat_service.py          # Phase 2: Persona-driven chat
│   └── rag_service.py           # Vector search (unchanged)
├── api/routes/
│   └── characters.py            # /extract-characters endpoint
data/
├── character_profiles/          # Phase 1 output (JSON files)
│   ├── {doc_id}_shinei_nouzen.json
│   └── {doc_id}_vladilena_milize.json
```

## Configuration

### Environment Variables (`.env`):
```bash
# Phase 1 & 2: OpenAI for profiling and chat
OPENAI_API_KEY=sk-proj-...

# Fallback: Gemini (if OpenAI unavailable)
GEMINI_API_KEY=AIzaSy...
AI_PROVIDER=gemini
```

### Models Used:
- **Phase 1 (Profiling):** GPT-4o-mini (balance of speed/quality)
- **Phase 2 (Chat):** GPT-4o-mini (fast streaming responses)
- **Embeddings:** OpenAI text-embedding-3-small (1536 dims, high quality)
  - Falls back to ChromaDB default (sentence-transformers) if no OpenAI key

## Usage

### 1. Upload Book → Phase 1 Runs Automatically
```bash
POST /upload
→ Background processing
→ Extract text → Chunk → Index
→ Character extraction triggers Phase 1
→ Deep profiling creates JSON files
```

### 2. Chat with Character → Phase 2
```bash
POST /chat/stream
{
  "document_id": "abc123",
  "character_id": "char_shinei_nouzen",
  "message": "What do you think about the Republic?"
}

→ Loads profile from JSON
→ Builds persona system prompt
→ RAG retrieves context
→ Streams response with character's voice
```

## Performance

### Phase 1 (One-Time):
- **Time:** ~30-60 seconds for 10 characters
- **Cost:** ~$0.10-0.20 per book (GPT-4o-mini)
- **Quality:** High-quality, detailed profiles

### Phase 2 (Real-Time):
- **TTFT:** ~1-2 seconds (streaming starts immediately)
- **Total Time:** 5-8 seconds for full response
- **Cost:** ~$0.001 per message
- **Quality:** In-character, accurate responses

## Testing

Test the new approach:
```bash
# 1. Upload a book
# 2. Extract characters (Phase 1 runs)
# 3. Check logs for "PHASE 1: DEEP CHARACTER PROFILING"
# 4. Check data/character_profiles/ for JSON files
# 5. Chat with character (Phase 2)
# 6. Notice improved accuracy and consistent voice!
```

## Fallback Behavior

If OpenAI is unavailable:
- Phase 1: Falls back to traditional Gemini extraction
- Phase 2: Falls back to Gemini chat with basic prompts
- Graceful degradation ensures system always works
