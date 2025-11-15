# 🧪 Testing Character Chat with FastAPI UI

The FastAPI server is already running at: **http://localhost:8000/docs**

## 📋 Step-by-Step Testing Guide

### Step 1: Upload a PDF (if not already done)

1. Go to **POST /api/v1/upload/upload-pdf**
2. Click "Try it out"
3. Click "Choose File" and select your storybook PDF
4. Click "Execute"
5. Copy the `document_id` from the response (e.g., `fa0d116d-38ca-4de5-9f2b-611ddcde9d2f`)

**Expected Response:**
```json
{
  "status": "success",
  "message": "Storybook processed and indexed for RAG",
  "document_id": "fa0d116d-38ca-4de5-9f2b-611ddcde9d2f",
  "page_count": 50,
  "chunk_count": 120
}
```

---

### Step 2: Extract Characters

1. Go to **GET /api/v1/characters/extract-characters/{document_id}**
2. Click "Try it out"
3. Paste your `document_id` in the field
4. Click "Execute"
5. Copy a `character_id` from the response (e.g., `char_shinei_nouzen`)

**Expected Response:**
```json
{
  "status": "success",
  "document_id": "fa0d116d-38ca-4de5-9f2b-611ddcde9d2f",
  "characters": [
    {
      "character_id": "char_shinei_nouzen",
      "name": "Shinei Nouzen",
      "aliases": ["Undertaker", "Shin"],
      "personality": "A stoic and battle-hardened soldier..."
    }
  ]
}
```

---

### Step 3: Get Character Greeting

1. Go to **POST /api/v1/chat/greeting**
2. Click "Try it out"
3. Fill in the request body:
```json
{
  "document_id": "fa0d116d-38ca-4de5-9f2b-611ddcde9d2f",
  "character_id": "char_shinei_nouzen"
}
```
4. Click "Execute"
5. See the character's greeting in their personality

**Expected Response:**
```json
{
  "status": "success",
  "character_name": "Shinei Nouzen",
  "greeting": "...Captain. What do you need?"
}
```

---

### Step 4: Chat with Character (RAG-Powered)

1. Go to **POST /api/v1/chat**
2. Click "Try it out"
3. Fill in the request body:

**First Message (No History):**
```json
{
  "document_id": "fa0d116d-38ca-4de5-9f2b-611ddcde9d2f",
  "character_id": "char_shinei_nouzen",
  "message": "Tell me about your squadron",
  "conversation_history": []
}
```

**Follow-up Message (With History):**
```json
{
  "document_id": "fa0d116d-38ca-4de5-9f2b-611ddcde9d2f",
  "character_id": "char_shinei_nouzen",
  "message": "What happened during the last battle?",
  "conversation_history": [
    {
      "role": "user",
      "content": "Tell me about your squadron"
    },
    {
      "role": "assistant",
      "content": "The Spearhead Squadron... we're the Eighty-Six..."
    }
  ]
}
```

4. Click "Execute"
5. See the character's response with RAG context

**Expected Response:**
```json
{
  "status": "success",
  "character_name": "Shinei Nouzen",
  "response": "The Spearhead Squadron is composed of veterans who've survived countless battles...",
  "context_chunks_used": 5,
  "relevant_context": [
    {
      "text": "Story chunk from the book about the squadron...",
      "relevance_score": 0.85
    }
  ]
}
```

---

## 🔍 What to Verify

### ✅ RAG is Working:
- Response includes `context_chunks_used` (should be > 0)
- Character mentions specific story details from the book
- `relevant_context` array shows story chunks with high relevance scores (0.7+)

### ✅ Character Personality:
- Character stays in character (tone, speech patterns)
- Responses align with personality description
- Character references their own experiences from the story

### ✅ Conversation History:
- Character remembers previous messages
- Follow-up questions get coherent responses
- Context builds across the conversation

---

## 💡 Test Scenarios

### Scenario 1: Story Details
**User:** "What happened in chapter 3?"
**Verify:** Character uses RAG to retrieve specific chapter content

### Scenario 2: Character Relationships
**User:** "Tell me about [other character name]"
**Verify:** Character discusses relationships from story context

### Scenario 3: Personality Consistency
**User:** Ask 5 different questions
**Verify:** Character maintains consistent tone/personality

### Scenario 4: Conversation Memory
**User:** "What did we just discuss?"
**Verify:** Character references previous conversation turns

---

## 🐛 Troubleshooting

### Error: "Character not found"
- Re-run **Step 2** to extract characters
- Verify `character_id` is correct (copy from extract response)

### Error: "Document not found in vector store"
- Re-upload the PDF (RAG indexing happens automatically)
- Check `chroma_db/` directory exists

### Low relevance scores (< 0.5)
- Try more specific questions about story events
- Check if the document was properly chunked

### Character responses are generic
- Verify personality was extracted (check Step 2 response)
- Ensure RAG context is being retrieved (check `context_chunks_used`)

---

## 📊 Expected Behavior

| Feature | Working Correctly |
|---------|-------------------|
| **RAG Context** | 3-5 relevant chunks retrieved per query |
| **Relevance Scores** | 0.6 - 0.9 for good matches |
| **Response Time** | 2-5 seconds per chat message |
| **Character Voice** | Consistent with personality description |
| **Memory** | References previous 5-10 conversation turns |

---

## 🎯 Success Criteria

Your implementation is working if:
1. ✅ Character greets you in their personality
2. ✅ Character answers with specific story details (RAG working)
3. ✅ Character stays in character across multiple messages
4. ✅ Character remembers conversation context
5. ✅ `context_chunks_used` is 3-5 per message
6. ✅ `relevance_score` is above 0.6 for most chunks

---

## 📝 Quick Copy-Paste Values

**Your existing document:**
```
document_id: fa0d116d-38ca-4de5-9f2b-611ddcde9d2f
```

**Test Questions:**
- "Tell me about your background"
- "What happened in the story?"
- "Describe your relationship with [other character]"
- "What are your thoughts on [story event]?"
- "How did you feel during [specific scene]?"
