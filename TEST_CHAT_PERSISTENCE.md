# Chat Session Persistence Test Script

This script demonstrates the new chat session persistence feature.

## Test the new endpoints:

### 1. Chat with Harry Potter (first time)
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"document_id\": \"default_hp1_doc_001\",
    \"character_id\": \"char_harry_potter\",
    \"message\": \"Tell me about your scar\",
    \"conversation_history\": []
  }"
```

### 2. Check saved history
```bash
curl "http://localhost:8000/api/v1/chat/session/history?document_id=default_hp1_doc_001&character_id=char_harry_potter"
```

### 3. Send another message (will be added to history)
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"document_id\": \"default_hp1_doc_001\",
    \"character_id\": \"char_harry_potter\",
    \"message\": \"What about Voldemort?\",
    \"conversation_history\": []
  }"
```

### 4. Check updated history (should have 4 messages now)
```bash
curl "http://localhost:8000/api/v1/chat/session/history?document_id=default_hp1_doc_001&character_id=char_harry_potter"
```

### 5. Switch to Hermione
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d "{
    \"document_id\": \"default_hp1_doc_001\",
    \"character_id\": \"char_hermione_granger\",
    \"message\": \"Tell me about your studies\",
    \"conversation_history\": []
  }"
```

### 6. Check Hermione's history (separate from Harry)
```bash
curl "http://localhost:8000/api/v1/chat/session/history?document_id=default_hp1_doc_001&character_id=char_hermione_granger"
```

### 7. List all sessions for the book
```bash
curl "http://localhost:8000/api/v1/chat/session/list?document_id=default_hp1_doc_001"
```

### 8. Clear Harry's chat history
```bash
curl -X DELETE "http://localhost:8000/api/v1/chat/session/clear?document_id=default_hp1_doc_001&character_id=char_harry_potter"
```

### 9. Verify Harry's history is cleared
```bash
curl "http://localhost:8000/api/v1/chat/session/history?document_id=default_hp1_doc_001&character_id=char_harry_potter"
```

## Expected Behavior:

✅ Each character has separate conversation history
✅ History persists even when switching between characters
✅ Backend automatically saves after each message
✅ Can clear individual character histories
✅ Can see all active chats for a book

## Database Location:

Chat sessions are stored in: `data/app.db`

Table: `chat_sessions`

Columns:
- id (primary key)
- session_id (unique: document_id + character_id)
- document_id
- character_id
- character_name
- conversation_history (JSON)
- created_at
- updated_at
